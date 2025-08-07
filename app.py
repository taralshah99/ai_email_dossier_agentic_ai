import os
import base64
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from crewai import Crew, Process, Task, LLM
from crewai_agents import MeetingAgents
from gmail_utils import get_gmail_service, list_email_threads, get_email_thread, get_thread_subject_and_sender

# --- Load .env variables ---
load_dotenv()

# --- LiteLLM / CrewAI Azure LLM Setup ---
# Must set LiteLLM-compatible env vars:
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "")

azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
llm = LLM(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    model=f"azure/{azure_deployment}"
)

# --- Agents Setup ---
agents = MeetingAgents(llm)

# --- Gmail Service ---
gmail_service = get_gmail_service()

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)

# --- Helper: Ask Azure ---
def ask_azure_openai(prompt: str):
    # CrewAI's LLM is based on LiteLLM, so we use its invoke-style interface
    return llm.complete(messages=[{"role": "user", "content": prompt}]).choices[0]["message"]["content"]

def parse_product_info(text: str):
    product_name_match = re.search(r"Product Name:\s*\**(.+?)\**\s*$", str(text), re.MULTILINE)
    product_domain_match = re.search(r"Product Domain:\s*\**(.+?)\**\s*$", str(text), re.MULTILINE)

    return {
        "product_name": product_name_match.group(1).strip() if product_name_match else "Unknown Product",
        "product_domain": product_domain_match.group(1).strip() if product_domain_match else "general product"
    }

