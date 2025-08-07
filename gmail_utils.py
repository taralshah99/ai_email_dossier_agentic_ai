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

def list_email_threads(service, query="", max_results=100):
    """Lists all threads matching the query."""
    threads = []
    page_token = None
    while True:
        results = service.users().threads().list(userId="me", q=query, includeSpamTrash=False, pageToken=page_token, maxResults=max_results).execute()
        threads.extend(results.get("threads", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return threads

def get_email_thread(service, thread_id):
    """Gets the full content of a thread."""
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


