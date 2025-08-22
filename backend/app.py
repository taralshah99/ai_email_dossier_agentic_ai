from email import message_from_bytes
import os
import base64
import re
import json
from typing import List, Tuple
from datetime import timedelta
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session #type: ignore
from dotenv import load_dotenv

# Import gmail_utils and requests first (these don't depend on CrewAI)
from gmail_utils import list_email_threads, get_email_thread, get_thread_subject_and_sender, get_gmail_user_profile
import requests

# Import CrewAI only when needed (lazy import to avoid .env encoding issues)
# from crewai import Crew, Process, Task, LLM
# from crewai_agents import MeetingAgents

# Import our authentication modules
from auth import (
    initiate_oauth_flow, handle_oauth_callback, is_authenticated, 
    get_current_user, logout, require_auth, get_gmail_service as get_auth_gmail_service
)
from session_manager import setup_session_cleanup, validate_session, create_session, get_session_info

# --- Load .env variables ---
try:
    load_dotenv()
except UnicodeDecodeError as e:
    print(f"Warning: Could not load .env file due to encoding issue: {e}")
    print("Continuing with default environment variables...")

# Disable CrewAI telemetry to prevent timeout issues
import os
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

# Allow insecure transport for local OAuth development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def extract_company_name_from_domain(domain_part):
    """
    Enhanced company name extraction from domain parts.
    Uses purely algorithmic approach based on linguistic patterns.
    """
    if not domain_part:
        return None
        
    company_name = domain_part.lower()
    
    def find_natural_breaks(word):
        """Find natural word boundaries using linguistic patterns only."""
        if len(word) <= 4:
            return [word]
        
        potential_breaks = []
        
        # Pattern 1: Vowel followed by consonant cluster (e.g., "hal-al")
        for i in range(1, len(word) - 1):
            if (word[i-1] in 'aeiou' and 
                word[i] not in 'aeiou' and 
                i + 1 < len(word) and word[i+1] in 'aeiou'):
                potential_breaks.append(i)
        
        # Pattern 2: Double consonants (e.g., "app-le", "buff-et")
        for i in range(1, len(word) - 1):
            if word[i-1] == word[i] and word[i] not in 'aeiou':
                potential_breaks.append(i)
        
        # Pattern 3: Consonant cluster to vowel (e.g., "str-ong")
        for i in range(2, len(word) - 1):
            if (word[i-2] not in 'aeiou' and 
                word[i-1] not in 'aeiou' and 
                word[i] in 'aeiou'):
                potential_breaks.append(i-1)
        
        # Pattern 4: Detect potential suffix boundaries algorithmically
        # Look for patterns where vowel patterns change near the end
        if len(word) > 6:
            for i in range(len(word) - 4, len(word) - 1):
                if i > 2 and word[i-1] not in 'aeiou' and word[i] in 'aeiou':
                    # This might be a suffix boundary
                    potential_breaks.append(i)
        
        # If we found potential breaks, choose the best one
        if potential_breaks:
            # Prefer breaks that create more balanced word parts
            best_break = min(potential_breaks, 
                           key=lambda x: abs(x - len(word) // 2))
            return [word[:best_break], word[best_break:]]
        
        # If no clear patterns, try a simple middle split for very long words
        if len(word) > 8:
            mid = len(word) // 2
            # Find the nearest vowel-consonant boundary to the middle
            for offset in range(1, 3):
                for pos in [mid - offset, mid + offset]:
                    if (0 < pos < len(word) - 1 and 
                        word[pos-1] in 'aeiou' and word[pos] not in 'aeiou'):
                        return [word[:pos], word[pos:]]
        
        return [word]
    
    # Handle "the" prefix
    if company_name.startswith("the") and len(company_name) > 3:
        remainder = company_name[3:]
        words = find_natural_breaks(remainder)
        if len(words) > 1:
            company_name = "The " + " ".join(word.capitalize() for word in words)
        else:
            company_name = f"The {remainder.capitalize()}"
    else:
        # Handle camelCase first
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', company_name)
        
        # If no camelCase and word is long, try natural breaking
        if spaced == company_name and len(company_name) > 6:
            words = find_natural_breaks(company_name)
            if len(words) > 1:
                company_name = " ".join(word.capitalize() for word in words)
            else:
                company_name = company_name.capitalize()
        else:
            company_name = spaced.capitalize()
    
    # Clean up separators and apply title case
    company_name = company_name.replace("-", " ").replace("_", " ").title()
    
    return company_name

def extract_all_participants_from_emails(emails, gmail_service=None):
    """
    Extract ALL participants from email headers: FROM, TO, CC, BCC, and additional delivery headers.
    Returns a comprehensive list of all people involved in the email thread.
    
    IMPROVEMENTS MADE:
    1. Added Gmail service parameter to get user profile
    2. Enhanced email parsing to handle both angle-bracketed and plain email addresses
    3. Added Gmail user detection and inclusion
    4. Added comprehensive debugging output
    5. Improved header parsing for delivery headers (delivered-to, x-original-to)
    6. Added fallback mechanisms for Gmail user identification
    """
    participants = {}
    header_stats = {"from": 0, "to": 0, "cc": 0, "bcc": 0, "delivered-to": 0, "x-original-to": 0}
    
    if not emails:
        return participants
    
    print(f"[extract_participants] Processing {len(emails)} emails to extract ALL participants...")
    
    # Get Gmail user's email from profile
    gmail_user_email = None
    if gmail_service:
        try:
            from gmail_utils import get_gmail_user_profile
            profile = get_gmail_user_profile(gmail_service)
            if profile:
                gmail_user_email = profile.get("emailAddress", "").lower()
                print(f"[extract_participants] Found Gmail user email from profile: {gmail_user_email}")
        except Exception as e:
            print(f"[extract_participants] Error getting Gmail user profile: {e}")
    
    # Fallback: Try to get Gmail user's email from the first email's headers
    if not gmail_user_email and emails:
        first_email_headers = emails[0].get("payload", {}).get("headers", [])
        
        # Method 1: Check for SENT label in x-gmail-labels
        for header in first_email_headers:
            if header.get("name", "").lower() == "x-gmail-labels":
                labels = header.get("value", "")
                if "SENT" in labels:
                    # Find the sender of this email to get Gmail user's email
                    for h in first_email_headers:
                        if h.get("name", "").lower() == "from":
                            from_value = h.get("value", "")
                            email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', from_value)
                            if email_match:
                                gmail_user_email = email_match.group(1) or email_match.group(2)
                                gmail_user_email = gmail_user_email.strip().lower()
                                print(f"[extract_participants] Found Gmail user email from SENT label: {gmail_user_email}")
                                break
                break
        
        # Method 2: If no SENT label, check for Gmail user in all emails
        if not gmail_user_email:
            # Look for emails where the user appears as sender but not in other headers
            potential_gmail_users = set()
            for email in emails:
                headers = email.get("payload", {}).get("headers", [])
                from_emails = []
                to_emails = []
                cc_emails = []
                
                for header in headers:
                    name = header.get("name", "").lower()
                    value = header.get("value", "")
                    
                    if name == "from" and value:
                        from_emails.extend([addr.strip() for addr in value.split(",")])
                    elif name in ["to", "cc"] and value:
                        if name == "to":
                            to_emails.extend([addr.strip() for addr in value.split(",")])
                        else:
                            cc_emails.extend([addr.strip() for addr in value.split(",")])
                
                # Extract email addresses
                for addr in from_emails:
                    email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', addr)
                    if email_match:
                        email_addr = email_match.group(1) or email_match.group(2)
                        email_addr = email_addr.strip().lower()
                        potential_gmail_users.add(email_addr)
                
                # If this email has a sender that doesn't appear in TO/CC of other emails, it might be the Gmail user
                for addr in from_emails:
                    email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', addr)
                    if email_match:
                        email_addr = email_match.group(1) or email_match.group(2)
                        email_addr = email_addr.strip().lower()
                        
                        # Check if this email appears in TO/CC of other emails
                        appears_as_recipient = False
                        for other_email in emails:
                            if other_email != email:
                                other_headers = other_email.get("payload", {}).get("headers", [])
                                for h in other_headers:
                                    if h.get("name", "").lower() in ["to", "cc"]:
                                        other_value = h.get("value", "")
                                        if email_addr in other_value.lower():
                                            appears_as_recipient = True
                                            break
                        
                        if not appears_as_recipient:
                            gmail_user_email = email_addr
                            print(f"[extract_participants] Found Gmail user email from sender analysis: {gmail_user_email}")
                            break
    
    for email_idx, email in enumerate(emails):
        # Extract from headers
        headers = email.get("payload", {}).get("headers", [])
        
        # Track participants found in this email
        email_participants = set()
        
        # Debug: Print all headers for the first email to see what we're working with
        if email_idx == 0:
            print(f"[extract_participants] DEBUG: First email headers:")
            for h in headers:
                print(f"[extract_participants]   {h.get('name', 'NO_NAME')}: {h.get('value', 'NO_VALUE')[:100]}...")
            
            # Also print the raw message structure for debugging
            print(f"[extract_participants] DEBUG: First email structure keys: {list(email.keys())}")
            if 'payload' in email:
                print(f"[extract_participants] DEBUG: Payload keys: {list(email['payload'].keys())}")
                if 'headers' in email['payload']:
                    print(f"[extract_participants] DEBUG: Header count: {len(email['payload']['headers'])}")
        
        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")
            
            # Comprehensive header extraction - FROM, TO, CC, BCC and delivery headers
            if name in ["from", "to", "cc", "bcc", "delivered-to", "x-original-to", "reply-to"] and value:
                # Normalize header names for role assignment
                normalized_name = name
                if name in ["delivered-to", "x-original-to"]:
                    normalized_name = "to"  # Treat delivery headers as 'to' recipients
                elif name == "reply-to":
                    normalized_name = "to"  # Reply-to addresses are also recipients
                
                # Split multiple addresses (comma-separated) and clean them
                addresses = [addr.strip() for addr in value.split(",")]
                
                for addr in addresses:
                    if "@" in addr:
                        # Extract email using comprehensive regex patterns
                        email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', addr)
                        if email_match:
                            email_addr = email_match.group(1) or email_match.group(2)
                            email_addr = email_addr.strip().lower()  # Normalize email
                            
                            # Extract and clean display name
                            display_name = re.sub(r'<[^>]+>', '', addr).strip().strip('"\'')
                            
                            # If no display name found, generate from email
                            if not display_name or display_name == email_addr:
                                local_part = email_addr.split('@')[0]
                                # Smart name generation from email local part
                                if '.' in local_part:
                                    # john.doe -> John Doe
                                    name_parts = [part for part in local_part.split('.') if part]
                                    display_name = ' '.join(part.capitalize() for part in name_parts)
                                elif '_' in local_part:
                                    # john_doe -> John Doe  
                                    name_parts = [part for part in local_part.split('_') if part]
                                    display_name = ' '.join(part.capitalize() for part in name_parts)
                                else:
                                    # jsmith -> Jsmith
                                    display_name = local_part.capitalize()
                            
                            # Add to participants dictionary
                            if email_addr not in participants:
                                participants[email_addr] = {
                                    "email": email_addr,
                                    "display_name": display_name,
                                    "roles": set()
                                }
                            
                            # Add role and track statistics
                            participants[email_addr]["roles"].add(normalized_name)
                            email_participants.add(email_addr)
                            header_stats[name if name in header_stats else "other"] += 1
                        
                        # Also check for email addresses without angle brackets
                        elif re.search(r'[^\s<>]+@[^\s<>]+', addr):
                            # This is a plain email address without display name
                            email_addr = addr.strip().lower()
                            local_part = email_addr.split('@')[0]
                            
                            # Generate display name
                            if '.' in local_part:
                                name_parts = [part for part in local_part.split('.') if part]
                                display_name = ' '.join(part.capitalize() for part in name_parts)
                            elif '_' in local_part:
                                name_parts = [part for part in local_part.split('_') if part]
                                display_name = ' '.join(part.capitalize() for part in name_parts)
                            else:
                                display_name = local_part.capitalize()
                            
                            # Add to participants dictionary
                            if email_addr not in participants:
                                participants[email_addr] = {
                                    "email": email_addr,
                                    "display_name": display_name,
                                    "roles": set()
                                }
                            
                            # Add role and track statistics
                            participants[email_addr]["roles"].add(normalized_name)
                            email_participants.add(email_addr)
                            header_stats[name if name in header_stats else "other"] += 1
        
        # Log participants found in this email
        if len(emails) <= 3:  # Only log for small threads to avoid spam
            print(f"[extract_participants] Email {email_idx + 1}: Found {len(email_participants)} participants")
    
    # Add Gmail user if we found their email and they're not already in participants
    if gmail_user_email and gmail_user_email not in participants:
        local_part = gmail_user_email.split('@')[0]
        if '.' in local_part:
            name_parts = [part for part in local_part.split('.') if part]
            display_name = ' '.join(part.capitalize() for part in name_parts)
        elif '_' in local_part:
            name_parts = [part for part in local_part.split('_') if part]
            display_name = ' '.join(part.capitalize() for part in name_parts)
        else:
            display_name = local_part.capitalize()
        
        participants[gmail_user_email] = {
            "email": gmail_user_email,
            "display_name": display_name,
            "roles": set(["gmail_user"])  # Special role for Gmail user
        }
        print(f"[extract_participants] Added Gmail user: {display_name} ({gmail_user_email})")
    
    # Summary logging
    total_found = len(participants)
    print(f"[extract_participants] ===== EXTRACTION SUMMARY =====")
    print(f"[extract_participants] Total unique participants: {total_found}")
    print(f"[extract_participants] Header breakdown: FROM({header_stats['from']}), TO({header_stats['to']}), CC({header_stats['cc']}), BCC({header_stats['bcc']})")
    
    # Detailed participant list
    print(f"[extract_participants] ===== ALL PARTICIPANTS =====")
    for email, participant in participants.items():
        roles_list = list(participant['roles'])
        print(f"[extract_participants] • {participant['display_name']} ({email}) - Roles: {roles_list}")
    
    # Convert sets to lists for JSON serialization
    for participant in participants.values():
        participant["roles"] = list(participant["roles"])
    
    print(f"[extract_participants] ===== EXTRACTION COMPLETE =====")
    return participants

def format_email_metadata(emails):
    """Extract From, To, CC addresses and return clean string for prompt."""
    from_addresses = []
    to_addresses = []
    cc_addresses = []

    for email in emails:
        if "from" in email:
            from_addresses.append(email["from"])
        if "to" in email and isinstance(email["to"], list):
            to_addresses.extend(email["to"])
        if "cc" in email and isinstance(email["cc"], list):
            cc_addresses.extend(email["cc"])

    def extract_domain(addr):
        if "@" in addr:
            domain = addr.split("@")[-1]
            base = domain.split(".")[0]
            return extract_company_name_from_domain(base)
        return None

    domains = set()
    for addr in from_addresses + to_addresses + cc_addresses:
        d = extract_domain(addr)
        if d:
            domains.add(d)

    if not domains:
        return "Email Participants' Companies (from metadata): Unknown"

    return f"Email Participants' Companies (from metadata): {', '.join(domains)}"


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
# Initialize these as None and load them lazily to avoid .env encoding issues
llm = None
agents = None

def get_llm():
    """Lazy load LLM to avoid startup issues."""
    global llm
    if llm is None:
        # Must set LiteLLM-compatible env vars:
        os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_KEY", "")
        os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "")
        
        # Import CrewAI only when needed
        from crewai import LLM
        from crewai_agents import MeetingAgents
        
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        llm = LLM(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model=f"azure/{azure_deployment}"
        )
    return llm

def get_agents():
    """Lazy load agents to avoid startup issues."""
    global agents
    if agents is None:
        # Import CrewAI only when needed
        from crewai_agents import MeetingAgents
        
        agents = MeetingAgents(get_llm())
    return agents

# --- Gmail Service (lazy init to avoid startup crash if creds missing) ---
gmail_service = None
gmail_service_error = None

def ensure_gmail_service():
    """Get authenticated Gmail service using session-based credentials."""
    try:
        # Use our new authentication system
        return get_auth_gmail_service()
    except Exception as e:
        raise RuntimeError(
            f"Gmail service is not available: {str(e)}. Please ensure you are logged in."
        )

# --- Flask app setup ---
app = Flask(__name__)

# Flask-Session configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False  # Let us control permanence manually
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Use a unique session directory to avoid conflicts and Windows file lock issues
import tempfile
session_dir = os.path.join(tempfile.gettempdir(), 'email_dossier_sessions')
os.makedirs(session_dir, exist_ok=True)
app.config['SESSION_FILE_DIR'] = session_dir

# Configure session settings to minimize file lock issues
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['SESSION_FILE_MODE'] = 0o600
app.config['SESSION_USE_SIGNER'] = True  # Sign session cookies
app.config['SESSION_KEY_PREFIX'] = 'email-dossier:'  # Unique prefix

# Additional settings to help with Windows file handling
if os.name == 'nt':  # Windows
    app.config['SESSION_FILE_THRESHOLD'] = 100  # Lower threshold for Windows
    app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Reduce file writes

# Initialize Flask-Session
Session(app)

# Setup session cleanup on server shutdown
setup_session_cleanup()

# Configure CORS with proper settings
CORS(app, 
     supports_credentials=True, 
     origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# --- Helper: Ask Azure ---
def ask_azure_openai(prompt: str):
    # CrewAI's LLM is based on LiteLLM, so we use its invoke-style interface
    return get_llm().complete(messages=[{"role": "user", "content": prompt}]).choices[0]["message"]["content"]

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
    - client_name: str
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

        # Derive top-level client/product info if available (first product seen)
        top_client_name = "Unknown Client"
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
            top_client_name = first.get("client_name") or top_client_name
            top_product_name = first.get("product_name") or top_product_name
            top_product_domain = first.get("product_domain") or top_product_domain

        return {
            "groups": groups_out,
            "global_summary": global_summary_out,
            "client_name": top_client_name,
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

    # Extract client & product info from markdown text
    def _extract_field(label, default=None):
        pattern = rf"{label}:\s*\**(.+?)\**\s*$"
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        return match.group(1).strip() if match else default

    def clean_extracted_name(name):
        """Clean up extracted names by removing explanatory text and parenthetical remarks."""
        if not name:
            return name
        
        # Remove parenthetical explanations like "(likely X organization)" or "(domain not stated)"
        cleaned = re.sub(r'\s*\([^)]*\)', '', name)
        
        # Remove common explanatory prefixes/suffixes
        cleaned = re.sub(r'^\s*(likely|probably|appears to be|seems to be)\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*(organization|company|corp|inc|ltd)?\s*;\s*.*$', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()

    client_name = clean_extracted_name(_extract_field("Client Name", "Unknown Client"))
    product_name = clean_extracted_name(_extract_field("Product Name", "Unknown Product"))
    product_domain = _extract_field("Product Domain", "general product")

    structured.update({
        "client_name": client_name,
        "product_name": product_name,
        "product_domain": product_domain,
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


def process_threads_metadata_only(thread_ids: list):
    """
    Extract metadata from threads without performing AI analysis.
    Returns thread metadata, participants, and basic client/product info from domains.
    """
    if not thread_ids:
        return None
    
    all_thread_metadata = []
    combined_participants = {}
    all_dates = []
    all_messages = []  # Collect all messages for client name extraction
    
    service = get_auth_gmail_service()
    
    for thread_id in thread_ids:
        try:
            # Get thread metadata
            subject, sender = get_thread_subject_and_sender(service, thread_id)
            if not subject:
                continue
                
            # Get messages for metadata extraction
            messages = get_email_thread(service, thread_id)
            if not messages:
                continue
            
            # Store messages for client name extraction
            all_messages.extend(messages)
            
            # Extract participants
            thread_participants = {}
            participants = extract_all_participants_from_emails(messages, service)
            
            # Add Gmail user to participants
            try:
                gmail_profile = get_gmail_user_profile(service)
                if gmail_profile:
                    gmail_user_email = gmail_profile.get("emailAddress", "").lower()
                    if gmail_user_email and gmail_user_email not in participants:
                        local_part = gmail_user_email.split('@')[0]
                        if '.' in local_part:
                            name_parts = [part for part in local_part.split('.') if part]
                            display_name = ' '.join(part.capitalize() for part in name_parts)
                        elif '_' in local_part:
                            name_parts = [part for part in local_part.split('_') if part]
                            display_name = ' '.join(part.capitalize() for part in name_parts)
                        else:
                            display_name = local_part.capitalize()
                        
                        participants[gmail_user_email] = {
                            "email": gmail_user_email,
                            "display_name": display_name,
                            "roles": ["gmail_user"]
                        }
            except Exception as e:
                print(f"[process_threads_metadata_only] Error adding Gmail user: {e}")
            
            thread_participants = participants
            
            # Merge participants
            for email, participant in thread_participants.items():
                if email not in combined_participants:
                    combined_participants[email] = participant
                else:
                    existing_roles = set(combined_participants[email]["roles"])
                    new_roles = set(participant["roles"])
                    combined_participants[email]["roles"] = list(existing_roles.union(new_roles))
            
            # Extract dates
            thread_dates = []
            for msg in messages:
                headers = msg.get("payload", {}).get("headers", [])
                for header in headers:
                    if header.get("name", "").lower() == "date":
                        try:
                            from email.utils import parsedate_to_datetime
                            date_value = header.get("value", "")
                            if date_value:
                                date_obj = parsedate_to_datetime(date_value)
                                if date_obj:
                                    thread_dates.append(date_obj)
                                    all_dates.append(date_obj)
                        except Exception as e:
                            print(f"Error parsing date '{header.get('value', '')}': {e}")
                            pass
            
            # Sort dates
            thread_dates.sort()
            
            thread_metadata = {
                "thread_id": thread_id,
                "subject": subject,
                "sender": sender,
                "message_count": len(messages),
                "participants": thread_participants,
                "first_email_date": thread_dates[0].strftime("%Y-%m-%d %H:%M:%S") if thread_dates else None,
                "last_email_date": thread_dates[-1].strftime("%Y-%m-%d %H:%M:%S") if thread_dates else None
            }
            all_thread_metadata.append(thread_metadata)
            
        except Exception as e:
            print(f"[process_threads_metadata_only] Error processing thread {thread_id}: {e}")
            continue
    
    # Extract client names from all collected messages using proper logic that filters out Gmail user's domain
    print(f"[process_threads_metadata_only] Starting client name extraction with {len(all_messages)} messages")
    if all_messages:
        domain_based_client_names = extract_client_name_from_domains(all_messages, service)
        print(f"[process_threads_metadata_only] Extracted client names: {domain_based_client_names}")
        
        # Additional debugging: check what domains were found
        if domain_based_client_names == ["Unknown Client"]:
            print(f"[process_threads_metadata_only] WARNING: Client extraction returned 'Unknown Client'")
            # Let's check the first few messages for debugging
            for i, msg in enumerate(all_messages[:2]):
                headers = msg.get("payload", {}).get("headers", [])
                from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "Not found")
                to_header = next((h["value"] for h in headers if h["name"].lower() == "to"), "Not found")
                print(f"[process_threads_metadata_only] Message {i+1} - From: {from_header}, To: {to_header}")
    else:
        domain_based_client_names = ["Unknown Client"]
        print(f"[process_threads_metadata_only] No messages found, using fallback client names")
    
    # Create combined metadata
    if all_dates:
        all_dates.sort()
    
    combined_metadata = {
        "thread_count": len(thread_ids),
        "total_participants": len(combined_participants),
        "participants": {email: {
            "email": p["email"],
            "display_name": p["display_name"],
            "roles": list(p["roles"])
        } for email, p in combined_participants.items()},
        "first_email_date": all_dates[0].strftime("%Y-%m-%d %H:%M:%S") if all_dates else None,
        "last_email_date": all_dates[-1].strftime("%Y-%m-%d %H:%M:%S") if all_dates else None,
        "threads": all_thread_metadata
    }
    
    # Basic product info extraction (without AI analysis)
    product_info = {"product_name": "Unknown Product", "product_domain": "general product"}
    
    return {
        "thread_count": len(thread_ids),
        "combined_metadata": combined_metadata,
        "available_client_names": domain_based_client_names,
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"],
        "processed_thread_ids": thread_ids
    }

def analyze_thread_content(thread_id: str):
    try:
        print(f"[analyze_thread_content] Starting analysis for thread: {thread_id}")
        service = ensure_gmail_service()
        print(f"[analyze_thread_content] Gmail service obtained")
        
        print(f"[analyze_thread_content] Fetching email thread...")
        messages = get_email_thread(service, thread_id)
        print(f"[analyze_thread_content] Retrieved {len(messages) if messages else 0} messages")

        # NEW: Fetch subject & sender
        print(f"[analyze_thread_content] Fetching subject and sender...")
        subject, sender = get_thread_subject_and_sender(service, thread_id)
        print(f"[analyze_thread_content] Subject: {subject}, Sender: {sender}")
        
        # Extract thread metadata
        print(f"[analyze_thread_content] Extracting participants...")
        participants = extract_all_participants_from_emails(messages, service)
        print(f"[analyze_thread_content] Found {len(participants)} participants")
        
        # Ensure Gmail user is always included
        try:
            from gmail_utils import get_gmail_user_profile
            gmail_profile = get_gmail_user_profile(service)
            if gmail_profile:
                gmail_user_email = gmail_profile.get("emailAddress", "").lower()
                if gmail_user_email and gmail_user_email not in participants:
                    local_part = gmail_user_email.split('@')[0]
                    if '.' in local_part:
                        name_parts = [part for part in local_part.split('.') if part]
                        display_name = ' '.join(part.capitalize() for part in name_parts)
                    elif '_' in local_part:
                        name_parts = [part for part in local_part.split('_') if part]
                        display_name = ' '.join(part.capitalize() for part in name_parts)
                    else:
                        display_name = local_part.capitalize()
                    
                    participants[gmail_user_email] = {
                        "email": gmail_user_email,
                        "display_name": display_name,
                        "roles": ["gmail_user"]
                    }
                    print(f"[analyze_thread_content] Added Gmail user to participants: {display_name} ({gmail_user_email})")
        except Exception as e:
            print(f"[analyze_thread_content] Error adding Gmail user to participants: {e}")
        
        thread_metadata = {
            "thread_id": thread_id,
            "subject": subject,
            "sender": sender,
            "message_count": len(messages) if messages else 0,
            "participants": participants,
            "first_email_date": None,
            "last_email_date": None
        }
    except Exception as e:
        print(f"[analyze_thread_content] Error in initialization: {e}")
        import traceback
        traceback.print_exc()
        # Return a minimal response to prevent complete failure
        return {
            "analysis": f"Error analyzing thread {thread_id}: {str(e)}",
            "structured_analysis": {"client_name": "Unknown Client", "product_name": "Unknown Product", "product_domain": "general product"},
            "product_name": "Unknown Product",
            "product_domain": "general product",
            "thread_metadata": {
                "thread_id": thread_id,
                "subject": "Error",
                "sender": "Unknown",
                "message_count": 0,
                "participants": {},
                "first_email_date": None,
                "last_email_date": None
            }
        }
    
    # Extract dates from messages
    if messages:
        dates = []
        for msg in messages:
            headers = msg.get("payload", {}).get("headers", [])
            for header in headers:
                if header.get("name", "").lower() == "date":
                    try:
                        from email.utils import parsedate_to_datetime
                        date_value = header.get("value", "")
                        if date_value:
                            date_obj = parsedate_to_datetime(date_value)
                            if date_obj:  # Make sure we got a valid date object
                                dates.append(date_obj)
                    except Exception as e:
                        # Log the error but continue processing
                        print(f"Error parsing date '{header.get('value', '')}': {e}")
                        pass
        
        if dates:
            dates.sort()
            thread_metadata["first_email_date"] = dates[0].strftime("%Y-%m-%d %H:%M:%S")
            thread_metadata["last_email_date"] = dates[-1].strftime("%Y-%m-%d %H:%M:%S")

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
    print(f"[analyze_thread_content] Email content length: {len(full_email_thread_text)} characters")

    print(f"[analyze_thread_content] Creating analysis agent...")
    analysis_agent = get_agents().meeting_agenda_extractor()

    print(f"[analyze_thread_content] Creating analysis task...")
    # Import CrewAI components when needed
    from crewai import Task, Crew, Process
    
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
            "**Client Name:** [If present; else 'Unknown Client']\n"
            "**Product Name:** [If present; else 'Unknown']\n"
            "**Product Domain:** [If present; else best-guess domain, e.g., 'SaaS', 'HR tech', 'payments']\n\n"
            f"--- EMAIL THREAD CONTENT (verbatim) ---\n{full_email_thread_text}"
        ),
        expected_output=(
            "A detailed and strictly structured report that follows the template, with a multi-sentence Final Conclusion and no 'first email says' phrasing when only one email exists."
        ),
        agent=analysis_agent
    )

    print(f"[analyze_thread_content] Starting CrewAI analysis...")
    crew = Crew(agents=[analysis_agent], tasks=[task], process=Process.sequential)
    
    try:
        analysis_output = crew.kickoff()
        print(f"[analyze_thread_content] CrewAI analysis completed successfully")
    except Exception as e:
        print(f"[analyze_thread_content] CrewAI analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    product_info = parse_product_info(analysis_output)
    
    # NEW: Extract client names from email domains
    print(f"[analyze_thread_content] Extracting client names from email domains...")
    domain_based_client_names = extract_client_name_from_domains(messages, service)
    print(f"[analyze_thread_content] Domain-based client names: {domain_based_client_names}")
    
    # Get the LLM-extracted client name
    structured_analysis = structure_analysis_output(analysis_output)
    llm_client_name = structured_analysis.get("client_name", "Unknown Client")
    print(f"[analyze_thread_content] LLM-extracted client name: {llm_client_name}")
    
    # Always use domain-based client name as primary method (replacing LLM output)
    # Take the first domain-based client name if available, otherwise use LLM fallback
    if domain_based_client_names and domain_based_client_names[0].lower() not in ["unknown client", "unknown"]:
        final_client_name = domain_based_client_names[0]
        print(f"[analyze_thread_content] Using domain-based client name as primary: {final_client_name}")
    else:
        # Fallback to LLM-extracted client name only if domain extraction failed
        final_client_name = llm_client_name
        print(f"[analyze_thread_content] Using LLM-extracted client name as fallback: {final_client_name}")
    
    # Update the structured analysis with the final client name
    structured_analysis["client_name"] = final_client_name

    return {
        "analysis": str(analysis_output),
        "structured_analysis": structured_analysis,
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"],
        "thread_metadata": thread_metadata,
        "domain_based_client_names": domain_based_client_names,  # Include for debugging
        "available_client_names": domain_based_client_names  # Include for UI selection
    }


def analyze_multiple_threads(thread_ids: list):
    if not thread_ids:
        return None

    all_thread_contents = []
    all_subjects = []
    all_thread_metadata = []
    combined_participants = {}
    all_dates = []

    service = ensure_gmail_service()
    for thread_id in thread_ids:
        messages = get_email_thread(service, thread_id)
        subject, sender = get_thread_subject_and_sender(service, thread_id)
        
        # Extract thread metadata
        thread_participants = extract_all_participants_from_emails(messages, service)
        thread_dates = []
        
        # Ensure Gmail user is always included in this thread's participants
        try:
            from gmail_utils import get_gmail_user_profile
            gmail_profile = get_gmail_user_profile(service)
            if gmail_profile:
                gmail_user_email = gmail_profile.get("emailAddress", "").lower()
                if gmail_user_email and gmail_user_email not in thread_participants:
                    local_part = gmail_user_email.split('@')[0]
                    if '.' in local_part:
                        name_parts = [part for part in local_part.split('.') if part]
                        display_name = ' '.join(part.capitalize() for part in name_parts)
                    elif '_' in local_part:
                        name_parts = [part for part in local_part.split('_') if part]
                        display_name = ' '.join(part.capitalize() for part in name_parts)
                    else:
                        display_name = local_part.capitalize()
                    
                    thread_participants[gmail_user_email] = {
                        "email": gmail_user_email,
                        "display_name": display_name,
                        "roles": ["gmail_user"]
                    }
        except Exception as e:
            print(f"[analyze_multiple_threads] Error adding Gmail user to thread participants: {e}")
        
        # Merge participants
        for email, participant in thread_participants.items():
            if email not in combined_participants:
                combined_participants[email] = participant
            else:
                # Convert both to sets, merge, then back to list
                existing_roles = set(combined_participants[email]["roles"])
                new_roles = set(participant["roles"])
                combined_participants[email]["roles"] = list(existing_roles.union(new_roles))
        
        # Extract dates
        for msg in messages:
            headers = msg.get("payload", {}).get("headers", [])
            for header in headers:
                if header.get("name", "").lower() == "date":
                    try:
                        from email.utils import parsedate_to_datetime
                        date_value = header.get("value", "")
                        if date_value:
                            date_obj = parsedate_to_datetime(date_value)
                            if date_obj:  # Make sure we got a valid date object
                                thread_dates.append(date_obj)
                                all_dates.append(date_obj)
                    except Exception as e:
                        # Log the error but continue processing
                        print(f"Error parsing date '{header.get('value', '')}': {e}")
                        pass
        
        # Sort dates before accessing
        thread_dates.sort()
        
        thread_metadata = {
            "thread_id": thread_id,
            "subject": subject,
            "sender": sender,
            "message_count": len(messages),
            "participants": thread_participants,
            "first_email_date": thread_dates[0].strftime("%Y-%m-%d %H:%M:%S") if thread_dates else None,
            "last_email_date": thread_dates[-1].strftime("%Y-%m-%d %H:%M:%S") if thread_dates else None
        }
        all_thread_metadata.append(thread_metadata)

        email_content = []
        for msg in messages:
            if "snippet" in msg:
                email_content.append(msg["snippet"])
            elif msg.get("payload", {}).get("parts"):
                for part in msg["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        email_content.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))

        thread_text = "\n".join(email_content)

        # NEW: prepend extracted email metadata for LLM to use in client name inference
        metadata_str = format_email_metadata(messages)  # thread_emails should be the raw email dicts with from/to/cc
        thread_text = f"{metadata_str}\n\n{thread_text}"

        all_thread_contents.append(f"=== THREAD: {subject} ===Z\n{thread_text}")
        all_subjects.append(subject)


    combined_content = "\n\n".join(all_thread_contents)
    analysis_agent = get_agents().meeting_agenda_extractor()

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
        "\n      \"products\": [ { \"client_name\": \"string\", \"product_name\": \"string\", \"product_domain\": \"string\" } ]"
        "\n    }"
        "\n  ],"
        "\n  \"global_summary\": {"
        "\n    \"final_conclusion\": \"string\","
        "\n    \"products\": [ { \"client_name\": \"string\", \"product_name\": \"string\", \"product_domain\": \"string\" } ]"
        "\n  }"
        "\n}"
    )

    # Import CrewAI components when needed
    from crewai import Task, Crew, Process

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

    # Extract product info from structured analysis instead of raw text
    product_info = {"product_name": "Unknown Product", "product_domain": "general product"}
    
    try:
        # Try to get product info from structured analysis JSON
        structured_analysis_temp = structure_analysis_output(analysis_output)
        if structured_analysis_temp:
            # Check for products in groups
            if isinstance(structured_analysis_temp, dict) and "groups" in structured_analysis_temp:
                groups = structured_analysis_temp["groups"]
                if isinstance(groups, list) and len(groups) > 0:
                    for group in groups:
                        if isinstance(group, dict) and "products" in group:
                            products = group["products"]
                            if isinstance(products, list) and len(products) > 0:
                                first_product = products[0]
                                if isinstance(first_product, dict):
                                    if "product_name" in first_product and first_product["product_name"]:
                                        product_info["product_name"] = first_product["product_name"]
                                    if "product_domain" in first_product and first_product["product_domain"]:
                                        product_info["product_domain"] = first_product["product_domain"]
                                    break
            
            # Also check global summary for products
            if "global_summary" in structured_analysis_temp:
                global_summary = structured_analysis_temp["global_summary"]
                if isinstance(global_summary, dict) and "products" in global_summary:
                    products = global_summary["products"]
                    if isinstance(products, list) and len(products) > 0:
                        first_product = products[0]
                        if isinstance(first_product, dict):
                            if "product_name" in first_product and first_product["product_name"]:
                                product_info["product_name"] = first_product["product_name"]
                            if "product_domain" in first_product and first_product["product_domain"]:
                                product_info["product_domain"] = first_product["product_domain"]
    except Exception as e:
        print(f"[analyze_multiple_threads] Error extracting product info from JSON: {e}")
        # Fallback to old text-based extraction
    product_info = parse_product_info(analysis_output)
    
    print(f"[analyze_multiple_threads] Extracted product info: {product_info}")
    
    # Extract client names from all messages using proper logic that filters out Gmail user's domain
    all_messages_for_client_extraction = []
    for thread_id in thread_ids:
        try:
            messages = get_email_thread(service, thread_id)
            if messages:
                all_messages_for_client_extraction.extend(messages)
        except Exception as e:
            print(f"[analyze_multiple_threads] Error getting messages for client extraction from thread {thread_id}: {e}")
    
    if all_messages_for_client_extraction:
        domain_based_client_names = extract_client_name_from_domains(all_messages_for_client_extraction, service)
        print(f"[analyze_multiple_threads] Domain-based client names: {domain_based_client_names}")
    else:
        domain_based_client_names = ["Unknown Client"]
    
    # Get the structured analysis and update client name using domain-based logic
    structured_analysis = structure_analysis_output(analysis_output)
    llm_client_name = structured_analysis.get("client_name", "Unknown Client")
    print(f"[analyze_multiple_threads] LLM-extracted client name: {llm_client_name}")
    
    # Always use domain-based client name as primary method (replacing LLM output)
    # Take the first domain-based client name if available, otherwise use LLM fallback
    if domain_based_client_names and domain_based_client_names[0].lower() not in ["unknown client", "unknown"]:
        final_client_name = domain_based_client_names[0]
        print(f"[analyze_multiple_threads] Using domain-based client name as primary: {final_client_name}")
    else:
        # Fallback to LLM-extracted client name only if domain extraction failed
        final_client_name = llm_client_name
        print(f"[analyze_multiple_threads] Using LLM-extracted client name as fallback: {final_client_name}")
    
    # Update the structured analysis with the final client name
    structured_analysis["client_name"] = final_client_name

    # Create combined metadata
    if all_dates:
        all_dates.sort()
    
    combined_metadata = {
        "thread_count": len(thread_ids),
        "total_participants": len(combined_participants),
        "participants": {email: {
            "email": p["email"],
            "display_name": p["display_name"],
            "roles": list(p["roles"])
        } for email, p in combined_participants.items()},
        "first_email_date": all_dates[0].strftime("%Y-%m-%d %H:%M:%S") if all_dates else None,
        "last_email_date": all_dates[-1].strftime("%Y-%m-%d %H:%M:%S") if all_dates else None,
        "threads": all_thread_metadata
    }

    return {
        "analysis": str(analysis_output),
        "structured_analysis": structured_analysis,
        "product_name": product_info["product_name"],
        "product_domain": product_info["product_domain"],
        "thread_count": len(thread_ids),
        "combined_metadata": combined_metadata,
        "available_client_names": domain_based_client_names
    }





def generate_meeting_flow_dossier(analysis_payload: dict):
    """
    Generate ONLY the meeting flow section from analysis data.
    Returns: { "meeting_flow": str, "product_name": str, "product_domain": str }
    """
    print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Analysis payload keys: {list(analysis_payload.keys()) if isinstance(analysis_payload, dict) else 'Not a dict'}")
    print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Analysis payload type: {type(analysis_payload)}")
    print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Analysis payload content preview: {str(analysis_payload)[:500] if isinstance(analysis_payload, dict) else 'Not a dict'}")
    
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

    # Extract metadata for meeting flow
    metadata_text = ""
    
    try:
        if isinstance(analysis_payload, dict):
            print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Checking for thread_metadata...")
            # Single thread metadata
            if "thread_metadata" in analysis_payload:
                meta = analysis_payload["thread_metadata"]
                
                metadata_text = f"""
THREAD METADATA:
- Thread ID: {meta.get('thread_id', 'N/A')}
- Subject: {meta.get('subject', 'N/A')}
- Number of Emails in Thread: {meta.get('message_count', 0)}
- First Email Date: {meta.get('first_email_date', 'N/A')}
- Last Email Date: {meta.get('last_email_date', 'N/A')}
"""
                print(f"[generate_meeting_flow_dossier] ✅ Single thread metadata created")
            
            # Multiple threads metadata
            elif "combined_metadata" in analysis_payload:
                print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Found combined_metadata")
                meta = analysis_payload["combined_metadata"]
                
                metadata_text = f"""
COMBINED THREADS METADATA:
- Total Threads: {meta.get('thread_count', 0)}
- First Email Date: {meta.get('first_email_date', 'N/A')}
- Last Email Date: {meta.get('last_email_date', 'N/A')}

INDIVIDUAL THREADS:
"""
                if meta.get("threads"):
                    for i, thread in enumerate(meta["threads"], 1):
                        metadata_text += f"""
Thread {i}: {thread.get('subject', 'N/A')}
  - ID: {thread.get('thread_id', 'N/A')}
  - Messages: {thread.get('message_count', 0)}
  - Date Range: {thread.get('first_email_date', 'N/A')} to {thread.get('last_email_date', 'N/A')}
"""
                print(f"[generate_meeting_flow_dossier] ✅ Combined metadata created")
            else:
                print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: No thread_metadata or combined_metadata found in analysis_payload")
                print(f"[generate_meeting_flow_dossier] 🔍 DEBUG: Available keys: {list(analysis_payload.keys())}")
                print(f"[generate_meeting_flow_dossier] ❌ NO METADATA found")
                print(f"[generate_meeting_flow_dossier] ⚠️ WARNING: This usually means the frontend is not passing the complete analysis payload. Check that analysisResults is passed directly, not a subset.")
                metadata_text = ""
    except Exception as e:
        metadata_text = f"Error extracting metadata: {str(e)}"

    # Prepare source text for LLM - METADATA FIRST, then analysis
    if metadata_text:
        source_text = metadata_text + "\n\n" + ("\n\n".join([s for s in source_sections if s]).strip() or "No analysis content provided.")
        print(f"[generate_meeting_flow_dossier] ✅ Metadata included in prompt ({len(metadata_text)} chars)")
    else:
        source_text = "\n\n".join([s for s in source_sections if s]).strip() or "No analysis content provided."
        print(f"[generate_meeting_flow_dossier] ❌ NO METADATA found in analysis payload!")
    
    print(f"[generate_meeting_flow_dossier] Total source text length: {len(source_text)} chars")

    # Create a meeting flow task
    meeting_flow_agent = get_agents().meeting_flow_writer()
    meeting_task_desc = (
        "You are generating a 'Meeting Flow Dossier' to help prepare for an upcoming meeting based on email discussions.\n\n"
        "PURPOSE: This dossier should focus on MEETING PREPARATION - what needs to be discussed, decided, and accomplished in the meeting. This is NOT a historical summary but a forward-looking meeting preparation guide.\n\n"
        "CRITICAL: Return CLEAN PLAIN TEXT only. Do NOT use markdown symbols like #, ##, *, or **. Do NOT use special characters like \\u2014 or \\u2019. Use simple dashes and apostrophes.\n\n"

        "CONTENT REQUIREMENTS:\n"
        "- Focus on FUTURE ACTIONS and meeting preparation, not past summaries\n"
        "- Identify what needs to be DISCUSSED, DECIDED, or RESOLVED in the meeting\n"
        "- Extract unresolved issues, pending decisions, and action items from emails\n"
        "- Create a practical meeting agenda based on email discussions\n"
        "- Look for any mentioned meeting dates, times, or scheduling information in the emails\n"
        "- Suggest meeting process improvements based on email communication patterns\n\n"
        "Return exactly this structure in PLAIN TEXT format:\n\n"
        "Meeting Flow Dossier\n\n"
        "Meeting Date and Time\n"
        "- [Extract any mentioned meeting date, time, or scheduling information from the emails. If no specific date/time is mentioned, omit this entire section]\n\n"
        "Meeting Objectives\n"
        "- [Specific objectives for the upcoming meeting based on email discussions]\n\n"
        "Meeting Context\n"
        "[Brief context paragraph explaining why this meeting is needed and what needs to be addressed]\n\n"
        "Key Discussion Points for Meeting\n"
        "- [Main topics that need to be discussed in the meeting]\n\n"
        "Decisions Required\n"
        "- [Specific decisions that need to be made during the meeting]\n\n"
        "Current Blockers to Address\n"
        "- [Issues or blockers that need resolution in the meeting]\n\n"
        "Proposed Meeting Agenda\n"
        "1. [First agenda item]\n"
        "2. [Second agenda item]\n"
        "3. [Additional items as needed]\n\n"
        "Next Steps & Owners (Post-Meeting)\n"
        "- [Actions that should be assigned during the meeting]\n\n"
        "Meeting Process Improvements\n"
        "- [Suggestions to make the meeting more effective]\n\n"
        f"SOURCE MATERIAL START\n{source_text}\nSOURCE MATERIAL END"
    )

    # Import CrewAI components when needed
    from crewai import Task, Crew, Process

    task = Task(
        description=meeting_task_desc,
        expected_output="A meeting flow in plain text format with clear headings and no markdown symbols.",
        agent=meeting_flow_agent,
    )

    crew = Crew(agents=[meeting_flow_agent], tasks=[task], process=Process.sequential)
    
    # Set timeout and disable telemetry to prevent timeout issues
    import os
    os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
    
    try:
        flow_output = crew.kickoff()
    except Exception as e:
        print(f"[generate_meeting_flow_dossier] CrewAI execution error: {e}")
        # Fallback: create a basic meeting flow structure
        flow_text = f"""Meeting Flow Dossier

Meeting Objectives
- Review meeting objectives from email content

Meeting Context
Meeting context extracted from email thread analysis.

Key Discussion Points for Meeting
- Key points that need to be discussed in the meeting

Decisions Required
- Decisions that need to be made during the meeting

Current Blockers to Address
- Any blockers or issues that need resolution

Proposed Meeting Agenda
1. First agenda item
2. Second agenda item
3. Additional items as needed

Next Steps & Owners (Post-Meeting)
- Action items and their owners

Meeting Process Improvements
- Process improvement suggestions"""
        return {
            "meeting_flow": flow_text,
            "product_name": product_name or "Unknown Product",
            "product_domain": product_domain or "general product"
        }
    
    # Get the AI output
    flow_text = str(flow_output)
    
    # Post-process the output to ensure plain text formatting (in case AI still uses markdown)
    def clean_markdown_formatting(text):
        """Remove markdown symbols and ensure plain text formatting"""
        import re
        
        # Remove markdown headers (# and ##)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic markers (** and *)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Ensure proper heading formatting (capitalize first letter of each word)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('-') and not stripped.startswith('•'):
                # This might be a heading - capitalize it properly
                if len(stripped) > 0 and stripped[0].isalpha():
                    # Capitalize first letter of each word for headings
                    words = stripped.split()
                    if len(words) <= 5:  # Likely a heading if 5 words or less
                        cleaned_lines.append(' '.join(word.capitalize() for word in words))
                        continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    # Clean the output to ensure plain text formatting
    flow_text = clean_markdown_formatting(flow_text)


    return {
        "meeting_flow": flow_text,
        "product_name": product_name or "Unknown Product",
        "product_domain": product_domain or "general product"
    }


def generate_client_dossier(client_name: str = "", client_domain: str = "", client_context: str = ""):
    """
    Generate client dossier using Perplexity API for intensive research.
    Returns: { "client_dossier": str }
    """
    # Validate that we have a real client name
    if not client_name or client_name.lower() in ["unknown client", "unknown", ""]:
        return {
            "client_dossier": "",
            "error": "No valid client name provided. Client dossier generation skipped."
        }
    
    # Use Perplexity API for intensive research
    research_prompt = f"Do intensive research on the company {client_name} and give me a massive report on everything you find."
    
    try:
        # Get research from Perplexity API
        perplexity_research = ask_perplexity_api(research_prompt)
        
        # Use CrewAI agent to structure the research into a proper dossier format
        client_agent = get_agents().client_dossier_creator(client_name, client_domain)
        
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

        # Import CrewAI components when needed
        from crewai import Task, Crew, Process

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

def generate_complete_email_dossier(analysis_payload: dict, include_client: bool = False, client_context: str = ""):
    """
    Generate a complete email dossier with components:
    1. Meeting Flow (from analysis)
    2. Client Dossier (from context) - optional
    
    Returns: { 
        "meeting_flow": str, 
        "client_dossier": str (if included),
        "product_name": str, 
        "product_domain": str 
    }
    """
    result = {}
    
    # Always generate meeting flow
    meeting_result = generate_meeting_flow_dossier(analysis_payload)
    result.update(meeting_result)
    
    # Extract product info for meeting flow context
    product_name = meeting_result.get("product_name", "Unknown Product")
    product_domain = meeting_result.get("product_domain", "general product")
    
    # Optionally generate client dossier
    if include_client:
        try:
            # Extract client name from the analysis payload
            extracted_client_name = ""
            if isinstance(analysis_payload, dict):
                # Try to get from structured analysis first
                structured = analysis_payload.get("structured_analysis")
                if structured and isinstance(structured, dict):
                    extracted_client_name = structured.get("client_name", "")
                
                # If not found, try to extract from raw analysis text
                if not extracted_client_name or extracted_client_name.lower() in ["unknown client", "unknown"]:
                    raw_analysis = analysis_payload.get("analysis", "")
                    if raw_analysis:
                        # Try to extract client name from the raw text
                        import re
                        client_match = re.search(r"Client Name:\s*\**(.+?)\**\s*$", str(raw_analysis), re.MULTILINE | re.IGNORECASE)
                        if client_match:
                            # Clean up the extracted client name
                            raw_name = client_match.group(1).strip()
                            # Remove parenthetical explanations
                            cleaned_name = re.sub(r'\s*\([^)]*\)', '', raw_name)
                            # Remove explanatory prefixes
                            cleaned_name = re.sub(r'^\s*(likely|probably|appears to be|seems to be)\s+', '', cleaned_name, flags=re.IGNORECASE)
                            # Remove explanatory suffixes after semicolons
                            cleaned_name = re.sub(r'\s*(organization|company|corp|inc|ltd)?\s*;\s*.*$', '', cleaned_name, flags=re.IGNORECASE)
                            # Clean up whitespace
                            extracted_client_name = ' '.join(cleaned_name.split()).strip()
            
            # Only generate client dossier if we have a valid client name
            if extracted_client_name and extracted_client_name.lower() not in ["unknown client", "unknown", ""]:
                client_result = generate_client_dossier(extracted_client_name, "", client_context)
                result.update(client_result)
            else:
                result["client_dossier_error"] = "No valid client name found in analysis. Client dossier generation skipped."
        except Exception as e:
            result["client_dossier"] = f"Error generating client dossier: {e}"
    
    return result
    
# --- Authentication Routes ---
@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """Initiate Google OAuth login flow."""
    try:
        # Clear any existing session data
        session.clear()
        
        # Generate authorization URL
        auth_url = initiate_oauth_flow()
        
        return jsonify({
            'auth_url': auth_url,
            'message': 'Redirect to this URL to begin authentication'
        })
    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({'error': f'Failed to initiate login: {str(e)}'}), 500

@app.route("/api/auth/callback")
def api_auth_callback():
    """Handle OAuth callback from Google."""
    try:
        print(f"[Callback Route] Received callback request")
        print(f"[Callback Route] Request URL: {request.url}")
        print(f"[Callback Route] Request args: {dict(request.args)}")
        print(f"[Callback Route] Session ID: {session.get('_id', 'No session ID')}")
        print(f"[Callback Route] Session keys before callback: {list(session.keys())}")
        
        # Get the full callback URL
        authorization_response_url = request.url
        
        # Handle the OAuth callback
        success = handle_oauth_callback(authorization_response_url)
        
        print(f"[Callback Route] OAuth callback success: {success}")
        print(f"[Callback Route] Session keys after callback: {list(session.keys())}")
        
        if success:
            # Redirect to frontend with success
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            redirect_url = f"{frontend_url}?auth=success"
            print(f"[Callback Route] Redirecting to: {redirect_url}")
            return redirect(redirect_url)
        else:
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}?auth=error")
            
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        import traceback
        traceback.print_exc()
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}?auth=error&message={str(e)}")

@app.route("/api/auth/status", methods=["GET"])
def api_auth_status():
    """Check current authentication status."""
    try:
        if is_authenticated() and validate_session():
            user_profile = get_current_user()
            session_info = get_session_info()
            return jsonify({
                'authenticated': True,
                'user': user_profile,
                'session': session_info
            })
        else:
            return jsonify({'authenticated': False})
    except Exception as e:
        print(f"Error checking auth status: {e}")
        return jsonify({'authenticated': False, 'error': str(e)})

@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    """Logout user and clear session."""
    try:
        success = logout()
        return jsonify({
            'success': success,
            'message': 'Logged out successfully' if success else 'Logout completed with warnings'
        })
    except Exception as e:
        print(f"Error in logout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/auth/profile", methods=["GET"])
@require_auth
def api_auth_profile():
    """Get current user profile (protected route)."""
    try:
        user_profile = get_current_user()
        return jsonify(user_profile)
    except Exception as e:
        print(f"Error getting profile: {e}")
        return jsonify({'error': str(e)}), 500

# --- API Routes ---
@app.route("/api/find_threads", methods=["POST"])
@require_auth
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
@require_auth
def api_analyze_thread():
    try:
        print(f"[analyze_thread] Request received at {request.url}")
        data = request.get_json()
        print(f"[analyze_thread] Request data: {data}")
        
        thread_id = data.get('thread_id') if data else None
        
        if not thread_id:
            print("[analyze_thread] Missing thread_id in request")
            return jsonify({'error': 'thread_id is required'}), 400
            
        print(f"[analyze_thread] Processing thread_id: {thread_id}")
        
        try:
            ensure_gmail_service()
            print("[analyze_thread] Gmail service verified")
        except Exception as ge:
            print(f"[analyze_thread] Gmail service error: {ge}")
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
            
        print("[analyze_thread] Starting thread analysis...")
        result = analyze_thread_content(thread_id)
        print(f"[analyze_thread] Analysis completed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"[analyze_thread] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/api/process_threads_metadata", methods=["POST"])
@require_auth
def api_process_threads_metadata():
    """Extract metadata from threads without AI analysis"""
    try:
        data = request.get_json()
        thread_ids = data.get('thread_ids', [])
        
        if not thread_ids:
            return jsonify({'error': 'thread_ids array is required'}), 400
        
        try:
            ensure_gmail_service()
        except Exception as ge:
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
        
        result = process_threads_metadata_only(thread_ids)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/analyze_multiple_threads", methods=["POST"])
@require_auth
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
@require_auth
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





@app.route("/api/generate_client_dossier", methods=["POST"])
@require_auth
def api_generate_client_dossier():
    """Generate only the client dossier"""
    try:
        data = request.get_json()
        client_name = data.get('client_name', '')
        client_domain = data.get('client_domain', '')
        client_context = data.get('client_context', '')
        
        result = generate_client_dossier(client_name, client_domain, client_context)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/test_domain_client_extraction", methods=["POST"])
def api_test_domain_client_extraction():
    """Test the domain-based client name extraction with a sample thread"""
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return jsonify({'error': 'thread_id is required'}), 400
        
        service = ensure_gmail_service()
        messages = get_email_thread(service, thread_id)
        
        # Test the domain extraction
        domain_client_names = extract_client_name_from_domains(messages, service)
        
        # Get Gmail user info for context
        gmail_user_email = None
        try:
            from gmail_utils import get_gmail_user_profile
            profile = get_gmail_user_profile(service)
            if profile:
                gmail_user_email = profile.get("emailAddress", "")
        except Exception as e:
            print(f"Error getting Gmail user profile: {e}")
        
        return jsonify({
            'thread_id': thread_id,
            'gmail_user_email': gmail_user_email,
            'domain_based_client_names': domain_client_names,
            'message_count': len(messages) if messages else 0,
            'first_two_emails_processed': min(2, len(messages) if messages else 0)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/validate_client_name", methods=["POST"])
def api_validate_client_name():
    """Validate if a client name is suitable for dossier generation"""
    try:
        data = request.get_json()
        analysis_payload = data.get('analysis')
        
        if not analysis_payload:
            return jsonify({'valid': False, 'client_name': '', 'reason': 'No analysis payload provided'})
        
        # Extract client name from analysis (same logic as in generate_complete_email_dossier)
        extracted_client_name = ""
        if isinstance(analysis_payload, dict):
            # Try to get from structured analysis first
            structured = analysis_payload.get("structured_analysis")
            if structured and isinstance(structured, dict):
                extracted_client_name = structured.get("client_name", "")
            
            # If not found, try to extract from raw analysis text
            if not extracted_client_name or extracted_client_name.lower() in ["unknown client", "unknown"]:
                raw_analysis = analysis_payload.get("analysis", "")
                if raw_analysis:
                    import re
                    client_match = re.search(r"Client Name:\s*\**(.+?)\**\s*$", str(raw_analysis), re.MULTILINE | re.IGNORECASE)
                    if client_match:
                        # Clean up the extracted client name
                        raw_name = client_match.group(1).strip()
                        # Remove parenthetical explanations
                        cleaned_name = re.sub(r'\s*\([^)]*\)', '', raw_name)
                        # Remove explanatory prefixes
                        cleaned_name = re.sub(r'^\s*(likely|probably|appears to be|seems to be)\s+', '', cleaned_name, flags=re.IGNORECASE)
                        # Remove explanatory suffixes after semicolons
                        cleaned_name = re.sub(r'\s*(organization|company|corp|inc|ltd)?\s*;\s*.*$', '', cleaned_name, flags=re.IGNORECASE)
                        # Clean up whitespace
                        extracted_client_name = ' '.join(cleaned_name.split()).strip()
        
        # Validate the client name
        is_valid = (extracted_client_name and 
                   extracted_client_name.lower() not in ["unknown client", "unknown", ""])
        
        reason = ""
        if not is_valid:
            if not extracted_client_name:
                reason = "No client name found in analysis"
            elif extracted_client_name.lower() in ["unknown client", "unknown"]:
                reason = "Client name is marked as unknown"
            else:
                reason = "Client name is empty or invalid"
        
        return jsonify({
            'valid': is_valid,
            'client_name': extracted_client_name,
            'reason': reason if not is_valid else 'Valid client name found'
        })
        
    except Exception as e:
        return jsonify({'valid': False, 'client_name': '', 'reason': f'Error validating client name: {str(e)}'}), 500


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
            

            
        elif dossier_type == 'client':
            client_name = data.get('client_name', '')
            client_domain = data.get('client_domain', '')
            client_context = data.get('client_context', '')
            result = generate_client_dossier(client_name, client_domain, client_context)
            
        else:  # 'complete' or default
            analysis_payload = data.get('analysis')
            if not analysis_payload:
                return jsonify({'error': 'analysis payload is required for complete dossier'}), 400
            
            include_client = data.get('include_client', False)
            client_context = data.get('client_context', '')
            
            result = generate_complete_email_dossier(
                analysis_payload, 
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

@app.route("/api/test_participant_extraction", methods=["POST"])
def test_participant_extraction():
    """Test endpoint to verify participant extraction is working correctly"""
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return jsonify({'error': 'thread_id is required'}), 400
        
        try:
            ensure_gmail_service()
        except Exception as ge:
            return jsonify({'error': str(ge), 'code': 'GMAIL_NOT_CONFIGURED'}), 400
        
        service = ensure_gmail_service()
        messages = get_email_thread(service, thread_id)
        
        # Test participant extraction
        participants = extract_all_participants_from_emails(messages, service)
        
        # Get Gmail user profile
        from gmail_utils import get_gmail_user_profile
        gmail_profile = get_gmail_user_profile(service)
        
        # Enhanced debugging information
        debug_info = {
            'thread_id': thread_id,
            'message_count': len(messages),
            'participants': participants,
            'gmail_user_profile': gmail_profile,
            'participant_count': len(participants),
            'debug_details': {}
        }
        
        # Add detailed debugging for first few messages
        if messages:
            debug_info['debug_details']['first_message_headers'] = []
            first_message = messages[0]
            headers = first_message.get("payload", {}).get("headers", [])
            for header in headers:
                debug_info['debug_details']['first_message_headers'].append({
                    'name': header.get('name'),
                    'value': header.get('value', '')[:200] + '...' if len(header.get('value', '')) > 200 else header.get('value', '')
                })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

def extract_client_name_from_domains(messages, gmail_service=None):
    """
    Extract client names from email domains in the first 2 emails of a thread.
    Only considers FROM and TO addresses (ignores CC/BCC).
    Filters out the Gmail user's domain and returns all remaining domains as client names.
    
    Args:
        messages: List of email message dictionaries
        gmail_service: Gmail service object to get user profile
    
    Returns:
        list: List of client names derived from domains, or ["Unknown Client"] if no valid domain found
    """
    if not messages or len(messages) == 0:
        return ["Unknown Client"]
    
    # Get Gmail user's email to identify their domain
    gmail_user_domain = None
    if gmail_service:
        try:
            from gmail_utils import get_gmail_user_profile
            profile = get_gmail_user_profile(gmail_service)
            if profile:
                gmail_user_email = profile.get("emailAddress", "").lower()
                if gmail_user_email and "@" in gmail_user_email:
                    gmail_user_domain = gmail_user_email.split("@")[1]
                    print(f"[extract_client_name_from_domains] Gmail user domain: {gmail_user_domain}")
        except Exception as e:
            print(f"[extract_client_name_from_domains] Error getting Gmail user profile: {e}")
    
    # Only process first 2 emails
    emails_to_process = messages[:2]
    print(f"[extract_client_name_from_domains] Processing first {len(emails_to_process)} emails")
    
    all_domains = set()
    
    for email_idx, email in enumerate(emails_to_process):
        headers = email.get("payload", {}).get("headers", [])
        
        # Only look at FROM and TO headers (ignore CC/BCC)
        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")
            
            if name in ["from", "to"] and value:
                # Split multiple addresses (comma-separated)
                addresses = [addr.strip() for addr in value.split(",")]
                
                for addr in addresses:
                    if "@" in addr:
                        # Extract email using regex
                        email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', addr)
                        if email_match:
                            email_addr = email_match.group(1) or email_match.group(2)
                            email_addr = email_addr.strip().lower()
                            
                            # Extract domain
                            if "@" in email_addr:
                                domain = email_addr.split("@")[1]
                                # Remove common TLDs like .com, .in, .org, etc.
                                domain_parts = domain.split(".")
                                if len(domain_parts) >= 2:
                                    # Take the main domain part (before the last dot)
                                    main_domain = ".".join(domain_parts[:-1])
                                    all_domains.add(main_domain)
                                    print(f"[extract_client_name_from_domains] Email {email_idx + 1} - Found domain: {main_domain} from {email_addr}")
    
    # Filter out Gmail user's domain
    if gmail_user_domain:
        gmail_main_domain = gmail_user_domain.split(".")[0] if "." in gmail_user_domain else gmail_user_domain
        all_domains.discard(gmail_main_domain)
        print(f"[extract_client_name_from_domains] Filtered out Gmail user domain: {gmail_main_domain}")
    
    print(f"[extract_client_name_from_domains] All domains found: {list(all_domains)}")
    
    # Convert all domains to client names
    client_names = []
    if all_domains:
        for domain in sorted(all_domains):  # Sort for consistent ordering
            client_name = convert_domain_to_client_name(domain)
            client_names.append(client_name)
            print(f"[extract_client_name_from_domains] Converted domain '{domain}' to client name: '{client_name}'")
    
    if not client_names:
        client_names = ["Unknown Client"]
    
    print(f"[extract_client_name_from_domains] Returning client names: {client_names}")
    return client_names

def convert_domain_to_client_name(domain):
    """
    Convert a domain name to a proper client name.
    Examples:
    - 'techifysolutions' -> 'Techify Solutions'
    - 'thehalalshack' -> 'The Halal Shack'
    - 'abc-corp' -> 'ABC Corp'
    """
    if not domain:
        return "Unknown Client"
    
    # Handle common patterns
    domain_lower = domain.lower()
    
    # Remove common prefixes/suffixes
    domain_clean = domain_lower
    for prefix in ['www.', 'mail.', 'smtp.', 'pop.', 'imap.']:
        if domain_clean.startswith(prefix):
            domain_clean = domain_clean[len(prefix):]
    
    # Split by common separators and capitalize
    parts = re.split(r'[-_.]', domain_clean)
    
    # Handle special cases
    if len(parts) == 1:
        # Single word domain
        word = parts[0]
        if word.startswith('the'):
            # Handle "the" prefix
            rest = word[3:]
            if rest:
                return f"The {rest.title()}"
            else:
                return "The"
        else:
            return word.title()
    else:
        # Multiple parts
        result_parts = []
        for part in parts:
            if part:
                # Handle "the" as first part
                if part == 'the' and not result_parts:
                    result_parts.append('The')
                else:
                    result_parts.append(part.title())
        
        return ' '.join(result_parts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
