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
            L.login(username, password)
            L.save_session_to_file()
            return True
        except Exception as e:
            raise AuthenticationError(f"Instaloader legacy login failed: {e}")
            
    @staticmethod
    def get_session_file(username: str) -> Optional[str]:
        """Finds the Instaloader session file for the user."""
        candidates = [
            f"session-{username}",
            os.path.join(settings.SESSION_DIR, f"session-{username}")
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
                # Instaloader saves the requests URL lib cookie jar via pickle
                # Let's cleanly reverse engineer it without importing instaloader runtime
                import sys
                
                # Create dummy classes so pickle doesn't crash if instaloader is missing
                class DummyContext: pass
                sys.modules['instaloader.instaloadercontext'] = type('instaloadercontext', (), {
                    'InstaloaderContext': DummyContext
                })
                
                # Unpack the tuple. Instaloader saves: (version, user_agent, cookiejar, other_flags)
                data = pickle.load(f)
                cookie_jar = data[2] # requests.cookies.RequestsCookieJar
                
                # Convert into Playwright format
                playwright_cookies = []
                for cookie in cookie_jar:
                    playwright_cookies.append({
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": cookie.path,
                        "secure": cookie.secure
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
