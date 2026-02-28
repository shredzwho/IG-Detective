from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class User:
    id: str
    username: str
    full_name: str
    biography: str = ""
    follower_count: int = 0
    following_count: int = 0
    is_private: bool = False
    is_verified: bool = False
    profile_pic_url: Optional[str] = None
    external_url: Optional[str] = None
    business_category: Optional[str] = None
    business_email: Optional[str] = None
    business_phone: Optional[str] = None

@dataclass
class Post:
    id: str
    shortcode: str
    owner_id: str
    timestamp: datetime
    caption: str = ""
    likes_count: int = 0
    comments_count: int = 0
    is_video: bool = False
    video_view_count: Optional[int] = None
    location_name: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    tagged_users: List[str] = field(default_factory=list)
    raw_node: Dict[str, Any] = field(default_factory=dict, repr=False)

@dataclass
class Comment:
    id: str
    post_id: str
    owner_username: str
    text: str
    created_at: datetime
