import pytest
from unittest.mock import MagicMock
from src.python.core.scraper import InstagramScraper
from src.python.core.models import User, Post

@pytest.fixture
def mock_loader():
    return MagicMock()

@pytest.fixture
def scraper(mock_loader):
    return InstagramScraper(mock_loader)

def test_get_profile_success(scraper, mock_loader, monkeypatch):
    # Mock instaloader.Profile.from_username
    import instaloader
    
    mock_profile = MagicMock()
    mock_profile.username = "testuser"
    mock_profile.full_name = "Test User"
    mock_profile.biography = "Bio"
    mock_profile.followers = 1000
    mock_profile.followees = 500
    mock_profile.is_private = False
    mock_profile.is_verified = True
    mock_profile.profile_pic_url = "http://example.com/pic.jpg"
    mock_profile.external_url = None
    
    monkeypatch.setattr("instaloader.Profile.from_username", lambda ctx, user: mock_profile)
    
    user = scraper.get_profile("testuser")
    
    assert isinstance(user, User)
    assert user.username == "testuser"
    assert user.follower_count == 1000

def test_get_posts_success(scraper, mock_loader, monkeypatch):
    import instaloader
    
    mock_profile = MagicMock()
    mock_post = MagicMock()
    mock_post.mediaid = 123456
    mock_post.shortcode = "abc"
    mock_post.caption = "Test Caption"
    mock_post.likes = 10
    mock_post.comments = 2
    mock_post.date_utc = "2023-01-01"
    mock_post.owner_username = "testuser"
    mock_post.is_video = False
    
    mock_profile.get_posts.return_value = [mock_post]
    
    monkeypatch.setattr("instaloader.Profile.from_username", lambda ctx, user: mock_profile)
    
    posts = scraper.get_posts("testuser", count=1)
    
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].id == "123456"
