import os
import base64
import re
import json
from typing import List, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from crewai import Crew, Process, Task, LLM
from crewai_agents import MeetingAgents
from gmail_utils import get_gmail_service, list_email_threads, get_email_thread, get_thread_subject_and_sender
import requests

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

# --- Gmail Service (lazy init to avoid startup crash if creds missing) ---
gmail_service = None
gmail_service_error = None

def ensure_gmail_service():
    global gmail_service, gmail_service_error
    if gmail_service is None and gmail_service_error is None:
        try:
            gmail_service = get_gmail_service()
        except Exception as e:
            gmail_service_error = str(e)
    if gmail_service is None:
        raise RuntimeError(
            f"Gmail service is not configured: {gmail_service_error or 'Unknown error. Ensure credentials.json exists and OAuth consent is completed.'}"
        )
    return gmail_service

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


def _extract_section(text: str, header_variants: list[str]) -> str:
    """Return raw section content between a header and the next header or end.

    header_variants: list of header strings without surrounding asterisks/colons normalization.
    Matches forms like '**Header:**' optionally with trailing/leading spaces.
    """
    if not text:
        return ""

    # Build a regex to match any of the header variants in bold markdown style
    header_regexes = [
        pattern
        for h in header_variants
        for pattern in [
            rf"\*\*{re.escape(h)}\s*:\*\*",
            rf"\*\*{re.escape(h)}\s*:\s*",
            rf"{re.escape(h)}\s*:\s*",  # fallback without bold
        ]
    ]
    combined_header_pattern = "|".join([f"(?:{p})" for p in header_regexes])

    # Find start of section
    match = re.search(combined_header_pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""

    start_idx = match.end()

    # Find the next bold header '**...:**' after start
    next_header_match = re.search(r"\n\s*\*\*[^\n]+?:\*\*", text[start_idx:], flags=re.IGNORECASE)
    if next_header_match:
        end_idx = start_idx + next_header_match.start()
    else:
        end_idx = len(text)

    section_text = text[start_idx:end_idx].strip()
    return section_text


def _parse_bullets(section_text: str) -> list[str]:
    """Parse lines that look like bullets ('- ...' or numbered) into a list of strings."""
    if not section_text:
        return []
    lines = section_text.splitlines()
    bullets: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # Accept '- foo', '* foo', '1. foo'
        bullet_match = re.match(r"^(?:[-\*]\s+|\d+\.\u00a0?|\d+\.\s+)(.+)$", line)
        if bullet_match:
            item = bullet_match.group(1).strip()
        else:
            # If the whole section isn't bulleted, treat each non-empty line as an item
            item = line

        # Normalize prefixes like 'Email 1: '
        item = re.sub(r"^Email\s*\d+\s*:\s*", "", item, flags=re.IGNORECASE)
        bullets.append(item)
    return bullets


def structure_analysis_output(text: str) -> dict:
    """Convert the model's markdown-like output into a structured schema.

    Returns keys:
    - email_summaries: list[str]
    - meeting_agenda: list[str]
    - meeting_date_time: list[str]
    - final_conclusion: str
    - product_name: str
    - product_domain: str

    Also supports multi-thread variants like 'Thread Subjects', 'Combined Email Summaries', etc.
    """
    text = str(text or "")

    # Sections (single-thread template)
    email_summaries_raw = _extract_section(text, ["Email Summaries"])
    meeting_agenda_raw = _extract_section(text, ["Meeting Agenda", "Consolidated Meeting Agenda"])
    meeting_dt_raw = _extract_section(text, ["Meeting Date & Time", "Meeting Dates & Times"])
    conclusion_raw = _extract_section(text, ["Final Conclusion"])

    # Multi-thread optional sections
    thread_subjects_raw = _extract_section(text, ["Thread Subjects"]) or ""
    combined_summaries_raw = _extract_section(text, ["Combined Email Summaries"]) or email_summaries_raw

    structured = {
        "thread_subjects": _parse_bullets(thread_subjects_raw) if thread_subjects_raw else [],
        "email_summaries": _parse_bullets(combined_summaries_raw),
        "meeting_agenda": _parse_bullets(meeting_agenda_raw),
        "meeting_date_time": _parse_bullets(meeting_dt_raw),
        "final_conclusion": conclusion_raw.strip() if conclusion_raw else "",
    }

    # Attach product info
    product = parse_product_info(text)
    structured.update({
        "product_name": product["product_name"],
        "product_domain": product["product_domain"],
    })

    return structured


# --- Aliases / Embeddings Utilities ---
def expand_keyword_aliases(keyword: str) -> List[str]:
    """Generate likely variations/abbreviations for the keyword via a lightweight prompt.

    Returns a deduplicated list including the original keyword, trimmed.
    """
    base = (keyword or "").strip()
    if not base:
        return []
    prompt = (
        "Given the term '" + base + "', list 5-10 likely variations, abbreviations, and informal names. "
        "Return one per line without numbering or extra text."
    )
    try:
        raw = ask_azure_openai(prompt)
        lines = [l.strip().strip("-•*") for l in str(raw).splitlines()]
        aliases = [a for a in lines if a]
    except Exception:
        aliases = []

    # Add simple orthographic variants heuristically
    variants = set([base])
    for a in aliases + [base]:
        if not a:
            continue
        variants.add(a)
        variants.add(a.replace("-", " "))
        variants.add(a.replace(" ", ""))
        variants.add(a.replace(" ", "-") )
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for v in variants:
        v2 = v.strip()
        if v2 and v2.lower() not in seen:
            seen.add(v2.lower())
            ordered.append(v2)
    return ordered


def _azure_embeddings_available() -> bool:
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_VERSION") and os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"))


