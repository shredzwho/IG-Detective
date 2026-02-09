from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class User:
    username: str
    full_name: Optional[str] = None
    biography: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    is_private: bool = False
    is_verified: bool = False
    profile_pic_url: Optional[str] = None
    external_url: Optional[str] = None
    business_email: Optional[str] = None
    business_phone: Optional[str] = None
    business_category: Optional[str] = None

@dataclass
class Location:
    id: str
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    slug: Optional[str] = None

@dataclass
class Post:
    id: str
    shortcode: str
    caption: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    timestamp: Optional[datetime] = None
    owner_username: str = ""
    location: Optional[Location] = None
    is_video: bool = False
    video_view_count: Optional[int] = None
