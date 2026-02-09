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

def set_secure_permissions(filepath):
    """Set file permissions to 600 (read/write only by owner)."""
    if os.path.exists(filepath):
        os.chmod(filepath, 0o600)
        # print(f"Secured permissions for {filepath}")

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

def main_menu(L):
    scraper = InstagramScraper(L)
    
    while True:
        clear_screen()
        print_banner()
        print(f"Logged in as: {L.context.username if L.context.is_logged_in else 'Guest'}\n")
        print("1. Get User Profile Info")
        print("2. Get Recent Posts")
        print("3. Download Profile (Posts/Stories)")
        print("4. Logout & Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            target_username = input("\nEnter target username: ").strip()
            try:
                user = scraper.get_profile(target_username)
                print(f"\nUsername: {user.username}")
                print(f"Full Name: {user.full_name}")
                print(f"Bio: {user.biography}")
                print(f"Followers: {user.follower_count}")
                print(f"Following: {user.following_count}")
                print(f"Verified: {user.is_verified}")
                print(f"Private: {user.is_private}")
                print(f"Pic URL: {user.profile_pic_url}")
                if user.business_category:
                    print(f"Category: {user.business_category}")
                if user.business_email:
                    print(f"Email: {user.business_email}")
                if user.business_phone:
                    print(f"Phone: {user.business_phone}")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")

        elif choice == '2':
            target_username = input("\nEnter target username: ").strip()
            count = input("How many posts? (default 10): ").strip()
            if not count:
                count = 10
            else:
                try:
                    count = int(count)
                except ValueError:
                    print("Invalid number, using default 10.")
                    count = 10
            
            try:
                print(f"\nFetching {count} posts for {target_username}...")
                posts = scraper.get_posts(target_username, count)
                for post in posts:
                    print("-" * 40)
                    print(f"ID: {post.id} ({post.shortcode})")
                    print(f"Date: {post.timestamp}")
                    print(f"Likes: {post.likes_count} | Comments: {post.comments_count}")
                    if post.is_video:
                        print(f"Views: {post.video_view_count}")
                    if post.caption:
                        print(f"Caption: {post.caption[:100]}..." if len(post.caption) > 100 else f"Caption: {post.caption}")
                print("-" * 40)
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")

        elif choice == '3':
            target_username = input("\nEnter target username to download: ").strip()
            try:
                print(f"\nDownloading profile {target_username}...")
                profile = instaloader.Profile.from_username(L.context, target_username)
                L.download_profile(profile, profile_pic_only=False)
                print(f"\nDownload complete! Check the folder '{target_username}'.")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"Error downloading: {e}")
                input("\nPress Enter to continue...")

        elif choice == '4':
            print("\n1. Logout & Keep Session")
            print("2. Logout & Delete Session (Secure)")
            sub_choice = input("Enter choice (1-2): ").strip()
            
            if sub_choice == '2':
                if L.context.is_logged_in:
                    cleanup_session(L.context.username)
            
            print("\nExiting...")
            sys.exit(0)
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    clear_screen()
    print_banner()
    loader = login()
    if loader:
        main_menu(loader)
