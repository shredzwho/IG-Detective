import instaloader
import time
import random
import logging
from typing import List, Generator, Dict, Any, Optional
from src.ig_detective.core.models import User, Post
from src.ig_detective.config import settings

# Setup logger
logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self, loader: instaloader.Instaloader):
        self.L = loader

    def get_profile(self, username: str) -> User:
        """Fetch profile details for a given username using instaloader."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
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
        except instaloader.ProfileNotExistsException:
             logger.error(f"Profile {username} does not exist.")
             raise ValueError(f"User '{username}' does not exist.")
        except Exception as e:
            logger.error(f"Failed to fetch profile for {username}: {e}")
            raise Exception(f"Failed to fetch profile: {e}")

    def get_posts(self, username: str, count: int = 10) -> List[Post]:
        """Fetch n recent posts using instaloader."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
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
            return posts
        except Exception as e:
            logger.error(f"Failed to fetch posts for {username}: {e}")
            raise Exception(f"Failed to fetch posts: {e}")

    def get_followers(self, username: str, limit: int = 50) -> List[User]:
        """Fetch list of followers."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
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
            return followers
        except Exception as e:
            logger.error(f"Failed to fetch followers for {username}: {e}")
            raise Exception(f"Failed to fetch followers: {e}")

    def get_followings(self, username: str, limit: int = 50) -> List[User]:
        """Fetch list of followings."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
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
            return followings
        except Exception as e:
            logger.error(f"Failed to fetch followings for {username}: {e}")
            raise Exception(f"Failed to fetch followings: {e}")

    def scan_followers_for_contact(self, username: str, limit: int = 50) -> Generator[Dict[str, Any], None, None]:
        """
        Scan followers for email and phone numbers safely.
        """
        logger.info(f"Starting safe contact scan for {username}'s followers (Limit: {limit})")
        
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            count = 0
            
            followers_iter = profile.get_followers()
            
            for follower in followers_iter:
                if count >= limit:
                    break
                
                try:
                    full_profile = instaloader.Profile.from_username(self.L.context, follower.username)
                    
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
                    
                    # Safety Delays
                    sleep_time = random.uniform(settings.MIN_DELAY, settings.MAX_DELAY)
                    time.sleep(sleep_time)
                    
                    if count % settings.BATCH_SIZE == 0:
                        long_sleep = random.uniform(settings.BATCH_DELAY_MIN, settings.BATCH_DELAY_MAX)
                        logger.info(f"Batch {count} reached. Sleeping for {long_sleep:.2f}s...")
                        time.sleep(long_sleep)
                        
                except instaloader.ConnectionException as e:
                    logger.warning(f"Connection warning (potentially rate limited): {e}")
                    time.sleep(60) # Backoff
                    continue
                except instaloader.QueryReturnedNotFoundException:
                    continue
                except Exception as e:
                    logger.error(f"Error processing {follower.username}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Fatal error in contact scan: {e}")
            raise Exception(f"Failed to scan followers: {e}")
