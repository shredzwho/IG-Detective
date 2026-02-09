from src.python.core.models import User, Post
import requests

class InstagramScraper:
    BASE_URL = "https://www.instagram.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })

    def get_profile(self, username) -> User:
        """Fetch profile details for a given username."""
        # Placeholder logic simulating a successful fetch
        return User(
            username=username,
            full_name="Test User",
            biography="This is a test biography.",
            follower_count=1000,
            following_count=500,
            is_private=False,
            is_verified=True
        )

    def get_posts(self, username, count=10) -> list[Post]:
        """Fetch n recent posts."""
        # Placeholder logic
        return [
            Post(
                id="1234567890",
                shortcode="B_123abc",
                caption="Hello World!",
                likes_count=150,
                comments_count=20,
                owner_username=username,
                is_video=False
            )
        ]
