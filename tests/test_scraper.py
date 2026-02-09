import pytest
from src.python.core.scraper import InstagramScraper
import requests_mock

@pytest.fixture
def scraper():
    return InstagramScraper()

from src.python.core.models import User, Post

def test_get_profile_success(scraper):
    username = "testuser"
    # For now, the scraper returns a dummy User object directly.
    # In a real implementation with requests, we'd mock the response and check the parsed User object.
    user = scraper.get_profile(username)
    
    assert isinstance(user, User)
    assert user.username == username
    assert user.full_name == "Test User"
    assert user.follower_count == 1000

def test_get_posts_placeholder(scraper):
    username = "testuser"
    posts = scraper.get_posts(username)
    
    assert isinstance(posts, list)
    assert len(posts) > 0
    assert isinstance(posts[0], Post)
    assert posts[0].caption == "Hello World!"
    assert posts[0].owner_username == username
