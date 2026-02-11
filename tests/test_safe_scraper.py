import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.python.core.scraper import InstagramScraper

class TestSafeScraper(unittest.TestCase):
    def setUp(self):
        self.mock_loader = MagicMock()
        self.scraper = InstagramScraper(self.mock_loader)

    @patch('time.sleep')
    @patch('random.uniform')
    def test_scan_followers_for_contact(self, mock_random, mock_sleep):
        """Test scanning followers with simulated delays and data extraction."""
        # Mock random to return fixed values for predictable testing
        mock_random.side_effect = [10.0, 30.0, 10.0, 30.0] 
        
        # Mock followers iterator (2 followers)
        mock_follower_1 = MagicMock()
        mock_follower_1.username = "user1"
        mock_follower_2 = MagicMock()
        mock_follower_2.username = "user2"
        
        # Mock profile.get_followers()
        mock_profile = MagicMock()
        mock_profile.get_followers.return_value = [mock_follower_1, mock_follower_2]

        # Use side_effect function to return different mocks based on username
        def side_effect_from_username(context, username):
            if username == "target_user":
                return mock_profile
            elif username == "user1":
                m = MagicMock()
                m.username = "user1"
                m.full_name = "User One"
                m.business_email = "user1@example.com"
                m.business_phone_number = None
                return m
            elif username == "user2":
                m = MagicMock()
                m.username = "user2"
                m.full_name = "User Two"
                m.business_email = None
                m.business_phone_number = "+1234567890"
                return m
            else:
                raise Exception("Unknown user")

        with patch('instaloader.Profile.from_username', side_effect=side_effect_from_username):
            # Run the scan
            # Limit=2, Batch=1 (to test batch sleep)
            contacts = list(self.scraper.scan_followers_for_contact("target_user", limit=2, batch_size=1))
            
            # Verify results
            self.assertEqual(len(contacts), 2)
            self.assertEqual(contacts[0]['email'], "user1@example.com")
            self.assertEqual(contacts[1]['phone'], "+1234567890")

if __name__ == '__main__':
    unittest.main()
