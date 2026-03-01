import os
import sqlite3
import pickle
from typing import Dict, Any, Optional, List
from src.core.config import settings
from src.core.exceptions import AuthenticationError

class SessionManager:
    """Manages finding and loading Instagram sessions into Playwright."""
    
    @staticmethod
    def perform_login(username: str, password: str) -> bool:
        """Logs into Instagram cleanly using Instaloader to generate a fresh cookie session file."""
        import instaloader
        L = instaloader.Instaloader(dirname_pattern=settings.SESSION_DIR)
        try:
            os.makedirs(settings.SESSION_DIR, exist_ok=True)
            target_file = os.path.join(settings.SESSION_DIR, f"session-{username}")
            L.login(username, password)
            L.save_session_to_file(filename=target_file)
            return True
        except Exception as e:
            raise AuthenticationError(f"Instaloader legacy login failed: {e}")
            
    @staticmethod
    def get_session_file(username: str) -> Optional[str]:
        """Finds the Instaloader session file for the user."""
        candidates = [
            f"session-{username}",
            os.path.join(settings.SESSION_DIR, f"session-{username}"),
            os.path.expanduser(f"~/.config/instaloader/session-{username}")
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def load_cookies(username: str) -> List[Dict[str, Any]]:
        """Reads a legacy Instaloader session file and outputs a Playwright cookies list."""
        session_file = SessionManager.get_session_file(username)
        if not session_file:
            raise AuthenticationError(f"No saved session found for {username}.")
            
        try:
            with open(session_file, 'rb') as f:
                import sys
                
                # Create dummy classes so pickle doesn't crash if instaloader is missing
                class DummyContext: pass
                if 'instaloader.instaloadercontext' not in sys.modules:
                    sys.modules['instaloader.instaloadercontext'] = type('instaloadercontext', (), {
                        'InstaloaderContext': DummyContext
                    })
                
                # Instaloader saves a simple dict mapping cookie names to values
                data = pickle.load(f)
                
                if not isinstance(data, dict):
                    # In some older instaloader versions it might be a tuple.
                    # Handle fallback if necessary: tuple = (version, ua, cookiejar)
                    if isinstance(data, tuple) and len(data) >= 3:
                        cookie_jar = data[2]
                        playwright_cookies = []
                        for cookie in cookie_jar:
                            playwright_cookies.append({
                                "name": cookie.name,
                                "value": cookie.value,
                                "domain": cookie.domain,
                                "path": cookie.path
                            })
                        return playwright_cookies
                    raise ValueError(f"Unexpected session file structure: {type(data)}")
                
                # For modern instaloader standard dict:
                playwright_cookies = []
                for name, value in data.items():
                    playwright_cookies.append({
                        "name": name,
                        "value": str(value), # Ensure value is string
                        "domain": ".instagram.com", # Hardcoded domain requirements for playwright
                        "path": "/"
                    })
                    
                return playwright_cookies
                
        except Exception as e:
            raise AuthenticationError(f"Failed to parse session file: {e}")
            
    @staticmethod
    def delete_session(username: str):
        path = SessionManager.get_session_file(username)
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
