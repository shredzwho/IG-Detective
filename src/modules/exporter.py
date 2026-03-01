import os
import time
import json
import zipfile
import urllib.request
from typing import Dict, Any, List
from src.api.client import InstagramClient
from src.modules.recon import ReconEngine
from src.api.endpoints import Endpoints
from src.core.config import settings

class DataExporter:
    """Handles downloading and neatly zipping all target footprint data."""
    
    def __init__(self, api: InstagramClient, recon: ReconEngine):
        self.api = api
        self.recon = recon
        self.base_dir = settings.DATA_DIR
        os.makedirs(self.base_dir, exist_ok=True)
        
    def _download_file(self, url: str, dest_path: str):
        if not url: return None
        try:
            req = urllib.request.Request(url, headers={'User-Agent': settings.USER_AGENT})
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            return dest_path
        except Exception as e:
            return None

    def _fetch_paginated_list(self, user_id: str, query_hash: str) -> List[str]:
        """Generic paginator for followers and following."""
        usernames = []
        end_cursor = ""
        has_next = True
        
        # Max out around 500 for safety against heavy rate limits during testing
        while has_next and len(usernames) < 500:
            try:
                if query_hash == Endpoints.HASH_FOLLOWERS:
                    url = Endpoints.followers(user_id, 50, end_cursor)
                else:
                    url = Endpoints.followings(user_id, 50, end_cursor)
                    
                data = self.api.get_json(url)
                
                # Navigate standard graphql response
                user_data = data.get('data', {}).get('user', {})
                edge_name = "edge_followed_by" if query_hash == Endpoints.HASH_FOLLOWERS else "edge_follow"
                edge = user_data.get(edge_name, {})
                
                edges = edge.get('edges', [])
                for e in edges:
                    usernames.append(e['node']['username'])
                    
                page_info = edge.get('page_info', {})
                has_next = page_info.get('has_next_page', False)
                end_cursor = page_info.get('end_cursor', "")
                
                time.sleep(2) # Be polite
            except Exception as e:
                break
                
        return usernames

    def export_target_data(self, username: str, callback=None) -> str:
        """Main orchestrated method to download all data and zip it."""
        if callback: callback("Fetching core profile and user ID...")
        user = self.recon.get_user_profile(username)
        user_id = user.id
        
        target_dir = os.path.join(self.base_dir, username, "export_raw")
        os.makedirs(target_dir, exist_ok=True)
        
        media_dir = os.path.join(target_dir, "media")
        os.makedirs(media_dir, exist_ok=True)
        
        # 1. Fetch Followers
        if callback: callback("Extracting follower network via GraphQL...")
        followers = self._fetch_paginated_list(user_id, Endpoints.HASH_FOLLOWERS)
        with open(os.path.join(target_dir, "followers.txt"), "w") as f:
            f.write("\n".join(followers))
            
        # 2. Fetch Following
        if callback: callback("Extracting following network via GraphQL...")
        following = self._fetch_paginated_list(user_id, Endpoints.HASH_FOLLOWINGS)
        with open(os.path.join(target_dir, "following.txt"), "w") as f:
            f.write("\n".join(following))
            
        # 3. Posts (Media)
        if callback: callback("Scraping timeline media...")
        posts = self.recon.get_recent_posts(username, 24) # Fetch double the default
        
        metadata = []
        for i, p in enumerate(posts):
            metadata.append({
                "id": p.id,
                "caption": p.caption,
                "timestamp": str(p.timestamp),
                "likes": p.likes_count,
                "is_video": p.is_video
            })
            
            # Identify the display_url
            raw = p.raw_node
            media_url = raw.get('video_url') if p.is_video else raw.get('display_url')
            if media_url:
                ext = ".mp4" if p.is_video else ".jpg"
                dest = os.path.join(media_dir, f"post_{p.id}{ext}")
                self._download_file(media_url, dest)
                
        with open(os.path.join(target_dir, "posts_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        # 4. Profile Picture
        if user.profile_pic_url:
            if callback: callback("Downloading high-res profile picture...")
            self._download_file(user.profile_pic_url, os.path.join(media_dir, "profile_pic.jpg"))
            
        # Zip it all up
        if callback: callback("Compressing forensic evidence into ZIP archive...")
        zip_filename = os.path.join(self.base_dir, f"{username}_forensic_export_{int(time.time())}.zip")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.join(self.base_dir, username))
                    zipf.write(file_path, arcname)
                    
        return zip_filename
