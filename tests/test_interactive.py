import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detective import InteractiveShell
from src.python.core.models import User, Post

class TestInteractiveShell(unittest.TestCase):
    def setUp(self):
        self.mock_loader = MagicMock()
        self.shell = InteractiveShell(self.mock_loader)
        # Mock the scraper instance inside shell
        self.shell.scraper = MagicMock()

    def test_do_target_success(self):
        """Test setting a valid target."""
        self.shell.scraper.get_user_info.return_value = {
            "username": "test_user", "id": "123", "full_name": "Test User",
            "biography": "Bio", "followers": 100, "followees": 50,
            "is_private": False, "is_verified": False,
            "is_business_account": False, "business_category": None,
            "profile_pic_url": "http://example.com/pic.jpg"
        }
        
        self.shell.do_target("test_user")
        
        self.assertEqual(self.shell.target, "test_user")
        self.assertIn("test_user", self.shell.prompt)
        self.shell.scraper.get_user_info.assert_called_with("test_user")

    def test_do_target_failure(self):
        """Test setting an invalid target."""
        self.shell.scraper.get_user_info.side_effect = Exception("User not found")
        
        self.shell.do_target("invalid_user")
        
        self.assertIsNone(self.shell.target)
        self.assertEqual(self.shell.prompt, "(ig-detective) ")

    def test_do_info_no_target(self):
        """Test info command without target."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
             self.shell.do_info("")
             # Should print warning
             self.assertTrue(mock_stdout.write.called)

    def test_do_followers(self):
        """Test followers command."""
        self.shell.target = "test_user"
        self.shell.scraper.get_followers.return_value = [
            User(username="f1", full_name="Follower 1"),
            User(username="f2", full_name="Follower 2")
        ]
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            self.shell.do_followers("10")
            self.shell.scraper.get_followers.assert_called_with("test_user", 10)

    def test_do_posts(self):
        """Test posts command."""
        self.shell.target = "test_user"
        self.shell.scraper.get_posts.return_value = [
            Post(id="1", shortcode="abc", caption="Hello #world", likes_count=10, comments_count=2),
        ]
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            self.shell.do_posts("5") 
            self.shell.scraper.get_posts.assert_called_with("test_user", 5)

if __name__ == '__main__':
    unittest.main()
