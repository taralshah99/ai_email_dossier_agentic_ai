import os
from google.oauth2.credentials import Credentials  #type:ignore
from google_auth_oauthlib.flow import InstalledAppFlow #type:ignore
from google.auth.transport.requests import Request #type:ignore
from googleapiclient.discovery import build #type:ignore

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service( ):
    creds = None
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, "token.json")
    credentials_path = os.path.join(script_dir, "credentials.json")
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service

def list_email_threads(service, query: str = "", max_results: int = 100, include_spam_trash: bool = False):
    """Lists all threads matching the query.

    include_spam_trash: when True, include Spam and Trash in the results (matches Gmail's in:anywhere).
    """
    threads = []
    page_token = None
    while True:
        results = service.users().threads().list(
            userId="me",
            q=query,
            includeSpamTrash=include_spam_trash,
            pageToken=page_token,
            maxResults=max_results,
        ).execute()
        threads.extend(results.get("threads", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return threads

def get_email_thread(service, thread_id):
    """Gets the full content of a thread with all headers."""
    try:
        # Get the full thread with all message data
        thread = service.users().threads().get(userId="me", id=thread_id, format='full').execute()
        messages = thread.get("messages", [])
        
        # For each message, ensure we have all headers by making an additional call if needed
        enhanced_messages = []
        for message in messages:
            message_id = message.get("id")
            if message_id:
                # Get individual message with full headers
                full_message = service.users().messages().get(userId="me", id=message_id, format='full').execute()
                enhanced_messages.append(full_message)
            else:
                enhanced_messages.append(message)
        
        return enhanced_messages
    except Exception as e:
        print(f"Error fetching thread {thread_id}: {e}")
        # Fallback to original method
        thread = service.users().threads().get(userId="me", id=thread_id, format='full').execute()
        messages = thread.get("messages", [])
        return messages

def get_thread_subject_and_sender(service, thread_id):
    """Gets the subject and sender from the first message of a thread."""
    try:
        thread = service.users().threads().get(userId="me", id=thread_id, format='metadata', metadataHeaders=['Subject', 'From']).execute()
        messages = thread.get('messages', [])
        if not messages:
            return None, None
        
        headers = messages[0].get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        return subject, sender
    except Exception as e:
        print(f"Error fetching metadata for thread {thread_id}: {e}")
        return None, None

def get_gmail_user_profile(service):
    """Gets the Gmail user's profile information including email address."""
    try:
        profile = service.users().getProfile(userId="me").execute()
        return profile
    except Exception as e:
        print(f"Error fetching Gmail user profile: {e}")
        return None

def extract_participants_from_messages(messages):
    """Extract all participants (sender, recipients, CC, BCC) from email messages."""
    participants = {
        'sender': set(),
        'recipients': set(),
        'cc': set(),
        'bcc': set()
    }
    
    for message in messages:
        headers = message.get('payload', {}).get('headers', [])
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'from':
                # Extract email from sender (handle "Name <email>" format)
                email = extract_email_from_string(value)
                if email:
                    participants['sender'].add(email)
            elif name == 'to':
                # Parse multiple recipients
                recipients = parse_email_addresses(value)
                participants['recipients'].update(recipients)
            elif name == 'cc':
                recipients = parse_email_addresses(value)
                participants['cc'].update(recipients)
            elif name == 'bcc':
                recipients = parse_email_addresses(value)
                participants['bcc'].update(recipients)
    
    # Convert sets to lists for JSON serialization
    return {
        'sender': list(participants['sender']),
        'recipients': list(participants['recipients']),
        'cc': list(participants['cc']),
        'bcc': list(participants['bcc'])
    }

def extract_email_from_string(email_string):
    """Extract a single email address from a string that may contain a name and email."""
    import re
    
    # Pattern to match "Name <email>" format
    name_email_pattern = r'<([^>]+)>'
    match = re.search(name_email_pattern, email_string)
    
    if match:
        # Extract email from <email> format
        return match.group(1).lower()
    else:
        # If no angle brackets, try to extract email directly
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, email_string)
        if match:
            return match.group(0).lower()
    
    return None

def parse_email_addresses(email_string):
    """Parse email addresses from a string that may contain multiple addresses."""
    import re
    
    # Common email patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Find all email addresses in the string
    emails = re.findall(email_pattern, email_string)
    
    # Clean up and return unique emails
    return set(email.lower() for email in emails if email)


