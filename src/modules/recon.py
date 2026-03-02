import re
import datetime
from typing import List, Optional
from src.api.client import InstagramClient
from src.core.models import User, Post, Comment
from src.core.cache import global_cache
from src.modules.evasion import apply_jitter

class ReconEngine:
    """Intelligently maps raw Instagram API JSON into strict Dataclass OSINT models."""
    
    # Pre-compiled Regex Patterns for speed
    _EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    _PHONE_REGEX = re.compile(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')

    def __init__(self, api_client: InstagramClient):
        self.api = api_client
        # Lazy load geolocator to speed up boot
        self._geolocator = None
        
    @property
    def geolocator(self):
        if not self._geolocator:
            from geopy.geocoders import Nominatim
            self._geolocator = Nominatim(user_agent="ig_detective")
        return self._geolocator

    def get_user_profile(self, username: str) -> User:
        """Extract profile information including hidden business emails in bio."""
        cache_key = f"recon_user_{username}"
        cached = global_cache.get(cache_key)
        if cached: return cached
        
        apply_jitter("fast")
        data = self.api.fetch_user_info(username)
        
        bio = data.get('biography', '')
        # OSINT: Extract potential emails/phones hidden in the bio string using pre-compiled regex
        email_match = self._EMAIL_REGEX.search(bio)
        phone_match = self._PHONE_REGEX.search(bio)
        
        user = User(
            id=str(data.get('id', '')),
            username=data.get('username', username),
            full_name=data.get('full_name', ''),
            biography=bio,
            follower_count=data.get('edge_followed_by', {}).get('count', 0),
            following_count=data.get('edge_follow', {}).get('count', 0),
            is_private=data.get('is_private', False),
            is_verified=data.get('is_verified', False),
            profile_pic_url=data.get('profile_pic_url_hd'),
            external_url=data.get('external_url'),
            business_category=data.get('business_category_name'),
            business_email=data.get('business_email') or (email_match.group(0) if email_match else None),
            business_phone=data.get('business_phone_number') or (phone_match.group(0) if phone_match else None),
            obfuscated_email=data.get('obfuscated_email'),
            obfuscated_phone=data.get('obfuscated_phone')
        )
        
        global_cache.set(cache_key, user)
        return user

    def get_recent_posts(self, username: str, count: int = 12) -> List[Post]:
        """Fetch the user's latest posts and extract OSINT metadata."""
        cache_key = f"recon_posts_{username}_{count}"
        cached = global_cache.get(cache_key)
        if cached: return cached
        
        apply_jitter("normal")
        # For OSINT efficiency, the first ~12 posts are embedded fully in the target's profile JSON.
        data = self.api.fetch_user_info(username)
        timeline = data.get('edge_owner_to_timeline_media', {})
        edges = timeline.get('edges', [])
        
        # In a fully-scaled GraphQL paginator we would use the end_cursor.
        # Here we slice up to the requested count provided by the initial payload.
        posts = self._parse_timeline_edges(edges[:count])
        
        global_cache.set(cache_key, posts)
        return posts

    def _parse_timeline_edges(self, edges: list) -> List[Post]:
        posts = []
        for edge in edges:
            node = edge['node']
            
            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
            caption = caption_edges[0]['node']['text'] if caption_edges else ""
            
            timestamp = datetime.datetime.fromtimestamp(node.get('taken_at_timestamp', 0), tz=datetime.timezone.utc)
            
            # Location Extraction (OSINT)
            loc = node.get('location')
            loc_name, lat, lng = None, None, None
            if loc:
                loc_name = loc.get('name')
                # Wait for graphql location detail logic if lat/lng are missing (Instagram often strips GPS from timeline nodes) 
                lat, lng = loc.get('lat'), loc.get('lng')
            
            # Tagged Users
            tagged = []
            tagged_edges = node.get('edge_media_to_tagged_user', {}).get('edges', [])
            for t_edge in tagged_edges:
                tagged.append(t_edge['node']['user']['username'])
                
            p = Post(
                id=str(node.get('id')),
                shortcode=node.get('shortcode'),
                owner_id=str(node.get('owner', {}).get('id')),
                timestamp=timestamp,
                caption=caption,
                likes_count=node.get('edge_media_preview_like', {}).get('count', 0),
                comments_count=node.get('edge_media_to_comment', {}).get('count', 0),
                is_video=node.get('is_video', False),
                video_view_count=node.get('video_view_count'),
                location_name=loc_name,
                location_lat=lat,
                location_lng=lng,
                tagged_users=tagged,
                raw_node=node # Keep for future advanced extraction
            )
            posts.append(p)
        return posts
        
    def get_locations(self, username: str, limit: int = 50) -> List[dict]:
        """High level OSINT: Extract mapped locations."""
        posts = self.get_recent_posts(username, count=limit)
        locations = []
        for p in posts:
            if p.location_name:
                loc_info = {
                    "name": p.location_name,
                    "lat": p.location_lat,
                    "lng": p.location_lng,
                    "timestamp": p.timestamp,
                    "address": None
                }
                if p.location_lat and p.location_lng:
                    try:
                        time.sleep(1) # Be nice to geopy
                        loc = self.geolocator.reverse(f"{p.location_lat}, {p.location_lng}")
                        if loc: loc_info["address"] = loc.address
                    except Exception:
                        pass
                locations.append(loc_info)
        return locations

    def trigger_recovery_flow(self, username: str) -> dict:
        """Trigger password reset to extract masked contacts (Section 10.1)."""
        apply_jitter("fast")
        data = self.api.initiate_password_reset(username)
        
        # Parse the JSON response for the hidden contact info
        result = {
            "has_recovery": False,
            "emails": [],
            "phones": []
        }
        
        if data and data.get("user"):
            user_data = data["user"]
            result["has_recovery"] = True
            
            # Instagram sometimes returns multiple recovery options
            # They might be listed in 'step_data' or direct fields
            step_data = data.get("step_data", {})
            contact_points = step_data.get("contact_points", [])
            
            for point in contact_points:
                pt_type = point.get("contact_type")
                display = point.get("display")
                if pt_type == "EMAIL" and display:
                    result["emails"].append(display)
                elif pt_type == "PHONE" and display:
                    result["phones"].append(display)
                    
            # Fallback for older API versions
            if not result["emails"] and data.get("obfuscated_email"):
                result["emails"].append(data["obfuscated_email"])
                
            if not result["phones"] and data.get("obfuscated_phone"):
                result["phones"].append(data["obfuscated_phone"])
                
        return result
