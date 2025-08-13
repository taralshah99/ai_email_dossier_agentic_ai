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

def ask_perplexity_api(prompt: str):
    """Call Perplexity API for intensive research"""
    import requests
    
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        raise RuntimeError("PERPLEXITY_API_KEY not found in environment variables")
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-reasoning",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.2,
        "top_p": 0.9,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Making request to Perplexity API with payload: {payload}")  # Debug
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        
        print(f"Response status: {response.status_code}")  # Debug
        print(f"Response content: {response.text}")  # Debug
        
        response.raise_for_status()
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return content
        
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")  # Debug
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")  # Debug
        raise RuntimeError(f"Perplexity API request failed: {str(e)}")
    except Exception as e:
        print(f"Other exception: {e}")  # Debug
        raise RuntimeError(f"Error processing Perplexity API response: {str(e)}")


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


def _slugify(name: str) -> str:
    s = str(name or "").strip().lower()
    s = s.replace(" ", "-")
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"


def read_local_product_knowledge(product_name: str) -> str:
    """Read local knowledge for a product from JSON or markdown."""
    import os
    import json

    try:
        base_dir = os.path.join(os.path.dirname(__file__), "local_knowledge", "products")

        # --- 1) Check per-product folder for JSON file ---
        slug = _slugify(product_name)
        prod_dir = os.path.join(base_dir, slug)
        if os.path.isdir(prod_dir):
            for fn in os.listdir(prod_dir):
                if fn.lower().endswith(".json"):
                    try:
                        with open(os.path.join(prod_dir, fn), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        return json.dumps(data, indent=2)[:60000]
                    except Exception:
                        pass

        # --- 2) Vendor-specific product-portfolio.json ---
        vendor_dir = os.path.join(base_dir, product_name.lower().replace(" ", "-"))
        vendor_json = os.path.join(vendor_dir, "product-portfolio.json")
        if os.path.isfile(vendor_json):
            try:
                with open(vendor_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)[:60000]
            except Exception:
                pass

        # --- 3) Fallback to techify-solutions/product-portfolio.json ---
        fallback_json = os.path.join(base_dir, "techify-solutions", "product-portfolio.json")
        if os.path.isfile(fallback_json):
            try:
                with open(fallback_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)[:60000]
            except Exception:
                pass

        # --- 4) Fallback to markdown extraction ---
        fallback_md = os.path.join(base_dir, "techify-solutions", "product-portfolio.md")
        if os.path.isfile(fallback_md):
            try:
                with open(fallback_md, "r", encoding="utf-8") as f:
                    content = f.read()
                return _extract_md_section(content, product_name)
            except Exception:
                pass

        return ""
    except Exception:
        return ""

def _extract_md_section(content: str, product_name: str) -> str:
    """Extract the relevant section from a markdown file based on product_name."""
    import re
    headers = [(m.start(), m.group(1).strip()) for m in re.finditer(r"(?m)^##\s*(.*)$", content)]

    def normalize_for_match(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    target_norm = normalize_for_match(product_name)
    target_words = [normalize_for_match(w) for w in product_name.split() if w]
    loose_pattern = re.sub(r'[^a-z0-9]', r'.*', (product_name or "").strip())
    loose_regex = re.compile(loose_pattern, re.IGNORECASE)

    for idx, (pos, header) in enumerate(headers):
        header_clean = re.sub(r"^\d+\.\s*", "", header)
        header_norm = normalize_for_match(header_clean)
        if not header_norm:
            continue
        if (
            (target_norm and (target_norm in header_norm or header_norm in target_norm))
            or any(w and w in header_norm for w in target_words)
            or header_norm in target_norm
            or loose_regex.search(header_clean)
        ):
            start = pos
            end = len(content)
            if idx + 1 < len(headers):
                end = headers[idx + 1][0]
            return content[start:end].strip()[:60000]

    m = loose_regex.search(content)
    if m:
        prev_header_pos = 0
        for pos, _ in headers:
            if pos < m.start():
                prev_header_pos = pos
            else:
                break
        next_header_pos = len(content)
        for pos, _ in headers:
            if pos > m.start():
                next_header_pos = pos
                break
        return content[prev_header_pos:next_header_pos].strip()[:60000]

    return content[:60000]


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

    # Try strict JSON parse first (preferred for grouped multi-thread output)
    def _try_parse_json(raw: str):
        try:
            return json.loads(raw)
        except Exception:
            pass
        # Look for fenced code block with JSON
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", raw, flags=re.IGNORECASE)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # Fallback: find first '{' to last '}' to attempt parse
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass
        return None

    json_obj = _try_parse_json(text)
    if isinstance(json_obj, dict) and ("groups" in json_obj or "global_summary" in json_obj):
        # Normalize grouped structure
        groups_in = json_obj.get("groups", []) or []
        groups_out = []
        for g in groups_in:
            groups_out.append({
                "title": (g.get("title") or "Untitled Group").strip(),
                "thread_subjects": g.get("thread_subjects") or g.get("threads") or [],
                "email_summaries": g.get("email_summaries") or g.get("summaries") or [],
                "meeting_agenda": g.get("meeting_agenda") or g.get("agenda") or [],
                "meeting_date_time": g.get("meeting_dates_times") or g.get("meeting_date_time") or [],
                "final_conclusion": g.get("final_conclusion") or g.get("conclusion") or "",
                "products": g.get("products") or [],
            })

        global_summary_in = json_obj.get("global_summary") or {}
        global_summary_out = {
            "final_conclusion": global_summary_in.get("final_conclusion") or global_summary_in.get("conclusion") or "",
            "products": global_summary_in.get("products") or [],
        }

        # Derive top-level product_name/domain if available (first product seen)
        top_product_name = "Unknown Product"
        top_product_domain = "general product"
        all_products = []
        for g in groups_out:
            for p in g.get("products", []) or []:
                all_products.append(p)
        for p in global_summary_out.get("products", []) or []:
            all_products.append(p)
        if all_products:
            first = all_products[0]
            top_product_name = first.get("name") or top_product_name
            top_product_domain = first.get("domain") or top_product_domain

        return {
            "groups": groups_out,
            "global_summary": global_summary_out,
            "product_name": top_product_name,
            "product_domain": top_product_domain,
        }

    # Legacy markdown-style parsing (single or combined without groups)
    email_summaries_raw = _extract_section(text, ["Email Summaries"]) or _extract_section(text, ["Combined Email Summaries"]) 
    meeting_agenda_raw = _extract_section(text, ["Meeting Agenda", "Consolidated Meeting Agenda"]) 
    meeting_dt_raw = _extract_section(text, ["Meeting Date & Time", "Meeting Dates & Times"]) 
    conclusion_raw = _extract_section(text, ["Final Conclusion"]) 
    thread_subjects_raw = _extract_section(text, ["Thread Subjects"]) or ""

    structured = {
        "thread_subjects": _parse_bullets(thread_subjects_raw) if thread_subjects_raw else [],
        "email_summaries": _parse_bullets(email_summaries_raw),
        "meeting_agenda": _parse_bullets(meeting_agenda_raw),
        "meeting_date_time": _parse_bullets(meeting_dt_raw),
        "final_conclusion": conclusion_raw.strip() if conclusion_raw else "",
    }

    product = parse_product_info(text)
    structured.update({
        "product_name": product["product_name"],
        "product_domain": product["product_domain"],
    })
    return structured


# --- Aliases / Embeddings Utilities ---
def _extract_text_from_message(msg: dict) -> str:
    """Extract human-readable text from a Gmail message dict.

    Combines snippet, text/plain parts, and text/html (tags stripped).
    This is used for deterministic substring checks (non-AI).
    """
    collected: list[str] = []

    # Snippet first
    snippet = msg.get("snippet")
    if snippet:
        collected.append(str(snippet))

    def _decode_part_data(part: dict) -> str:
        data = part.get("body", {}).get("data")
        if not data:
            return ""
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _walk_parts(payload: dict):
        if not payload:
            return
        mime = payload.get("mimeType", "")
        if mime.startswith("text/plain"):
            txt = _decode_part_data(payload)
            if txt:
                collected.append(txt)
        elif mime.startswith("text/html"):
            html = _decode_part_data(payload)
            if html:
                # Strip tags and condense spaces
                text_only = re.sub(r"<[^>]+>", " ", html)
                text_only = re.sub(r"\s+", " ", text_only).strip()
                if text_only:
                    collected.append(text_only)

        # Recurse into children
        for child in payload.get("parts", []) or []:
            _walk_parts(child)

    payload = msg.get("payload", {})
    _walk_parts(payload)

    return "\n".join([c for c in collected if c]).strip()
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

def find_relevant_threads(start_date, end_date, keyword=None, from_email=None, query=None, deep_scan: bool = False):
    """Gmail-native search only using the q parameter, broadened for better parity with Gmail UI.

    Changes vs previous:
    - Treat end_date as inclusive by using before:(end_date + 1 day)
    - Expand keyword search to include body and headers via an OR group:
      ( keyword OR "keyword phrase" OR subject:keyword OR from:keyword OR to:keyword OR cc:keyword )
      including simple normalized variants (punctuation/space variants)
    - Skip all AI steps
    """
    service = ensure_gmail_service()

    # Build Gmail native search query (q)
    search_parts = []
    if start_date:
        search_parts.append(f"after:{start_date}")
    if end_date:
        # Make end date inclusive by adding one day for the before: operator
        try:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, "%Y/%m/%d") + timedelta(days=1)
            end_inclusive = end_dt.strftime("%Y/%m/%d")
        except Exception:
            end_inclusive = end_date  # Fallback to provided date
        search_parts.append(f"before:{end_inclusive}")
    if from_email:
        search_parts.append(f"from:{from_email}")

    # Build keyword segment. For strict parity with Gmail UI, prefer raw keyword only.
    if keyword:
        if os.getenv("STRICT_GMAIL_MATCH", "true").lower() == "true":
            # Use keyword exactly as the user would type into Gmail's search bar
            kw = str(keyword).strip()
            if kw:
                if " " in kw:
                    search_parts.append(f'"{kw}"')
                else:
                    search_parts.append(kw)
        else:
            # Enhanced mode: Build an OR group for keyword across body and common headers
            kw = str(keyword).strip()
            variants = [kw]
            # Simple normalizations to catch punctuation variants in addresses/text
            compact = kw.replace("-", " ").replace("_", " ").replace("+", " ").replace(".", " ")
            collapsed = compact.replace(" ", "")
            if compact and compact.lower() not in [v.lower() for v in variants]:
                variants.append(compact)
            if collapsed and collapsed.lower() not in [v.lower() for v in variants]:
                variants.append(collapsed)

            or_terms = []
            for v in variants:
                v = v.strip()
                if not v:
                    continue
                # Unquoted general term searches body + subject by Gmail semantics
                or_terms.append(v)
                # Quoted phrase if contains spaces
                if " " in v:
                    or_terms.append(f'"{v}"')
                # Explicit header targets
                or_terms.append(f"subject:{v}")
                or_terms.append(f"from:{v}")
                or_terms.append(f"to:{v}")
                or_terms.append(f"cc:{v}")
                # Domain/handle heuristics often matched by Gmail UI
                # e.g., searching 'halal' should catch '@halal', '@halal.com', 'halal.com', 'halaltechnologies.com'
                if not v.startswith("@"):
                    or_terms.append(f"@{v}")
                or_terms.append(f"{v}.com")
                or_terms.append(f"@{v}.com")
                # Common suffix pattern for tech companies
                or_terms.append(f"{v}technologies")
                or_terms.append(f"{v}technologies.com")
                or_terms.append(f"@{v}technologies.com")
                # Mailing list header
                or_terms.append(f"list:{v}.com")

            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for t in or_terms:
                key = t.lower()
                if key not in seen:
                    seen.add(key)
                    deduped.append(t)
            if deduped:
                search_parts.append("(" + " OR ".join(deduped) + ")")

    if query:
        search_parts.append(query)

    search_query = " ".join(search_parts).strip()

    # Detect scope for includeSpamTrash parity with Gmail
    q_lower = search_query.lower()
    include_spam_trash = any(token in q_lower for token in ["in:anywhere", "in:spam", "in:trash"])

    # Fetch threads directly from Gmail using the native query
    threads_page = list_email_threads(service, query=search_query, include_spam_trash=include_spam_trash)
    if not threads_page:
        return []

    # Enrich with subject/sender/snippet for UI, without any AI-based filtering
    relevant_threads = []
    for t in threads_page:
        thread_id = t.get("id")
        if not thread_id:
            continue
        subject, sender = get_thread_subject_and_sender(service, thread_id)
        messages = get_email_thread(service, thread_id)
        snippet = ""
        if messages:
            msg = messages[0]
            if "snippet" in msg:
                snippet = msg["snippet"]
            elif msg.get("payload", {}).get("parts"):
                for part in msg["payload"].get("parts", []):
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        snippet = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
        relevant_threads.append({
            "id": thread_id,
            "subject": subject or "No Subject",
            "sender": sender or "Unknown Sender",
            "body": f"{subject or ''}\n{snippet or ''}".strip()
        })

    # Optional deterministic substring augmentation: capture threads whose body contains the keyword
    # even if Gmail's q did not match them (e.g., company name only inside an email address in the body).
    if keyword:
        found_ids = {t["id"] for t in relevant_threads}
        # Build a broad query limited to the same date window (and from_email if provided)
        broad_parts = []
        if start_date:
            broad_parts.append(f"after:{start_date}")
        if end_date:
            try:
                from datetime import datetime, timedelta
                end_dt = datetime.strptime(end_date, "%Y/%m/%d") + timedelta(days=1)
                end_inclusive = end_dt.strftime("%Y/%m/%d")
            except Exception:
                end_inclusive = end_date
            broad_parts.append(f"before:{end_inclusive}")
        if from_email:
            broad_parts.append(f"from:{from_email}")
        # Keep user's advanced query constraints, but omit the keyword to avoid excluding matches
        if query:
            broad_parts.append(query)
        # Optionally include anywhere for more parity
        if os.getenv("BODY_SUBSTRING_IN_ANYWHERE", "true").lower() == "true":
            broad_parts.append("in:anywhere")
        broad_q = " ".join(broad_parts).strip()

        # Only run augmentation if explicitly enabled (opt-in) or when initial hits are very low
        # Gate augmentation by request flag or environment configuration (default off for speed)
        enable_augment_env = os.getenv("ENABLE_BODY_SUBSTRING_AUGMENT", "false").lower()
        enable_augment = deep_scan or (enable_augment_env == "true") or (enable_augment_env == "auto" and len(relevant_threads) < int(os.getenv("BODY_SUBSTRING_MIN_RESULTS", "5")))
        if not enable_augment:
            return relevant_threads

        # Fetch a limited number of candidate threads and post-filter locally by substring
        # Limit how many candidates we even list to avoid long runtimes
        max_candidates = int(os.getenv("BODY_SUBSTRING_AUGMENT_CANDIDATES", "350"))
        candidates: list[dict] = []
        page_token = None
        while True:
            batch_size = min(100, max_candidates - len(candidates))
            if batch_size <= 0:
                break
            results = service.users().threads().list(userId="me", q=broad_q, includeSpamTrash=False, pageToken=page_token, maxResults=batch_size).execute()
            candidates.extend(results.get("threads", []))
            page_token = results.get("nextPageToken")
            if not page_token or len(candidates) >= max_candidates:
                break
        kw_lower = str(keyword).lower()
        # Safety bound on additional processing
        max_extra = int(os.getenv("BODY_SUBSTRING_AUGMENT_MAX", "700"))
        checked = 0
        for t in candidates:
            if checked >= max_extra:
                break
            thread_id = t.get("id")
            if not thread_id or thread_id in found_ids:
                continue
            checked += 1
            msgs = get_email_thread(service, thread_id)
            if not msgs:
                continue
            # Aggregate text from a few messages
            aggregate_text = []
            for m in msgs:  # limit per thread for speed
                aggregate_text.append(_extract_text_from_message(m))
                # Also consider metadata headers for participants
                headers = m.get("payload", {}).get("headers", [])
                for h in headers:
                    if h.get("name", "").lower() in {"from", "to", "cc", "bcc"}:
                        aggregate_text.append(str(h.get("value", "")))
            combined = "\n".join([x for x in aggregate_text if x]).lower()
            if kw_lower and kw_lower in combined:
                subject2, sender2 = get_thread_subject_and_sender(service, thread_id)
                # Use snippet if available
                body_preview = ""
                if msgs and "snippet" in msgs[0]:
                    body_preview = msgs[0]["snippet"]
                relevant_threads.append({
                    "id": thread_id,
                    "subject": subject2 or "No Subject",
                    "sender": sender2 or "Unknown Sender",
                    "body": f"{subject2 or ''}\n{body_preview or ''}".strip()
                })
                found_ids.add(thread_id)

    return relevant_threads


def analyze_thread_content(thread_id: str):
    service = ensure_gmail_service()
    messages = get_email_thread(service, thread_id)

    # NEW: Fetch subject & sender
    subject, sender = get_thread_subject_and_sender(service, thread_id)

    email_content = []
    for msg in messages:
        if "snippet" in msg:
            email_content.append(msg["snippet"])
        elif msg.get("payload", {}).get("parts"):
            for part in msg["payload"]["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    email_content.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))

    # NEW: Prepend subject to the email thread text
    full_email_thread_text = f"Subject: {subject or 'No Subject'}\n" + "\n".join(email_content)

    analysis_agent = agents.meeting_agenda_extractor()

    task = Task(
        description=(
            "You are given a single email thread. Read every email carefully and produce a comprehensive, well-structured analysis.\n\n"
            "Rules:\n"
            "- Always return the sections below in the exact order and with the exact headings.\n"
            "- If the thread has only one email, do NOT write 'The first email says'. Write a direct summary instead.\n"
            "- Be specific. Use concrete details (who, what, when, where, why) from the thread.\n"
            "- If dates or times are ambiguous, infer the most likely time window and note uncertainty.\n"
            "- Expand the Final Conclusion into 3-6 detailed sentences covering outcomes, next steps, blockers, decisions, and owners.\n"
            "- Extract product information whenever present. If absent, return 'Unknown' and a plausible domain.\n"
            "- Use bullet points for lists. Keep tone concise and professional.\n\n"
            "Return exactly this template and fill it thoroughly:\n\n"
            "**Email Summaries:**\n"
            "- [One bullet per email in chronological order. Include sender, intent, key facts, and explicit asks/decisions.]\n\n"
            "**Meeting Agenda:**\n"
            "- [Bullet list of agenda items, discussion topics, action items, blockers, owners]\n\n"
            "**Meeting Date & Time:**\n"
            "- [All explicit or implied dates/times with timezone if present; otherwise note 'unspecified']\n\n"
            "**Final Conclusion:**\n"
            "- [3-6 sentences summarizing the outcome, context, decisions, stakeholders, next steps, and deadlines. Avoid 'first email says' phrasing.]\n\n"
            "**Product Name:** [If present; else 'Unknown']\n"
            "**Product Domain:** [If present; else best-guess domain, e.g., 'SaaS', 'HR tech', 'payments']\n\n"
            f"--- EMAIL THREAD CONTENT (verbatim) ---\n{full_email_thread_text}"
        ),
        expected_output=(
            "A detailed and strictly structured report that follows the template, with a multi-sentence Final Conclusion and no 'first email says' phrasing when only one email exists."
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

    # New grouped multi-thread prompt with strict JSON output
    thread_subjects_block = "\n".join([f"- {s}" for s in all_subjects])
    json_schema = (
        "{"
        "\n  \"groups\": ["
        "\n    {"
        "\n      \"title\": \"string\","
        "\n      \"thread_subjects\": [\"string\"],"
        "\n      \"email_summaries\": [\"string\"],"
        "\n      \"meeting_agenda\": [\"string\"],"
        "\n      \"meeting_date_time\": [\"string\"],"
        "\n      \"final_conclusion\": \"string\","
        "\n      \"products\": [ { \"name\": \"string\", \"domain\": \"string\" } ]"
        "\n    }"
        "\n  ],"
        "\n  \"global_summary\": {"
        "\n    \"final_conclusion\": \"string\","
        "\n    \"products\": [ { \"name\": \"string\", \"domain\": \"string\" } ]"
        "\n  }"
        "\n}"
    )

    task = Task(
        description=(
            f"You are given {len(thread_ids)} email threads. Analyze all emails together. "
            "Your job is to intelligently group emails by topics such as product/service discussed, meeting agendas, feature requests, demos/sales, bug reports, and general queries. "
            "If two threads reference the same product or meeting, group them together."
            "\n\nThread Subjects:\n"
            f"{thread_subjects_block}\n\n"
            "Output STRICTLY as minified JSON following this schema (no markdown, no prose, just JSON):\n"
            f"{json_schema}\n\n"
            "Rules:\n"
            "- Provide clear human-readable group titles.\n"
            "- For each group, include thread_subjects that contributed.\n"
            "- Extract meeting_agenda and meeting_date_time where present.\n"
            "- Include a group-specific final_conclusion.\n"
            "- In global_summary, add a high-level final_conclusion and consolidated products/domains.\n\n"
            f"EMAIL CONTENT START\n{combined_content}\nEMAIL CONTENT END"
        ),
        expected_output="Valid JSON matching the schema with grouped results and a global summary.",
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
    """
    Generate ONLY the product dossier using local product knowledge from .md files.
    Returns: { "product_dossier": str }
    """
    # Get internal product context from .md files
    product_context = read_local_product_knowledge(product_name) if product_name else ""

    dossier_agent = agents.product_dossier_creator(product_name or "Unknown Product", product_domain or "general product")

    # Build task description that forces the agent to use the PRODUCT KNOWLEDGE block only
    task_desc = (
        f"Create a comprehensive product dossier for '{product_name}' ({product_domain}).\n\n"
        "Return MARKDOWN only, with the exact headings (in this order):\n"
        "# Product Dossier: {name}\n"
        "## Executive Summary\n"
        "## Overview\n"
        "## Core Features\n"
        "## Key Benefits\n"
        "## Target Users & Use Cases\n"
        "## Integrations & Compatibility\n"
        "## Security & Compliance\n"
        "## Pricing & Packaging\n"
        "## Competitive Positioning & Differentiators\n"
        "## Sales / Implementation Talking Points\n\n"
        "PRODUCT KNOWLEDGE START\n"
        f"{product_context or 'Not available in internal docs.'}\n"
        "PRODUCT KNOWLEDGE END\n\n"
        "Use only the PRODUCT KNOWLEDGE section above to write the dossier. If a section is missing in the internal docs, write 'Not available in internal docs.' for that section. "
        "Do NOT invent facts or include placeholders like 'Client Details will be populated'."
    ).replace("{name}", product_name or "Unnamed Product")

    task = Task(
        description=task_desc,
        expected_output="Markdown product dossier with the headings specified above.",
        agent=dossier_agent,
    )

    crew = Crew(agents=[dossier_agent], tasks=[task], process=Process.sequential)
    dossier_output = crew.kickoff()

    return {
        "product_dossier": str(dossier_output)
    }


def generate_meeting_flow_dossier(analysis_payload: dict):
    """
    Generate ONLY the meeting flow section from analysis data.
    Returns: { "meeting_flow": str, "product_name": str, "product_domain": str }
    """
    try:
        structured = analysis_payload.get("structured_analysis") if isinstance(analysis_payload, dict) else None
        raw = analysis_payload.get("raw_analysis") or analysis_payload.get("analysis") if isinstance(analysis_payload, dict) else None
    except Exception:
        structured, raw = None, None

    # Build source bundle
    source_sections: list[str] = []
    if structured:
        try:
            source_sections.append("STRUCTURED ANALYSIS:\n" + json.dumps(structured, indent=2))
        except Exception:
            source_sections.append("STRUCTURED ANALYSIS (unserializable) provided")
    if raw:
        source_sections.append("RAW ANALYSIS:\n" + str(raw))

    # Extract product name/domain if present
    product_name = None
    product_domain = None
    try:
        if isinstance(analysis_payload, dict):
            product_name = analysis_payload.get("product_name")
            product_domain = analysis_payload.get("product_domain")
        if not product_name and isinstance(structured, dict):
            product_name = structured.get("product_name")
            product_domain = structured.get("product_domain")
    except Exception:
        product_name = product_name or None
        product_domain = product_domain or None

    # Prepare source text for LLM (no product details included here)
    source_text = "\n\n".join([s for s in source_sections if s]).strip() or "No analysis content provided."

    # Create a meeting flow task
    meeting_flow_agent = agents.meeting_flow_writer()
    meeting_task_desc = (
        "You are generating the 'Meeting Flow' section of an Email Dossier.\n\n"
        "Return MARKDOWN only with the exact headings and order below. Use the analysis as primary source:\n\n"
        "# Meeting Flow\n"
        "## Objectives\n"
        "- [Concise objectives of the meeting]\n\n"
        "## Context\n"
        "- [One-paragraph contextual summary; include product reference if present]\n\n"
        "## Key Discussion Points\n"
        "- [bulleted list of main topics]\n\n"
        "## Decisions\n"
        "- [explicit decisions made, owners if stated]\n\n"
        "## Blockers\n"
        "- [open issues or risks]\n\n"
        "## Next Steps & Owners\n"
        "- [Action — Owner — (due date if any)]\n\n"
        "## Suggested Improvements (to improve the meeting flow/process)\n"
        "- [short bullets]\n\n"
        f"SOURCE MATERIAL START\n{source_text}\nSOURCE MATERIAL END"
    )

    task = Task(
        description=meeting_task_desc,
        expected_output="A meeting flow in markdown with the exact headings specified above.",
        agent=meeting_flow_agent,
    )

    crew = Crew(agents=[meeting_flow_agent], tasks=[task], process=Process.sequential)
    flow_output = crew.kickoff()

    return {
        "meeting_flow": str(flow_output),
        "product_name": product_name or "Unknown Product",
        "product_domain": product_domain or "general product"
    }


def generate_client_dossier(client_name: str = "Techify Solutions", client_domain: str = "", client_context: str = ""):
    """
    Generate client dossier using Perplexity API for intensive research.
    Returns: { "client_dossier": str }
    """
    if not client_name:
        client_name = "Techify Solutions"
    
    # Use Perplexity API for intensive research
    research_prompt = f"Do intensive research on the company {client_name} and give me a massive report on everything you find."
    
    try:
        # Get research from Perplexity API
        perplexity_research = ask_perplexity_api(research_prompt)
        
        # Use CrewAI agent to structure the research into a proper dossier format
        client_agent = agents.client_dossier_creator(client_name, client_domain)
        
        task_desc = (
            f"Do intensive research on the company Techify Solutions and give me a massive report on everything you find.\n\n"
            "Return MARKDOWN only, with the exact headings (in this order):\n"
            "# Client Dossier: {name}\n"
            "## Executive Summary\n"
            "## Company Overview\n"
            "## Industry & Market Position\n"
            "## Business Challenges & Pain Points\n"
            "## Key Decision Makers & Stakeholders\n"
            "## Previous Interactions & History\n"
            "## Strategic Opportunities\n"
            "## Recommended Approach\n\n"
            "PERPLEXITY RESEARCH START\n"
            f"{perplexity_research}\n"
            "PERPLEXITY RESEARCH END\n\n"
            "ADDITIONAL CONTEXT START\n"
            f"{client_context or 'No additional context provided.'}\n"
            "ADDITIONAL CONTEXT END\n\n"
            "Use the PERPLEXITY RESEARCH and ADDITIONAL CONTEXT sections above to write the dossier. "
            "Structure the information into the specified sections. If information for a section is missing, "
            "write 'Information not available in research.' for that section. "
            "Do NOT invent facts about the client."
        ).replace("{name}", client_name)

        task = Task(
            description=task_desc,
            expected_output="Markdown client dossier with the headings specified above.",
            agent=client_agent,
        )

        crew = Crew(agents=[client_agent], tasks=[task], process=Process.sequential)
        dossier_output = crew.kickoff()

        return {
            "client_dossier": str(dossier_output)
        }
        
    except Exception as e:
        return {
            "client_dossier": f"# Client Dossier: {client_name}\n\nError generating client dossier: {str(e)}\n\nPlease check your Perplexity API key configuration."
        }

def generate_complete_email_dossier(analysis_payload: dict, include_product: bool = True, include_client: bool = False, client_context: str = ""):
    """
    Generate a complete email dossier with all three components:
    1. Meeting Flow (from analysis)
    2. Product Dossier (from .md files) - optional
    3. Client Dossier (from context) - optional
    
    Returns: { 
        "meeting_flow": str, 
        "product_dossier": str (if included), 
        "client_dossier": str (if included),
        "product_name": str, 
        "product_domain": str 
    }
    """
    result = {}
    
    # Always generate meeting flow
    meeting_result = generate_meeting_flow_dossier(analysis_payload)
    result.update(meeting_result)
    
    # Extract product info for other dossiers
    product_name = meeting_result.get("product_name", "Unknown Product")
    product_domain = meeting_result.get("product_domain", "general product")
    
    # Optionally generate product dossier
    if include_product and product_name and product_name.lower() not in {"unknown", "unknown product", ""}:
        try:
            product_result = generate_product_dossier(product_name, product_domain)
            result.update(product_result)
        except Exception as e:
            result["product_dossier"] = f"Error generating product dossier: {e}"
    
    # Optionally generate client dossier
    if include_client:
        try:
            # Try to extract client name from analysis if not provided
            client_name = ""  # This would need to be extracted from analysis or provided separately
            client_result = generate_client_dossier(client_name, "", client_context)
            result.update(client_result)
        except Exception as e:
            result["client_dossier"] = f"Error generating client dossier: {e}"
    
    return result
    
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

@app.route("/api/generate_meeting_dossier", methods=["POST"])
def api_generate_meeting_dossier():
    """Generate only the meeting flow dossier from analysis"""
    try:
        data = request.get_json()
        analysis_payload = data.get('analysis')
        if not analysis_payload:
            return jsonify({'error': 'analysis payload is required'}), 400
        
        result = generate_meeting_flow_dossier(analysis_payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/generate_product_dossier", methods=["POST"])
def api_generate_product_dossier():
    """Generate only the product dossier from .md files"""
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        product_domain = data.get('product_domain', 'general product')
        
        if not product_name:
            return jsonify({'error': 'product_name is required'}), 400
        
        result = generate_product_dossier(product_name, product_domain)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/generate_client_dossier", methods=["POST"])
def api_generate_client_dossier():
    """Generate only the client dossier (placeholder for future implementation)"""
    try:
        data = request.get_json()
        client_name = data.get('client_name', '')
        client_domain = data.get('client_domain', '')
        client_context = data.get('client_context', '')
        
        result = generate_client_dossier(client_name, client_domain, client_context)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/generate_dossier", methods=["POST"])
def api_generate_dossier():
    """
    Updated main dossier endpoint - now supports generating complete dossier with all 3 components
    or individual components based on parameters
    """
    try:
        data = request.get_json()
        
        # Check what type of dossier generation is requested
        dossier_type = data.get('type', 'complete')  # 'complete', 'meeting', 'product', 'client'
        
        if dossier_type == 'meeting':
            analysis_payload = data.get('analysis')
            if not analysis_payload:
                return jsonify({'error': 'analysis payload is required for meeting dossier'}), 400
            result = generate_meeting_flow_dossier(analysis_payload)
            
        elif dossier_type == 'product':
            product_name = data.get('product_name')
            product_domain = data.get('product_domain', 'general product')
            if not product_name:
                return jsonify({'error': 'product_name is required for product dossier'}), 400
            result = generate_product_dossier(product_name, product_domain)
            
        elif dossier_type == 'client':
            client_name = data.get('client_name', '')
            client_domain = data.get('client_domain', '')
            client_context = data.get('client_context', '')
            result = generate_client_dossier(client_name, client_domain, client_context)
            
        else:  # 'complete' or default
            analysis_payload = data.get('analysis')
            if not analysis_payload:
                return jsonify({'error': 'analysis payload is required for complete dossier'}), 400
            
            include_product = data.get('include_product', True)
            include_client = data.get('include_client', False)
            client_context = data.get('client_context', '')
            
            result = generate_complete_email_dossier(
                analysis_payload, 
                include_product=include_product, 
                include_client=include_client, 
                client_context=client_context
            )
        
        return jsonify(result)
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
