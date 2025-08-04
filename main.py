import os
import base64
import re
from dotenv import load_dotenv #type:ignore
from crewai import Crew, Process, Task #type:ignore
from langchain_groq import ChatGroq #type:ignore

from gmail_utils import get_gmail_service, list_email_threads, get_email_thread, get_thread_subject_and_sender
from crewai_agents import MeetingAgents

# --- Setup ---
load_dotenv()
# --- MODEL CHANGE ---
# Switched to a model known for strong instruction-following.
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="groq/gemma2-9b-it") 
# --------------------
gmail_service = get_gmail_service()
agents = MeetingAgents(llm=llm)

# --- Helper function to parse agent output ---
def parse_product_info(text: str):
    # This regex is more robust to find the labels even with markdown
    product_name_match = re.search(r"Product Name:\s*\**(.+?)\**\s*$", str(text), re.MULTILINE)
    product_domain_match = re.search(r"Product Domain:\s*\**(.+?)\**\s*$", str(text), re.MULTILINE)
    
    return {
        "product_name": product_name_match.group(1).strip() if product_name_match else "Unknown Product",
        "product_domain": product_domain_match.group(1).strip() if product_domain_match else "general product"
    }

# --- Core Functions ---

def find_relevant_threads(start_date, end_date, keyword=None, from_email=None, query=None):
    """Finds and filters email threads based on keyword, sender, or general query search."""
    # Build the base query with date range
    search_query = f"after:{start_date} before:{end_date}"
    
    # Add optional filters
    if from_email:
        search_query += f" from:{from_email}"
    
    # If a keyword is provided, it will search both subject and content by default in Gmail API
    if keyword:
        search_query += f" {keyword}"
    
    # The 'query' parameter is for general Gmail search syntax, which also searches content by default
    if query:
        search_query += f" {query}"

    all_threads = list_email_threads(gmail_service, query=search_query)
    if not all_threads:
        print("No email threads found for the search criteria.")
        return []

    search_criteria = []
    if keyword:
        search_criteria.append(f"keyword \'{keyword}\' (subject and content)")
    if from_email:
        search_criteria.append(f"from \'{from_email}\'")
    if query:
        search_criteria.append(f"general query \'{query}\'")
    
    criteria_text = ", ".join(search_criteria) if search_criteria else "date range only"
    print(f"Found {len(all_threads)} threads matching {criteria_text}...")

    relevant_threads = []
    for thread_meta in all_threads:
        thread_id = thread_meta["id"]
        subject, sender = get_thread_subject_and_sender(gmail_service, thread_id)
        
        if subject and sender:
            relevant_threads.append({"id": thread_id, "subject": subject, "sender": sender})

    return relevant_threads

def analyze_thread_content(thread_id: str):
    """Analyzes the content of a single email thread."""
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
    
    # --- THIS IS THE CRITICAL FIX ---
    # We are making the prompt extremely strict to guarantee the output format.
    task = Task(
        description=(
            "Analyze the provided email thread content. Your final answer MUST strictly follow this template, "
            "filling in the details from the email. Do not add any other conversational text.\n\n"
            "**Email Summaries:**\n"
            "- [Summary of Email 1]\n"
            "- [Summary of Email 2]\n\n"
            "**Meeting Agenda:**\n"
            "- [Extracted Meeting Agenda]\n\n"
            "**Meeting Date & Time:**\n"
            "- [Extracted Date and Time]\n\n"
            "**Final Conclusion:**\n"
            "- [Overall summary of the thread\'s conclusion]\n\n"
            "**Product Name:** [The specific product name identified]\n"
            "**Product Domain:** [The general domain of the product]\n\n"
            f"--- EMAIL THREAD CONTENT ---\n{full_email_thread_text}"
        ),
        expected_output=(
            "A structured summary that strictly follows the provided template, including the \'Product Name\' and \'Product Domain\' labels."
        ),
        agent=analysis_agent
    )
    # ---------------------------------

    crew = Crew(agents=[analysis_agent], tasks=[task], process=Process.sequential)
    analysis_output = crew.kickoff()

    # This will now work because the output is forced to be in the correct format.
    product_info = parse_product_info(analysis_output)
    
    return {
        "analysis": str(analysis_output),
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"]
    }

def analyze_multiple_threads(thread_ids: list):
    """Analyzes multiple email threads and combines their results."""
    if not thread_ids:
        return None
    
    # Collect all thread contents
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
    
    # Combine all thread contents
    combined_content = "\n\n".join(all_thread_contents)
    
    analysis_agent = agents.meeting_agenda_extractor()
    
    task = Task(
        description=(
            f"Analyze the provided {len(thread_ids)} email threads and create a comprehensive summary. "
            "Your final answer MUST strictly follow this template, filling in the details from all the email threads. "
            "Do not add any other conversational text.\n\n"
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
        expected_output=(
            "A structured summary that strictly follows the provided template, consolidating information from all email threads."
        ),
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
    """Generates a product dossier using a dedicated agent."""
    dossier_agent = agents.product_dossier_creator(product_name, product_domain)
    task = Task(
        description=f"Create a comprehensive product dossier for \'{product_name}\' which is in the \'{product_domain}\' domain.",
        expected_output=f"A detailed and well-structured product dossier for {product_name}.",
        agent=dossier_agent,
    )

    crew = Crew(agents=[dossier_agent], tasks=[task], process=Process.sequential)
    dossier_output = crew.kickoff()
    
    return str(dossier_output)

if __name__ == '__main__':
    print("This script is intended to be imported as a module and should not be run directly.")