def find_relevant_threads(start_date, end_date, keyword=None, from_email=None, query=None):
    search_parts = [f"after:{start_date} before:{end_date}"]
    if from_email:
        search_parts.append(f"from:{from_email}")
    if keyword:
        search_parts.append(f'"{keyword}"')
    if query:
        search_parts.append(query)

    search_query = " ".join(search_parts)
    all_threads = list_email_threads(gmail_service, query=search_query)
    if not all_threads:
        print("No email threads found for the criteria.")
        return []

    relevant_threads = []
    triage_agent = agents.email_triage_agent(keyword) if keyword else None

    for thread_meta in all_threads:
        thread_id = thread_meta["id"]
        subject, sender = get_thread_subject_and_sender(gmail_service, thread_id)
        messages = get_email_thread(gmail_service, thread_id)
        body = ""
        if messages:
            msg = messages[0]
            if "snippet" in msg:
                body = msg["snippet"]
            elif msg.get("payload", {}).get("parts"):
                for part in msg["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break

        if triage_agent:
            triage_task = Task(
                description=f"Decide if this email is relevant to '{keyword}':\n\nSubject: {subject}\n\nBody: {body}",
                expected_output="YES or NO",
                agent=triage_agent
            )
            crew = Crew(agents=[triage_agent], tasks=[triage_task], process=Process.sequential)
            outcome = str(crew.kickoff()).strip().upper()
            if "NO" in outcome:
                continue

        if subject and sender:
            relevant_threads.append({"id": thread_id, "subject": subject, "sender": sender, "body": body})

    return relevant_threads

def analyze_thread_content(thread_id: str):
    messages = get_email_thread(gmail_service, thread_id)
    email_content = []
    for msg in messages:
        if "snippet" in msg:
            email_content.append(msg["snippet"])
        elif msg.get("payload", {}).get("parts"):
            for part in msg["payload"]["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    email_content.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))

    full_email_thread_text = "\n".join(email_content)

    analysis_agent = agents.meeting_agenda_extractor()

    task = Task(
        description=(
            "Analyze the provided email thread content. Your final answer MUST strictly follow this template:\n\n"
            "**Email Summaries:**\n"
            "- [Summary of Email 1]\n"
            "- [Summary of Email 2]\n\n"
            "**Meeting Agenda:**\n"
            "- [Extracted Meeting Agenda]\n\n"
            "**Meeting Date & Time:**\n"
            "- [Extracted Date and Time]\n\n"
            "**Final Conclusion:**\n"
            "- [Overall summary of the thread's conclusion]\n\n"
            "**Product Name:** [The specific product name identified]\n"
            "**Product Domain:** [The general domain of the product]\n\n"
            f"--- EMAIL THREAD CONTENT ---\n{full_email_thread_text}"
        ),
        expected_output=(
            "A structured summary that strictly follows the provided template, including the 'Product Name' and 'Product Domain' labels."
        ),
        agent=analysis_agent
    )

    crew = Crew(agents=[analysis_agent], tasks=[task], process=Process.sequential)
    analysis_output = crew.kickoff()

    product_info = parse_product_info(analysis_output)

    return {
        "analysis": str(analysis_output),
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"]
    }


def analyze_multiple_threads(thread_ids: list):
    if not thread_ids:
        return None

    all_thread_contents = []
    all_subjects = []

    for thread_id in thread_ids:
        messages = get_email_thread(gmail_service, thread_id)
        subject, sender = get_thread_subject_and_sender(gmail_service, thread_id)

        email_content = []
        for msg in messages:
            if "snippet" in msg:
                email_content.append(msg["snippet"])
            elif msg.get("payload", {}).get("parts"):
                for part in msg["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        email_content.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))

        thread_text = "\n".join(email_content)
        all_thread_contents.append(f"=== THREAD: {subject} ===\n{thread_text}")
        all_subjects.append(subject)

    combined_content = "\n\n".join(all_thread_contents)
    analysis_agent = agents.meeting_agenda_extractor()

    task = Task(
        description=(
            f"Analyze the provided {len(thread_ids)} email threads and create a comprehensive summary. "
            "Your final answer MUST strictly follow this template:\n\n"
            "**Thread Subjects:**\n"
            f"{chr(10).join([f'- {subject}' for subject in all_subjects])}\n\n"
            "**Combined Email Summaries:**\n"
            "- [Summary of key emails across all threads]\n\n"
            "**Consolidated Meeting Agenda:**\n"
            "- [Combined meeting agenda items from all threads]\n\n"
            "**Meeting Dates & Times:**\n"
            "- [All extracted dates and times from all threads]\n\n"
            "**Final Conclusion:**\n"
            "- [Overall summary combining insights from all threads]\n\n"
            "**Product Name:** [The main product name identified across threads]\n"
            "**Product Domain:** [The general domain of the product]\n\n"
            f"--- COMBINED EMAIL THREAD CONTENT ---\n{combined_content}"
        ),
        expected_output="A structured summary that strictly follows the provided template, consolidating information from all email threads.",
        agent=analysis_agent
    )

    crew = Crew(agents=[analysis_agent], tasks=[task], process=Process.sequential)
    analysis_output = crew.kickoff()

    product_info = parse_product_info(analysis_output)

    return {
        "analysis": str(analysis_output),
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"],
        "thread_count": len(thread_ids)
    }


def generate_product_dossier(product_name: str, product_domain: str):
    dossier_agent = agents.product_dossier_creator(product_name, product_domain)
    task = Task(
        description=f"Create a comprehensive product dossier for \'{product_name}\' which is in the \'{product_domain}\' domain.",
        expected_output=f"A detailed and well-structured product dossier for {product_name}.",
        agent=dossier_agent,
    )
    crew = Crew(agents=[dossier_agent], tasks=[task], process=Process.sequential)
    dossier_output = crew.kickoff()

    return {
        "dossier": str(dossier_output)
    }


# --- API Routes ---
@app.route("/api/find_threads", methods=["POST"])
def api_find_threads():
    try:
        print("Received find_threads request")  # Debug
        data = request.get_json()
        print(f"Data: {data}")  # Debug
        threads = find_relevant_threads(
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            keyword=data.get('keyword'),
            from_email=data.get('from_email'),
            query=data.get('query')
        )
        print(f"Found {len(threads)} threads")  # Debug
        return jsonify(threads)
    except Exception as e:
        print(f"Error in find_threads: {e}")  # Debug
        return jsonify({'error': str(e)}), 500

@app.route("/api/analyze_thread", methods=["POST"])
def api_analyze_thread():
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        if not thread_id:
            return jsonify({'error': 'thread_id is required'}), 400
        result = analyze_thread_content(thread_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/analyze_multiple_threads", methods=["POST"])
def api_analyze_multiple_threads():
    try:
        data = request.get_json()
        thread_ids = data.get('thread_ids', [])
        if not thread_ids:
                return jsonify({'error': 'thread_ids array is required'}), 400
        result = analyze_multiple_threads(thread_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/generate_dossier", methods=["POST"])
def api_generate_dossier():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        product_domain = data.get('product_domain')
        if not product_name or not product_domain:
            return jsonify({'error': 'product_name and product_domain are required'}), 400
        dossier = generate_product_dossier(product_name, product_domain)
        return jsonify(dossier)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/azure_ask", methods=["POST"])
def api_azure_ask():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        result = ask_azure_openai(prompt)
        return jsonify({
            'response': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({'status': 'healthy'}) 


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
