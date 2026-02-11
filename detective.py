#!/usr/bin/env python3
import instaloader
import getpass
import os
import sys
from src.python.core.scraper import InstagramScraper
from src.python.core.models import User, Post

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(r"""
    ___ ____      ____       _            _   _
   |_ _/ ___|    |  _ \  ___| |_ ___  ___| |_(_)_   _____
    | | |  _ ____| | | |/ _ \ __/ _ \/ __| __| \ \ / / _ \
    | | |_| |____| |_| |  __/ ||  __/ (__| |_| |\ V /  __/
   |___\____|    |____/ \___|\__\___|\___|\__|_| \_/ \___|
    """)
    print("    IG-Detective - Open Source Intelligence Tool for Instagram")
    print("    ----------------------------------------------------------\n")
    print("Disclaimer: This tool is for educational purposes only. Please use it responsibly and respect the privacy of others.\n")
    print("Created by @shredzwho\n")


def set_secure_permissions(filepath):
    """Set file permissions to 600 (read/write only by owner)."""
    if os.path.exists(filepath):
        os.chmod(filepath, 0o600)

def cleanup_session(username):
    """Delete session file if it exists."""
    session_file = f"session-{username}"
    # check in local dir and config dir
    paths = [
        session_file,
        os.path.join(os.path.expanduser("~"), ".config/instaloader", session_file)
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted session file: {path}")
            except OSError as e:
                print(f"Error deleting {path}: {e}")

def login():
    L = instaloader.Instaloader()
    
    while True:
        print("Login Options:")
        print("1. Username & Password")
        print("2. Session File (if already saved)")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            username = input("Enter Instagram Username: ").strip()
            password = getpass.getpass("Enter Instagram Password: ").strip()
            try:
                print("\nAttempting to log in...")
                L.login(username, password)
                print("Login successful!")
                L.save_session_to_file()
                set_secure_permissions(f"session-{username}")
                print("Session saved to file.")
                return L
            except instaloader.TwoFactorAuthRequiredException:
                code = input("Enter 2FA Code: ").strip()
                try:
                    L.two_factor_login(code)
                    print("Login successful!")
                    L.save_session_to_file()
                    set_secure_permissions(f"session-{username}")
                    print("Session saved to file.")
                    return L
                except Exception as e:
                    print(f"2FA failed: {e}")
            except instaloader.BadCredentialsException:
                print("Invalid username or password.")
            except Exception as e:
                print(f"Login failed: {e}")
        
        elif choice == '2':
            username = input("Enter Instagram Username for session: ").strip()
            try:
                print(f"\nLoading session for {username}...")
                L.load_session_from_file(username)
                print("Session loaded successfully!")
                return L
            except FileNotFoundError:
                print("Session file not found.")
            except Exception as e:
                print(f"Failed to load session: {e}")
                
        elif choice == '3':
            sys.exit(0)
        else:
            print("Invalid choice.")

import cmd
from src.python.core.analysis import DataAnalyzer

class InteractiveShell(cmd.Cmd):
    intro = 'Welcome to IG-Detective Shell. Type help or ? to list commands.\n'
    prompt = '(ig-detective) '
    
    def __init__(self, loader):
        super().__init__()
        self.L = loader
        self.scraper = InstagramScraper(loader)
        self.target = None
        self.target_data = None 

    def do_target(self, arg):
        """Set target username: target [username]"""
        if not arg:
            print("Usage: target [username]")
            return
        
        username = arg.strip()
        print(f"Checking if user '{username}' exists...")
        try:
            self.target_data = self.scraper.get_user_info(username)
            self.target = username
            self.prompt = f'(ig-detective: {username}) '
            print(f"Target set to: {username}")
        except Exception as e:
            print(f"Error setting target: {e}")
            self.target = None
            self.prompt = '(ig-detective) '

    def do_info(self, arg):
        """Show current target info."""
        if not self.target:
            print("No target set. Use 'target [username]' first.")
            return

        print("\n" + "="*40)
        print(f"Target: {self.target_data['username']}")
        print("-" * 40)
        print(f"ID: {self.target_data['id']}")
        print(f"Name: {self.target_data['full_name']}")
        print(f"Bio: {self.target_data['biography']}")
        print(f"Followers: {self.target_data['followers']}")
        print(f"Following: {self.target_data['followees']}")
        print(f"Private: {self.target_data['is_private']}")
        print(f"Verified: {self.target_data['is_verified']}")
        print(f"Business: {self.target_data['is_business_account']} ({self.target_data['business_category']})")
        print(f"Profile Pic: {self.target_data['profile_pic_url']}")
        print("="*40 + "\n")

    def do_followers(self, arg):
        """Get followers list: followers [limit]"""
        if not self.target:
            print("No target set.")
            return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        print(f"Fetching {limit} followers...")
        try:
            followers = self.scraper.get_followers(self.target, limit)
            print(f"\nFound {len(followers)} followers:")
            for idx, user in enumerate(followers, 1):
                print(f"{idx}. {user.username} - {user.full_name}")
        except Exception as e:
            print(f"Error: {e}")

    def do_followings(self, arg):
        """Get followings list: followings [limit]"""
        if not self.target:
            print("No target set.")
            return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        print(f"Fetching {limit} followings...")
        try:
            followings = self.scraper.get_followings(self.target, limit)
            print(f"\nFound {len(followings)} followings:")
            for idx, user in enumerate(followings, 1):
                print(f"{idx}. {user.username} - {user.full_name}")
        except Exception as e:
            print(f"Error: {e}")

    def do_posts(self, arg):
        """Get recent posts: posts [limit]"""
        if not self.target:
            print("No target set.")
            return
            
        limit = 10
        if arg.isdigit():
            limit = int(arg)
            
        print(f"Fetching {limit} posts...")
        try:
            posts = self.scraper.get_posts(self.target, limit)
            for post in posts:
                print("-" * 40)
                print(f"ID: {post.id}")
                print(f"Date: {post.timestamp}")
                print(f"Likes: {post.likes_count} | Comments: {post.comments_count}")
                if post.is_video:
                    print(f"Views: {post.video_view_count}")
                print(f"Caption: {post.caption[:100]}..." if post.caption and len(post.caption) > 100 else f"Caption: {post.caption}")
        except Exception as e:
             print(f"Error: {e}")

    def do_hashtags(self, arg):
        """Analyze hashtags from recent posts: hashtags [limit_posts]"""
        if not self.target:
             print("No target set.")
             return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        print(f"Analyzing hashtags from last {limit} posts...")
        try:
            posts = self.scraper.get_posts(self.target, limit)
            top_hashtags = DataAnalyzer.get_most_used_hashtags(posts)
            
            print("\nTop Hashtags Used:")
            for tag, count in top_hashtags:
                print(f"#{tag}: {count}")
        except Exception as e:
            print(f"Error: {e}")

    def do_propic(self, arg):
        """Download profile picture."""
        if not self.target:
            print("No target set.")
            return
        
        print(f"Downloading profile picture for {self.target}...")
        try:
             self.L.download_profile(self.target, profile_pic_only=True)
             print("Download complete.")
        except Exception as e:
             print(f"Error: {e}")

    def do_clear(self, arg):
        """Clear screen."""
        clear_screen()
        print_banner()

    def do_exit(self, arg):
        """Exit the shell."""
        print("Exiting...")
        return True

    def do_quit(self, arg):
        """Exit the shell."""
        return self.do_exit(arg)

    def do_fwersemail(self, arg):
        """
        Scan followers for emails/phones: fwersemail [limit]
        WARNING: Slow operation to ensure safety.
        """
        if not self.target:
            print("No target set.")
            return

        limit = 50
        if arg.isdigit():
            limit = int(arg)

        csv_filename = f"{self.target}_followers_contact.csv"
        
        print(f"\n[*] Scanning {limit} followers of {self.target} for contact info...")
        print(f"[*] Results will be saved to {csv_filename}")
        print("[!] Press Ctrl+C to stop scanning safely.\n")

        found_count = 0
        try:
            # Create/Open CSV and write header
            mode = 'w'
            if os.path.exists(csv_filename):
                mode = 'a'
            
            with open(csv_filename, mode, newline='', encoding='utf-8') as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=["username", "full_name", "email", "phone"])
                if mode == 'w':
                    writer.writeheader()
                
                # Iterate generator
                for contact in self.scraper.scan_followers_for_contact(self.target, limit):
                    writer.writerow(contact)
                    f.flush() # Ensure it's written immediately
                    print(f"[+] Found: {contact['username']} | {contact['email']} | {contact['phone']}")
                    found_count += 1
                    
        except KeyboardInterrupt:
            print("\n[!] Scan stopped by user.")
        except Exception as e:
            print(f"\n[!] Error: {e}")
        finally:
            print(f"\n[*] Scan complete. Found {found_count} contacts.")
            print(f"[*] Saved to {csv_filename}")

    def do_fwingsemail(self, arg):
        """
        Scan followings for emails/phones: fwingsemail [limit]
        WARNING: Slow operation to ensure safety.
        """
        # Logic is identical to fwersemail but using get_followees (not implemented in shared scraper yet efficiently, 
        # so for now we will reuse similar logic or just warn it's prospective)
        print("Feature coming soon! (Use fwersemail for now)")


if __name__ == "__main__":
    clear_screen()
    print_banner()
    loader = login()
    if loader:
        try:
            shell = InteractiveShell(loader)
            shell.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