def get_azure_embeddings(texts: List[str]) -> List[List[float]]:
    """Call Azure OpenAI embeddings endpoint for a batch of texts. Returns list of vectors.
    Requires env AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT.
    """
    if not texts:
        return []
    if not _azure_embeddings_available():
        raise RuntimeError("Azure embeddings not configured (set AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT)")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    deployment = os.environ.get("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    url = f"{endpoint}/openai/deployments/{deployment}/embeddings?api-version={api_version}"
    headers = {
        "api-key": os.environ.get("AZURE_OPENAI_KEY", ""),
        "Content-Type": "application/json",
    }
    payload = {"input": texts}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    vectors = [d["embedding"] for d in data.get("data", [])]
    if len(vectors) != len(texts):
        # Attempt to align; pad/truncate to match
        while len(vectors) < len(texts):
            vectors.append(vectors[-1] if vectors else [])
        vectors = vectors[: len(texts)]
    return vectors


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def find_relevant_threads(start_date, end_date, keyword=None, from_email=None, query=None):
    """Smart relevancy finder with exact-phrase Gmail queries, embeddings pre-filter, and AI triage.

    - No OR tokenization: we query Gmail separately per alias phrase and union thread IDs
    - Embeddings: semantic pre-filter on subject + snippet/body
    - AI triage: final YES/NO with context awareness of aliases
    """
    service = ensure_gmail_service()

    # 1) Build alias phrases (exact phrases only)
    aliases = expand_keyword_aliases(keyword) if keyword else []
    alias_phrases = aliases if aliases else ([keyword] if keyword else [])

    # 2) Run separate Gmail searches per alias phrase; union thread IDs
    thread_ids = set()
    for phrase in alias_phrases if alias_phrases else [None]:
        search_parts = [f"after:{start_date} before:{end_date}"]
        if from_email:
            search_parts.append(f"from:{from_email}")
        if phrase:
            # exact phrase; quote if contains spaces
            if " " in phrase:
                search_parts.append(f'"{phrase}"')
            else:
                search_parts.append(phrase)
        if query:
            search_parts.append(query)
        search_query = " ".join(search_parts)
        threads_page = list_email_threads(service, query=search_query)
        for t in threads_page:
            if t.get("id"):
                thread_ids.add(t["id"])

    if not thread_ids:
        return []

    # Fetch lightweight info for all unique threads
    candidates = []
    for thread_id in thread_ids:
        subject, sender = get_thread_subject_and_sender(service, thread_id)
        messages = get_email_thread(service, thread_id)
        snippet = ""
        if messages:
            msg = messages[0]
            if "snippet" in msg:
                snippet = msg["snippet"]
            elif msg.get("payload", {}).get("parts"):
                for part in msg["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        snippet = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
        candidates.append({
            "id": thread_id,
            "subject": subject or "",
            "sender": sender or "",
            "text": f"{subject or ''}\n{snippet or ''}".strip()
        })

    # 3) Embeddings semantic pre-filter
    kept = candidates
    try:
        if alias_phrases and _azure_embeddings_available():
            # Compute embeddings for queries and candidates
            query_vectors = get_azure_embeddings(alias_phrases)
            doc_vectors = get_azure_embeddings([c["text"] for c in candidates])

            scored = []
            for c, dv in zip(candidates, doc_vectors):
                max_sim = max((cosine_similarity(dv, qv) for qv in query_vectors), default=0.0)
                c["semantic_score"] = max_sim
                scored.append(c)

            # Threshold/top-k filter
            threshold = float(os.getenv("SEMANTIC_SIM_THRESHOLD", "0.75"))
            top_k = int(os.getenv("SEMANTIC_TOP_K", "60"))
            scored.sort(key=lambda x: x.get("semantic_score", 0.0), reverse=True)
            kept = [s for s in scored if s.get("semantic_score", 0.0) >= threshold][:top_k]
    except Exception as e:
        # If embeddings fail, proceed without semantic filter
        print(f"Embeddings step failed, continuing without semantic filter: {e}")
        kept = candidates

    # 4) AI triage with alias context (only on the kept subset)
    relevant_threads = []
    if keyword:
        triage_agent = agents.email_triage_agent(keyword)
    else:
        triage_agent = None

    for c in kept:
        subject = c["subject"]
        text = c["text"]
        if triage_agent:
            alias_hint = ", ".join(alias_phrases[:8])
            sim_hint = f"Similarity: {c.get('semantic_score', 0.0):.2f}" if "semantic_score" in c else ""
            triage_desc = (
                f"Determine if this email is about '{keyword}' or its variations.\n"
                f"Known aliases: {alias_hint}\n{sim_hint}\n\n"
                f"Subject: {subject}\n\nBody Excerpt: {text[:1500]}"
            )
            triage_task = Task(
                description=triage_desc,
                expected_output="YES or NO",
                agent=triage_agent
            )
            crew = Crew(agents=[triage_agent], tasks=[triage_task], process=Process.sequential)
            outcome = str(crew.kickoff()).strip().upper()
            if outcome.startswith("NO"):
                continue

        relevant_threads.append({
            "id": c["id"],
            "subject": subject or "No Subject",
            "sender": c["sender"] or "Unknown Sender",
            "body": c["text"]
        })

    return relevant_threads

def analyze_thread_content(thread_id: str):
    service = ensure_gmail_service()
    messages = get_email_thread(service, thread_id)
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
        "structured_analysis": structure_analysis_output(analysis_output),
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"]
    }


def analyze_multiple_threads(thread_ids: list):
    if not thread_ids:
        return None

    all_thread_contents = []
    all_subjects = []

    service = ensure_gmail_service()
    for thread_id in thread_ids:
        messages = get_email_thread(service, thread_id)
        subject, sender = get_thread_subject_and_sender(service, thread_id)

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
        "structured_analysis": structure_analysis_output(analysis_output),
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
        # Ensure Gmail is configured before proceeding
        try:
            ensure_gmail_service()
        except Exception as ge:
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
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
        try:
            ensure_gmail_service()
        except Exception as ge:
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
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
        try:
            ensure_gmail_service()
        except Exception as ge:
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
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
