import os
from google.oauth2.credentials import Credentials  #type:ignore
from google_auth_oauthlib.flow import InstalledAppFlow #type:ignore
from google.auth.transport.requests import Request #type:ignore
from googleapiclient.discovery import build #type:ignore

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service( ):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("gmail-chain-466910-3f7821500c47.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service

def list_email_threads(service, query=""):
    """Lists all threads matching the query."""
    results = service.users().threads().list(userId="me", q=query, includeSpamTrash=False).execute()
    threads = results.get("threads", [])
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
