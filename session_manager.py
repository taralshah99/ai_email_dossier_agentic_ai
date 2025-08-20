"""
Session management utilities for handling Flask sessions and cleanup.
Manages session lifecycle, cleanup on server restart, and session validation.
"""

import os
import shutil
import signal
import atexit
from datetime import datetime, timedelta
from flask import session
from auth import revoke_credentials, clear_session

# Global variable to track if cleanup is registered
_cleanup_registered = False

def setup_session_cleanup():
    """Register cleanup functions for server shutdown."""
    global _cleanup_registered
    
    if _cleanup_registered:
        return
    
    # Register cleanup for normal exit
    atexit.register(cleanup_all_sessions)
    
    # Register cleanup for Ctrl+C (SIGINT)
    def signal_handler(signum, frame):
        print("\nShutting down server...")
        cleanup_all_sessions()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Register cleanup for SIGTERM (if available on Windows)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except AttributeError:
        # SIGTERM not available on Windows
        pass
    
    _cleanup_registered = True
    print("Session cleanup handlers registered")

def cleanup_all_sessions():
    """Clean up all session data and revoke tokens on server shutdown."""
    try:
        print("Cleaning up sessions and revoking tokens...")
        
        # Try to revoke current session tokens if any
        try:
            if session and session.get('authenticated'):
                revoke_credentials()
        except Exception as e:
            print(f"Error revoking current session tokens: {e}")
        
        # Clear Flask session directory
        cleanup_session_files()
        
        print("Session cleanup completed")
    except Exception as e:
        print(f"Error during session cleanup: {e}")

def cleanup_session_files():
    """Remove Flask session files from filesystem."""
    try:
        # Default Flask-Session filesystem path
        session_dir = "flask_session"
        
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            print(f"Removed session directory: {session_dir}")
        
        # Also check for any other common session directories
        other_dirs = ["sessions", "tmp/sessions"]
        for dir_path in other_dirs:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"Removed session directory: {dir_path}")
                
    except Exception as e:
        print(f"Error removing session files: {e}")

def validate_session():
    """Validate current session and clean up if invalid."""
    try:
        if not session.get('authenticated', False):
            return False
        
        # Check if credentials exist and are valid
        if 'credentials' not in session:
            clear_session()
            return False
        
        # Check session age (optional - expire after 24 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=24):
                print("Session expired due to age")
                clear_session()
                return False
        
        return True
    except Exception as e:
        print(f"Error validating session: {e}")
        clear_session()
        return False

def create_session(user_profile):
    """Create a new authenticated session."""
    try:
        session['authenticated'] = True
        session['user_profile'] = user_profile
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True  # Make session survive browser restart
        print(f"Created session for user: {user_profile.get('email', 'unknown')}")
    except Exception as e:
        print(f"Error creating session: {e}")
        raise

def get_session_info():
    """Get information about current session."""
    if not session.get('authenticated', False):
        return None
    
    return {
        'authenticated': True,
        'user_email': session.get('user_profile', {}).get('email', ''),
        'login_time': session.get('login_time', ''),
        'has_credentials': 'credentials' in session
    }

def extend_session():
    """Extend session lifetime (called on user activity)."""
    if session.get('authenticated', False):
        session['last_activity'] = datetime.now().isoformat()
        session.permanent = True

def cleanup_expired_sessions():
    """Clean up expired sessions (can be called periodically)."""
    # This would be more relevant if we were storing sessions in a database
    # For filesystem sessions, Flask handles basic cleanup
    pass

def is_session_valid():
    """Quick check if current session is valid."""
    return (
        session.get('authenticated', False) and
        'credentials' in session and
        'user_profile' in session
    )
