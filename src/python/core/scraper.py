import instaloader
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
