import instaloader
import time
import random
from src.python.core.models import User, Post

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
        except Exception as e:
            raise Exception(f"Failed to fetch profile: {e}")

    def get_posts(self, username: str, count: int = 10) -> list[Post]:
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
            raise Exception(f"Failed to fetch posts: {e}")

    def get_followers(self, username: str, limit: int = 50) -> list[User]:
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
            raise Exception(f"Failed to fetch followers: {e}")

    def get_followings(self, username: str, limit: int = 50) -> list[User]:
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
            raise Exception(f"Failed to fetch followings: {e}")

    def get_user_info(self, username: str) -> dict:
        """Fetch detailed raw user info."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            return {
                "id": profile.userid,
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "followers": profile.followers,
                "followees": profile.followees,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified,
                "external_url": profile.external_url,
                "profile_pic_url": profile.profile_pic_url,
                "business_category": profile.business_category_name,
                "is_business_account": profile.is_business_account,
            }
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

    def scan_followers_for_contact(self, username: str, limit: int = 50, batch_size: int = 50) -> list[dict]:
        """
        Scan followers for email and phone numbers.
        CAUTION: This is a high-intensity operation. 
        Includes random delays to minimize risk.
        """
        print(f"[*] Starting safe scan for {username}'s followers (Limit: {limit})...")
        print("[!] This process is intentionally slow to avoid detection.")
        
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            contacts = []
            count = 0
            
            followers_iter = profile.get_followers()
            
            for follower in followers_iter:
                if count >= limit:
                    break
                
                try:
                    # We need to fetch full profile to get business emails
                    # This triggers a request per user
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
                        contacts.append(contact_info)
                        yield contact_info # Yield immediately to save progress
                    
                    count += 1
                    
                    # Random delay between requests (safety)
                    sleep_time = random.uniform(8, 15)
                    time.sleep(sleep_time)
                    
                    # Larger delay after a batch
                    if count % batch_size == 0:
                        long_sleep = random.uniform(30, 60)
                        print(f"[!] Batch {count} reached. Sleeping for {long_sleep:.2f}s...")
                        time.sleep(long_sleep)
                        
                except instaloader.ConnectionException as e:
                    print(f"[!] Connection error (likely rate limited): {e}")
                    print("[!] Stopping scan for safety.")
                    break
                except instaloader.QueryReturnedNotFoundException:
                    continue
                except Exception as e:
                    print(f"[!] Error processing {follower.username}: {e}")
                    continue
                    
            return contacts

        except Exception as e:
            raise Exception(f"Failed to scan followers: {e}")
