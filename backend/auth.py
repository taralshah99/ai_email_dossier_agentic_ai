"""
Authentication module for Gmail OAuth web flow and session management.
Handles login, logout, token refresh, and session cleanup.
"""

import os
import json
import requests
from flask import session, request, redirect, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Allow insecure transport for local development (MUST be set before importing OAuth libraries)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRETS_FILE = "web_credentials.json"  # or "credentials.json" if you renamed it

def get_google_oauth_flow():
    """Create and configure Google OAuth flow for web applications."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES
        )
        # Use the redirect URI from the credentials file
        # Only override if environment variable is explicitly set
        if os.getenv('OAUTH_REDIRECT_URI'):
            flow.redirect_uri = os.getenv('OAUTH_REDIRECT_URI')
        
        return flow
    except Exception as e:
        print(f"Error creating OAuth flow: {e}")
        raise

def initiate_oauth_flow():
    """Start the OAuth authorization flow."""
    try:
        print("[OAuth Init] Starting OAuth flow...")
        flow = get_google_oauth_flow()
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Enable refresh token
            include_granted_scopes='false',  # Don't include previously granted scopes
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        print(f"[OAuth Init] Generated state: {state[:20]}...")
        print(f"[OAuth Init] Authorization URL: {authorization_url[:100]}...")
        
        # Store state in session for security
        session['oauth_state'] = state
        session.permanent = True  # Make session persistent
        
        print(f"[OAuth Init] State stored in session. Session keys: {list(session.keys())}")
        
        return authorization_url
    except Exception as e:
        print(f"Error initiating OAuth flow: {e}")
        raise

def handle_oauth_callback(authorization_response_url):
    """Handle the OAuth callback and exchange code for tokens."""
    try:
        print(f"[OAuth Callback] Processing callback URL: {authorization_response_url}")
        print(f"[OAuth Callback] Session keys: {list(session.keys())}")
        print(f"[OAuth Callback] OAuth state in session: {'oauth_state' in session}")
        
        flow = get_google_oauth_flow()
        
        # Try to get state from session, but don't fail if missing
        # (Google's library will validate the state parameter from the URL)
        if 'oauth_state' in session:
            flow.state = session['oauth_state']
            print(f"[OAuth Callback] Using stored state: {session['oauth_state'][:20]}...")
        else:
            print("[OAuth Callback] No stored state found, letting Google handle validation")
        
        # Exchange authorization code for tokens
        print("[OAuth Callback] Fetching tokens...")
        flow.fetch_token(authorization_response=authorization_response_url)
        print("[OAuth Callback] Tokens received successfully")
        
        # Store credentials in session
        credentials = flow.credentials
        store_credentials_in_session(credentials)
        print("[OAuth Callback] Credentials stored in session")
        
        # Get user profile information
        user_profile = get_user_profile(credentials)
        if user_profile:
            session['user_profile'] = user_profile
            print(f"[OAuth Callback] User profile stored: {user_profile.get('email', 'unknown')}")
        
        # Clean up OAuth state
        session.pop('oauth_state', None)
        
        # Make session permanent to survive browser refresh
        session.permanent = True
        
        return True
    except Exception as e:
        print(f"Error handling OAuth callback: {e}")
        print(f"[OAuth Callback] Error type: {type(e).__name__}")
        # Clean up on error
        session.pop('oauth_state', None)
        raise

def store_credentials_in_session(credentials):
    """Store OAuth credentials in Flask session."""
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    session['authenticated'] = True

def load_credentials_from_session():
    """Load OAuth credentials from Flask session."""
    if 'credentials' not in session or not session.get('authenticated', False):
        return None
    
    try:
        creds_data = session['credentials']
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )
        
        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update session with new token
            store_credentials_in_session(credentials)
        
        return credentials
    except Exception as e:
        print(f"Error loading credentials from session: {e}")
        # Clear invalid credentials
        clear_session()
        return None

def get_user_profile(credentials):
    """Get Gmail user profile information."""
    try:
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        return {
            'email': profile.get('emailAddress', ''),
            'messages_total': profile.get('messagesTotal', 0),
            'threads_total': profile.get('threadsTotal', 0)
        }
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

def is_authenticated():
    """Check if user is currently authenticated."""
    return session.get('authenticated', False) and 'credentials' in session

def get_current_user():
    """Get current user profile from session."""
    return session.get('user_profile', {})

def revoke_credentials():
    """Revoke the OAuth tokens with Google."""
    try:
        credentials = load_credentials_from_session()
        if credentials and credentials.token:
            # Revoke token with Google
            revoke_url = 'https://oauth2.googleapis.com/revoke'
            requests.post(revoke_url, 
                         params={'token': credentials.token},
                         headers={'content-type': 'application/x-www-form-urlencoded'})
    except Exception as e:
        print(f"Error revoking credentials: {e}")
        # Continue with logout even if revocation fails

def clear_session():
    """Clear all authentication data from session."""
    keys_to_remove = [
        'credentials', 
        'authenticated', 
        'user_profile', 
        'oauth_state'
    ]
    for key in keys_to_remove:
        session.pop(key, None)

def logout():
    """Complete logout process - revoke tokens and clear session."""
    try:
        # Revoke tokens with Google
        revoke_credentials()
        
        # Clear session data
        clear_session()
        
        return True
    except Exception as e:
        print(f"Error during logout: {e}")
        # Clear session even if revocation fails
        clear_session()
        return False

def require_auth(f):
    """Decorator to require authentication for routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated_function

def get_gmail_service():
    """Get authenticated Gmail service instance."""
    credentials = load_credentials_from_session()
    if not credentials:
        raise Exception("No valid credentials available")
    
    return build('gmail', 'v1', credentials=credentials)