import instaloader
import time
import random
import numpy as np
from curl_cffi import requests as cffi_requests
from src.python.core.models import User, Post
from geopy.geocoders import Nominatim
from src.python.utils.cache import CacheManager

def poisson_jitter(mean_delay: float) -> float:
    """Generate human-like delay using Poisson distribution."""
    return np.random.poisson(mean_delay)

class InstagramScraper:
    def __init__(self, loader: instaloader.Instaloader):
        self.L = loader
        self.cache = CacheManager()
        self.geolocator = Nominatim(user_agent="ig_detective")
        # Task 1: TLS Fingerprint Spoofing
        # Impersonate a modern browser to bypass CDN rate-limiting
        old_session = self.L.context._session
        self.session = cffi_requests.Session(impersonate="chrome")
        
        # Transfer cookies from the original authenticated session
        for cookie in old_session.cookies:
            self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
            
        self.session.headers.update(old_session.headers)
        
        # Inject the spoofed session into instaloader
        self.L.context._session = self.session
        
        # Patch instaloader's copy_session to support curl_cffi's Session object
        import instaloader.instaloadercontext
        original_copy = instaloader.instaloadercontext.copy_session
        
        def patched_copy(session, timeout):
            if isinstance(session, cffi_requests.Session):
                new = cffi_requests.Session(impersonate="chrome")
                for k, v in session.cookies.items():
                    new.cookies.set(k, v)
                new.headers.update(session.headers)
                new.proxies = session.proxies.copy() if hasattr(session, 'proxies') else {}
                return new
            else:
                return original_copy(session, timeout)
                
        instaloader.instaloadercontext.copy_session = patched_copy
        
        # Patch curl_cffi Response to support requests API used by Instaloader
        if not hasattr(cffi_requests.Response, 'is_redirect'):
            @property
            def is_redirect(self):
                return self.status_code in {301, 302, 303, 307, 308}
            cffi_requests.Response.is_redirect = is_redirect
            
        if not hasattr(cffi_requests.Response, 'text'):
            @property
            def text(self):
                return self.content.decode('utf-8')
            cffi_requests.Response.text = text

    def _get_profile_instance(self, username: str) -> instaloader.Profile:
        """Helper to get and cache instaloader.Profile instance with retry logic."""
        cache_key = f"profile_obj_{username}"
        profile = self.cache.get(cache_key)
        if not profile:
            max_retries = 3
            base_delay = 5
            for attempt in range(max_retries):
                try:
                    profile = instaloader.Profile.from_username(self.L.context, username)
                    self.cache.set(cache_key, profile)
                    break
                except instaloader.exceptions.ConnectionException as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt) + poisson_jitter(2)
                        print(f"\n[!] Rate limited (429). Retrying in {sleep_time:.1f}s...")
                        time.sleep(sleep_time)
                    else:
                        raise e
        return profile

    def get_profile(self, username: str) -> User:
        """Fetch profile details for a given username using instaloader."""
        try:
            profile = self._get_profile_instance(username)
            return User(
                username=profile.username,
                full_name=profile.full_name,
                biography=profile.biography,
                follower_count=profile.followers,
                following_count=profile.followees,
                is_private=profile.is_private,
                is_verified=profile.is_verified,
                profile_pic_url=profile.profile_pic_url,
                external_url=profile.external_url,
                business_email=profile.business_email,
                business_phone=profile.business_phone_number,
                business_category=profile.business_category_name
            )
        except Exception as e:
            raise Exception(f"Failed to fetch profile: {e}")

    def get_posts(self, username: str, count: int = 10) -> list[Post]:
        """Fetch n recent posts using instaloader."""
        cache_key = f"posts_{username}_{count}"
        cached_posts = self.cache.get(cache_key)
        if cached_posts:
            return cached_posts

        try:
            profile = self._get_profile_instance(username)
            posts = []
            for post in profile.get_posts():
                posts.append(Post(
                    id=str(post.mediaid),
                    shortcode=post.shortcode,
                    caption=post.caption,
                    likes_count=post.likes,
                    comments_count=post.comments,
                    timestamp=post.date_utc,
                    owner_username=post.owner_username,
                    is_video=post.is_video,
                    video_view_count=post.video_view_count if post.is_video else None
                ))
                if len(posts) >= count:
                    break
            
            self.cache.set(cache_key, posts)
            return posts
        except Exception as e:
            raise Exception(f"Failed to fetch posts: {e}")

    def get_locations(self, username: str, limit: int = 50) -> list[dict]:
        """Extract locations from target posts with addresses."""
        try:
            profile = self._get_profile_instance(username)
            locations = []
            for post in profile.get_posts():
                if post.location:
                    loc_data = {
                        "name": post.location.name,
                        "lat": post.location.lat,
                        "lng": post.location.lng,
                        "timestamp": post.date_utc,
                        "address": None
                    }
                    
                    # Reverse geocode if coordinates available
                    if loc_data["lat"] and loc_data["lng"]:
                        try:
                            location = self.geolocator.reverse(f"{loc_data['lat']}, {loc_data['lng']}")
                            if location:
                                loc_data["address"] = location.address
                        except Exception:
                            pass
                    
                    locations.append(loc_data)
                
                if len(locations) >= limit:
                    break
            return locations
        except Exception as e:
            raise Exception(f"Failed to fetch locations: {e}")

    def get_tagged_users(self, username: str, post_limit: int = 20) -> list[str]:
        """Get list of users tagged in target's posts."""
        try:
            profile = self._get_profile_instance(username)
            tagged_users = set()
            count = 0
            for post in profile.get_posts():
                if post.tagged_users:
                    tagged_users.update(post.tagged_users)
                count += 1
                if count >= post_limit:
                    break
            return list(tagged_users)
        except Exception as e:
            raise Exception(f"Failed to fetch tagged users: {e}")

    def get_stories_urls(self, username: str) -> list[str]:
        """Fetch URLs for active stories."""
        try:
            profile = self._get_profile_instance(username)
            if not self.L.context.is_logged_in:
                 raise Exception("Login required to view stories.")
            
            story_urls = []
            for story in self.L.get_stories(userids=[profile.userid]):
                for item in story.get_items():
                    story_urls.append(item.video_url if item.is_video else item.url)
            return story_urls
        except Exception as e:
            raise Exception(f"Failed to fetch stories: {e}")

    def get_followers(self, username: str, limit: int = 50) -> list[User]:
        """Fetch list of followers."""
        cache_key = f"followers_{username}_{limit}"
        cached_followers = self.cache.get(cache_key)
        if cached_followers:
            return cached_followers

        try:
            profile = self._get_profile_instance(username)
            followers = []
            for follower in profile.get_followers():
                followers.append(User(
                    username=follower.username,
                    full_name=follower.full_name,
                    is_private=follower.is_private,
                    is_verified=follower.is_verified,
                    profile_pic_url=follower.profile_pic_url
                ))
                if len(followers) >= limit:
                    break
            
            self.cache.set(cache_key, followers)
            return followers
        except Exception as e:
            raise Exception(f"Failed to fetch followers: {e}")

    def get_followings(self, username: str, limit: int = 50) -> list[User]:
        """Fetch list of followings."""
        cache_key = f"followings_{username}_{limit}"
        cached_followings = self.cache.get(cache_key)
        if cached_followings:
            return cached_followings

        try:
            profile = self._get_profile_instance(username)
            followings = []
            for followee in profile.get_followees():
                followings.append(User(
                    username=followee.username,
                    full_name=followee.full_name,
                    is_private=followee.is_private,
                    is_verified=followee.is_verified,
                    profile_pic_url=followee.profile_pic_url
                ))
                if len(followings) >= limit:
                    break
            
            self.cache.set(cache_key, followings)
            return followings
        except Exception as e:
            raise Exception(f"Failed to fetch followings: {e}")

    def get_user_info(self, username: str) -> dict:
        """Fetch detailed raw user info."""
        cache_key = f"user_info_{username}"
        cached_info = self.cache.get(cache_key)
        if cached_info:
            return cached_info

        try:
            profile = self._get_profile_instance(username)
            # Check bio for emails or phone numbers
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', profile.biography)
            phone_match = re.search(
                r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                profile.biography
            )
            info = {
                "id": profile.userid,
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "email_from_bio": email_match.group(0) if email_match else None,
                "phone_from_bio": phone_match.group(0) if phone_match else None,
                "followers": profile.followers,
                "followees": profile.followees,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified,
                "external_url": profile.external_url,
                "profile_pic_url": profile.profile_pic_url,
                "business_category": profile.business_category_name,
                "is_business_account": profile.is_business_account,
            }
            self.cache.set(cache_key, info)
            return info
        except Exception as e:
            raise Exception(f"Failed to fetch user info: {e}")


    def get_user_comments(self, username: str, posts_limit: int = 10) -> list[dict]:
        """Fetch comments from recent posts."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            comments_list = []
            count = 0 
            for post in profile.get_posts():
                for comment in post.get_comments():
                    comments_list.append({
                        "id": comment.id,
                        "text": comment.text,
                        "owner_username": comment.owner.username,
                        "created_at_utc": comment.created_at_utc,
                        "post_id": post.mediaid
                    })
                count += 1
                if count >= posts_limit:
                    break
            return comments_list
        except Exception as e:
            raise Exception(f"Failed to fetch comments: {e}")
            
    def get_stories(self, username: str) -> list[dict]:
        """Fetch active stories."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            if not self.L.context.is_logged_in:
                 raise Exception("Login required to view stories.")
                 
            stories = []
            if profile.has_public_story:
                for story in self.L.get_stories(userids=[profile.userid]):
                    for item in story.get_items():
                         stories.append({
                             "id": item.mediaid,
                             "date_utc": item.date_utc,
                             "is_video": item.is_video,
                             "video_duration": item.video_duration,
                             "viewer_count": item.viewer_count if hasattr(item, 'viewer_count') else None, # Only for own stories usually
                             "url": item.video_url if item.is_video else item.url
                         })
            return stories
        except Exception as e:
             raise Exception(f"Failed to fetch stories: {e}")

    def scan_followers_for_contact(self, username: str, limit: int = 50, batch_size: int = 50):
        """Scan followers for email and phone numbers."""
        profile = instaloader.Profile.from_username(self.L.context, username)
        return self._scan_iterator(profile.get_followers(), limit, batch_size)

    def scan_followings_for_contact(self, username: str, limit: int = 50, batch_size: int = 50):
        """Scan followings for email and phone numbers."""
        profile = instaloader.Profile.from_username(self.L.context, username)
        return self._scan_iterator(profile.get_followees(), limit, batch_size)

    def _scan_iterator(self, profile_iter, limit: int, batch_size: int):
        """Helper to scan any profile iterator for contact info."""
        count = 0
        for profile_item in profile_iter:
            if count >= limit:
                break
            
            try:
                # We need to fetch full profile to get business emails
                full_profile = instaloader.Profile.from_username(self.L.context, profile_item.username)
                
                email = full_profile.business_email
                phone = full_profile.business_phone_number
                
                if email or phone:
                    contact_info = {
                        "username": full_profile.username,
                        "full_name": full_profile.full_name,
                        "email": email,
                        "phone": phone
                    }
                    yield contact_info
                
                count += 1
                
                # Task 1: Poisson Jitter (Human-like delay)
                sleep_time = poisson_jitter(10.0)
                time.sleep(max(5, sleep_time)) # Ensure at least 5s to be safe
                
                # Larger delay after a batch using Poisson distribution
                if count % batch_size == 0:
                    long_sleep = poisson_jitter(45.0)
                    print(f"[!] Batch {count} reached. High-latency jitter sleep for {long_sleep}s...")
                    time.sleep(max(20, long_sleep))
                    
            except instaloader.ConnectionException as e:
                print(f"[!] Connection error (likely rate limited): {e}")
                break
            except instaloader.QueryReturnedNotFoundException:
                continue
            except Exception as e:
                print(f"[!] Error processing {profile_item.username}: {e}")
                continue

    def get_recovery_info(self, username: str) -> dict:
        """
        Research-Driven OSINT: Account Recovery Enumeration.
        Triggers the password reset flow to get masked contact info.
        """
        try:
            # We use the spoofed session to hit the recovery endpoint
            url = "https://www.instagram.com/api/v1/accounts/send_password_reset/"
            headers = {
                "X-CSRFToken": self.L.context._session.cookies.get("csrftoken", ""),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.instagram.com/accounts/password/reset/"
            }
            
            data = {"email_or_username": username}
            response = self.session.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                resp_json = response.json()
                return {
                    "username": username,
                    "status": resp_json.get("status"),
                    "message": resp_json.get("message"), # e.g. "We sent an email to s***h@g***.com"
                    "body": resp_json.get("body"), # Often contains the actual tip
                    "contact_point": resp_json.get("contact_point") # Sometimes present
                }
            else:
                return {"error": f"Failed to trigger recovery. Status: {response.status_code}", "raw": response.text}
                
        except Exception as e:
            raise Exception(f"Recovery enumeration failed: {e}")
