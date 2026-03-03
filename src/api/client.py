import json
import urllib.parse
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
from src.core.config import settings
from src.core.exceptions import NetworkError, AuthenticationError, RateLimitError, UserNotFoundError
from src.core.cache import global_cache
from src.api.endpoints import Endpoints
from src.api.auth import SessionManager

class InstagramClient:
    """Core network client for Instagram API using Playwright for evasion."""
    
    def __init__(self, username: Optional[str] = None):
        self._playwright = sync_playwright().start()
        
        # Memory & Speed Optimization: Stripped down headless Chromium
        self.browser = self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--mute-audio"
            ]
        )
        self.context = self.browser.new_context(
            user_agent=settings.USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            color_scheme="dark",
            locale="en-US",
            timezone_id="America/New_York",
        )
        
        self.page = self.context.new_page()
        
        # Memory & Speed Optimization: Intercept and block heavy visual assets
        def block_heavy_assets(route):
            if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                route.abort()
            else:
                route.continue_()
        self.page.route("**/*", block_heavy_assets)
        
        Stealth().apply_stealth_sync(self.page)
        self.page.goto("https://www.instagram.com/", wait_until="commit")
        
        self.username = username
        self.is_authenticated = False
        
        if username:
            try:
                cookies = SessionManager.load_cookies(username)
                self.context.add_cookies(cookies)
                
                # Fetch CSRF token for GraphQL requests
                has_session = any(c['name'] == 'sessionid' for c in cookies)
                if has_session:
                    self.is_authenticated = True
                    
            except AuthenticationError:
                pass # Proceed as unauthenticated
                
    def __del__(self):
        """Cleanup playwright resources."""
        if hasattr(self, 'browser') and self.browser:
            self.browser.close()
        if hasattr(self, '_playwright') and self._playwright:
            self._playwright.stop()
            
    def _request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, omit_cookies: bool = False) -> Dict[str, Any]:
        """Internal robust request handler using Playwright fetch evaluation."""
        for attempt in range(settings.MAX_RETRIES):
            try:
                fetch_options = {
                    "method": method,
                    "headers": headers or {}
                }
                if omit_cookies:
                    fetch_options["credentials"] = "omit"
                
                fetch_script = """
                async ([url, options]) => {
                    const response = await fetch(url, options);
                    const status = response.status;
                    let data = null;
                    let text = await response.text();
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        data = text;
                    }
                    return { status: status, data: data };
                }
                """
                
                result = self.page.evaluate(fetch_script, [url, fetch_options])
                
                status_code = result.get('status')
                data = result.get('data')
                
                if status_code == 429:
                    raise RateLimitError("Instagram rate limit (429) hit.")
                if status_code == 404:
                    raise UserNotFoundError(f"Endpoint or resource not found at {url}")
                if status_code in {401, 403}:
                    raise AuthenticationError("Session invalid or blocked (401/403).")
                    
                if status_code and status_code >= 400:
                    raise NetworkError(f"HTTP {status_code}: {data}")
                    
                if isinstance(data, str):
                    try:
                        return json.loads(data)
                    except ValueError:
                        raise NetworkError(f"Failed to decode JSON from response: {data[:100]}...")
                return data
                
            except PlaywrightTimeoutError:
                raise NetworkError("Request timed out.")
            except (NetworkError, RateLimitError) as e:
                import time
                from src.modules.evasion import poisson_jitter
                
                if attempt < settings.MAX_RETRIES - 1:
                    sleep_time = poisson_jitter(settings.JITTER_MEAN_FAST) * (attempt + 1)
                    time.sleep(sleep_time)
                else:
                    raise NetworkError(f"Request failed after {settings.MAX_RETRIES} attempts: {e}")
                    
    def get_json(self, url: str) -> Dict[str, Any]:
        """Fetch and parse JSON from Instagram APIs."""
        return self._request("GET", url)

    def fetch_user_info(self, target: str) -> Dict[str, Any]:
        """Fetch raw web profile info for a target using stable Instaloader engine if authenticated."""
        if self.is_authenticated and self.username:
            try:
                import instaloader
                L = instaloader.Instaloader(dirname_pattern=settings.SESSION_DIR, quiet=True)
                L.load_session_from_file(self.username, filename=SessionManager.get_session_file(self.username))
                profile = instaloader.Profile.from_username(L.context, target)
                
                user_dict = {
                    "id": str(profile.userid),
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "biography": profile.biography,
                    "edge_followed_by": {"count": profile.followers},
                    "edge_follow": {"count": profile.followees},
                    "is_private": profile.is_private,
                    "is_verified": profile.is_verified,
                    "business_email": profile.business_email,
                    "business_phone_number": profile.business_phone_number,
                    "profile_pic_url_hd": profile.profile_pic_url
                }
                
                # Map Recent Posts for advanced OSINT modules (SNA, Stylometry, Audit, Locations)
                try:
                    import itertools
                    edges = []
                    for post in itertools.islice(profile.get_posts(), 12):
                        node = {
                            "id": str(post.mediaid),
                            "shortcode": post.shortcode,
                            "owner": {"id": str(profile.userid)},
                            "taken_at_timestamp": int(post.date_utc.timestamp()),
                            "edge_media_preview_like": {"count": post.likes},
                            "edge_media_to_comment": {"count": post.comments},
                            "is_video": post.is_video,
                            "video_view_count": getattr(post, 'video_view_count', 0),
                        }
                        if post.caption:
                            node["edge_media_to_caption"] = {"edges": [{"node": {"text": post.caption}}]}
                        if getattr(post, 'location', None):
                            node["location"] = {
                                "name": post.location.name,
                                "lat": getattr(post.location, 'lat', None),
                                "lng": getattr(post.location, 'lng', None),
                            }
                        if post.tagged_users:
                            node["edge_media_to_tagged_user"] = {
                                "edges": [{"node": {"user": {"username": tu}}} for tu in post.tagged_users]
                            }
                        edges.append({"node": node})
                    user_dict["edge_owner_to_timeline_media"] = {"edges": edges}
                except Exception:
                    # Ignore private profiles or rate limits on post fetching
                    user_dict["edge_owner_to_timeline_media"] = {"edges": []}
                    
                return user_dict
            except Exception as e:
                pass # Fallback to standard request

        # Fallback to standard web endpoint, unauthenticated for shadowban evasion
        url = Endpoints.user_info(target)
        
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        data = self._request("GET", url, headers=headers, omit_cookies=True)
        if "data" in data and "user" in data["data"]:
            return data["data"]["user"]
        return data

    def fetch_graphql(self, query_hash: str, variables: dict) -> Dict[str, Any]:
        """Fetch data from GraphQL endpoint."""
        var_str = urllib.parse.quote(json.dumps(variables))
        url = f"{Endpoints.GRAPHQL_URL}?query_hash={query_hash}&variables={var_str}"
        
        headers = {}
        if self.is_authenticated:
            # We need CSRF token from cookies 
            cookies = self.context.cookies()
            csrf = next((c['value'] for c in cookies if c['name'] == 'csrftoken'), None)
            if csrf:
                headers = {
                    "X-CSRFToken": csrf,
                    "X-IG-App-ID": "936619743392459"
                }
                
        return self._request("GET", url, headers=headers)

    def initiate_password_reset(self, target: str) -> Dict[str, Any]:
        """Trigger the Instagram password reset flow to enumerate masked contacts."""
        # Use web API which respects standard browser auth and CSRF
        url = "https://www.instagram.com/api/v1/users/lookup/"
        
        # Grab CSRF Token from cookies (Instagram sets one even for unauthenticated guests on first visit)
        cookies = self.context.cookies()
        csrf = next((c['value'] for c in cookies if c['name'] == 'csrftoken'), "missing_csrf")
        
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf,
            "X-IG-App-ID": "936619743392459",
            "X-Instagram-AJAX": "1",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Prepare the urlencoded body
        body = f"q={target}"
        
        fetch_options = {
            "method": "POST",
            "headers": headers,
            "body": body,
            "credentials": "include"
        }
        
        fetch_script = """
        async ([url, options]) => {
            const response = await fetch(url, options);
            const status = response.status;
            let data = null;
            let text = await response.text();
            try {
                data = JSON.parse(text);
            } catch (e) {
                data = text;
            }
            return { status: status, data: data };
        }
        """
        
        result = self.page.evaluate(fetch_script, [url, fetch_options])
        
        status_code = result.get('status')
        data = result.get('data', {})
        
        if status_code == 429:
            raise RateLimitError("Instagram rate limit (429) hit for password recovery endpoint.")
        if status_code and status_code >= 400:
            raise NetworkError(f"HTTP {status_code}: {data}")
            
        return data
