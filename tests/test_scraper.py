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
def test_scan_followers_for_contact(scraper, mock_loader, monkeypatch):
    import instaloader
    
    mock_profile = MagicMock()
    mock_follower = MagicMock()
    mock_follower.username = "follower1"
    
    mock_full_profile = MagicMock()
    mock_full_profile.username = "follower1"
    mock_full_profile.full_name = "Follower One"
    mock_full_profile.business_email = "test@example.com"
    mock_full_profile.business_phone_number = None

    mock_profile.get_followers.return_value = [mock_follower]
    
    def mock_from_username(ctx, username):
        if username == "testuser":
            return mock_profile
        return mock_full_profile

    monkeypatch.setattr("instaloader.Profile.from_username", mock_from_username)
    monkeypatch.setattr("random.uniform", lambda a, b: 0)
    monkeypatch.setattr("time.sleep", lambda s: None)
    
    contacts = list(scraper.scan_followers_for_contact("testuser", limit=1))
    
    assert len(contacts) == 1
    assert contacts[0]["username"] == "follower1"
    assert contacts[0]["email"] == "test@example.com"

def test_scan_followings_for_contact(scraper, mock_loader, monkeypatch):
    import instaloader
    
    mock_profile = MagicMock()
    mock_followee = MagicMock()
    mock_followee.username = "followee1"
    
    mock_full_profile = MagicMock()
    mock_full_profile.username = "followee1"
    mock_full_profile.full_name = "Followee One"
    mock_full_profile.business_email = None
    mock_full_profile.business_phone_number = "123456789"

    mock_profile.get_followees.return_value = [mock_followee]
    
    def mock_from_username(ctx, username):
        if username == "testuser":
            return mock_profile
        return mock_full_profile

    monkeypatch.setattr("instaloader.Profile.from_username", mock_from_username)
    monkeypatch.setattr("random.uniform", lambda a, b: 0)
    monkeypatch.setattr("time.sleep", lambda s: None)
    
    contacts = list(scraper.scan_followings_for_contact("testuser", limit=1))
    
    assert len(contacts) == 1
    assert contacts[0]["username"] == "followee1"
    assert contacts[0]["phone"] == "123456789"
