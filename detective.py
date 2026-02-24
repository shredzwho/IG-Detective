#!/usr/bin/env python3
import instaloader
import getpass
import os
import sys
from src.python.core.scraper import InstagramScraper
from src.python.core.models import User, Post
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import print as rprint

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = r"""
    ___ ____      ____       _            _   _
   |_ _/ ___|    |  _ \  ___| |_ ___  ___| |_(_)_   _____
    | | |  _ ____| | | |/ _ \ __/ _ \/ __| __| \ \ / / _ \
    | | |_| |____| |_| |  __/ ||  __/ (__| |_| |\ V /  __/
   |___\____|    |____/ \___|\__\___|\___|\__|_| \_/ \___|
    """
    console.print(Panel(banner, subtitle="Open Source Intelligence Tool for Instagram", title="IG-Detective", border_style="bold cyan"))
    console.print("[bold yellow]Disclaimer:[/bold yellow] This tool is for educational purposes only. Please use it responsibly.\n")
    console.print("Created by [bold cyan]@shredzwho[/bold cyan]\n")


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
        self.report_dir = "data"

    def _save_report(self, category: str, data: Any, text_content: str = None):
        """Save command results to data/<target>/ directory."""
        if not self.target:
            return
            
        target_dir = os.path.join(self.report_dir, self.target)
        os.makedirs(target_dir, exist_ok=True)
        
        # Save JSON
        import json
        json_path = os.path.join(target_dir, f"{category}.json")
        try:
            # Handle non-serializable objects (like User/Post dataclasses)
            serializable_data = data
            if isinstance(data, list):
                from dataclasses import asdict, is_dataclass
                serializable_data = [asdict(item) if is_dataclass(item) else item for item in data]
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=4, default=str)
        except Exception as e:
            console.print(f"[dim red]Error saving JSON report: {e}[/dim red]")

        # Save TXT (optional formatted version)
        if text_content:
            txt_path = os.path.join(target_dir, f"{category}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

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
            console.print("[bold red]No target set.[/bold red] Use 'target [username]' first.")
            return

        table = Table(title=f"Target Profile: {self.target_data['username']}", show_header=False, border_style="dim")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("ID", str(self.target_data['id']))
        table.add_row("Name", self.target_data['full_name'])
        table.add_row("Bio", self.target_data['biography'])
        table.add_row("Followers", str(self.target_data['followers']))
        table.add_row("Following", str(self.target_data['followees']))
        table.add_row("Private", "[green]Yes[/green]" if self.target_data['is_private'] else "[red]No[/red]")
        table.add_row("Verified", "[blue]Yes[/blue]" if self.target_data['is_verified'] else "[red]No[/red]")
        table.add_row("Business", f"{self.target_data['is_business_account']} ({self.target_data['business_category']})")
        
        console.print(table)
        self._save_report("info", self.target_data)

    def do_followers(self, arg):
        """Get followers list: followers [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Fetching {limit} followers...") as status:
            try:
                followers = self.scraper.get_followers(self.target, limit)
                table = Table(title=f"Followers of {self.target}")
                table.add_column("No.", style="dim")
                table.add_column("Username", style="cyan")
                table.add_column("Full Name", style="white")
                
                for idx, user in enumerate(followers, 1):
                    table.add_row(str(idx), user.username, user.full_name)
                
                console.print(table)
                self._save_report("followers", followers)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_followings(self, arg):
        """Get followings list: followings [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Fetching {limit} followings...") as status:
            try:
                followings = self.scraper.get_followings(self.target, limit)
                table = Table(title=f"Followings of {self.target}")
                table.add_column("No.", style="dim")
                table.add_column("Username", style="cyan")
                table.add_column("Full Name", style="white")
                
                for idx, user in enumerate(followings, 1):
                    table.add_row(str(idx), user.username, user.full_name)
                
                console.print(table)
                self._save_report("followings", followings)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_posts(self, arg):
        """Get recent posts: posts [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
            
        limit = 10
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Fetching {limit} posts...") as status:
            try:
                posts = self.scraper.get_posts(self.target, limit)
                for post in posts:
                    panel = Panel(
                        f"[cyan]ID:[/cyan] {post.id}\n"
                        f"[cyan]Date:[/cyan] {post.timestamp}\n"
                        f"[cyan]Stats:[/cyan] {post.likes_count} Likes | {post.comments_count} Comments"
                        + (f" | {post.video_view_count} Views" if post.is_video else "") + "\n"
                        f"[cyan]Caption:[/cyan] {post.caption[:200]}..." if post.caption and len(post.caption) > 200 else f"[cyan]Caption:[/cyan] {post.caption}",
                        title=f"Post {post.shortcode}",
                        expand=False
                    )
                    console.print(panel)
                
                self._save_report("posts", posts)
            except Exception as e:
                 console.print(f"[bold red]Error:[/bold red] {e}")

    def do_hashtags(self, arg):
        """Analyze hashtags from recent posts: hashtags [limit_posts]"""
        if not self.target:
             console.print("[bold red]No target set.[/bold red]")
             return
        
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Analyzing hashtags from last {limit} posts...") as status:
            try:
                posts = self.scraper.get_posts(self.target, limit)
                top_hashtags = DataAnalyzer.get_most_used_hashtags(posts)
                
                table = Table(title=f"Top Hashtags: {self.target}")
                table.add_column("Hashtag", style="cyan")
                table.add_column("Count", style="white")
                
                for tag, count in top_hashtags:
                    table.add_row(f"#{tag}", str(count))
                
                console.print(table)
                self._save_report("hashtags", dict(top_hashtags))
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_addrs(self, arg):
        """Search for locations used in target's posts: addrs [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return

        limit = 50
        if arg.isdigit():
            limit = int(arg)

        with console.status(f"[bold green]Searching for locations in {limit} posts...") as status:
            try:
                locations = self.scraper.get_locations(self.target, limit)
                if not locations:
                    console.print("[yellow]No locations found.[/yellow]")
                    return

                table = Table(title=f"Location History: {self.target}")
                table.add_column("Date", style="dim")
                table.add_column("Location Name", style="cyan")
                table.add_column("Address", style="white")

                for loc in locations:
                    table.add_row(
                        loc["timestamp"].strftime("%Y-%m-%d %H:%M"),
                        loc["name"] or "Unknown",
                        loc["address"] or "No address found"
                    )
                
                console.print(table)
                self._save_report("locations", locations)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_tagged(self, arg):
        """Identify users tagged in target's posts: tagged [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return

        limit = 20
        if arg.isdigit():
            limit = int(arg)

        with console.status(f"[bold green]Checking tagged users in {limit} posts...") as status:
            try:
                tagged = self.scraper.get_tagged_users(self.target, limit)
                if not tagged:
                    console.print("[yellow]No tagged users found.[/yellow]")
                    return

                console.print(f"\n[bold cyan]Users tagged by {self.target}:[/bold cyan]")
                for user in sorted(tagged):
                    console.print(f"- {user}")
                self._save_report("tagged_users", sorted(tagged))
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_stats(self, arg):
        """Get aggregate statistics for target's account: stats [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return

        limit = 50
        if arg.isdigit():
            limit = int(arg)

        with console.status(f"[bold green]Calculating statistics for {limit} posts...") as status:
            try:
                posts = self.scraper.get_posts(self.target, limit)
                stats = DataAnalyzer.get_aggregate_stats(posts)

                table = Table(title=f"Account Statistics: {self.target} (Last {len(posts)} posts)", show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Total Likes", str(stats["total_likes"]))
                table.add_row("Total Comments", str(stats["total_comments"]))
                table.add_row("Avg Likes/Post", f"{stats['avg_likes']:.2f}")
                table.add_row("Avg Comments/Post", f"{stats['avg_comments']:.2f}")
                table.add_row("Photos", str(stats["photo_count"]))
                table.add_row("Videos", str(stats["video_count"]))
                table.add_row("Content Mix", f"{stats['photo_ratio']*100:.0f}% Photo / {stats['video_ratio']*100:.0f}% Video")

                console.print(table)
                self._save_report("stats", stats)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_stories(self, arg):
        """Fetch active story URLs: stories"""
        if not self.target:
             console.print("[bold red]No target set.[/bold red]")
             return
        
        with console.status("[bold green]Fetching active stories...") as status:
            try:
                urls = self.scraper.get_stories_urls(self.target)
                if not urls:
                    console.print("[yellow]No active stories found.[/yellow]")
                    return

                console.print(f"\n[bold cyan]Active Story URLs for {self.target}:[/bold cyan]")
                for idx, url in enumerate(urls, 1):
                    console.print(f"{idx}. {url}")
                self._save_report("stories", urls)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

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

    def do_logout(self, arg):
        """Logout and optionally delete session."""
        username = self.L.context.username
        print(f"Logging out {username}...")
        cleanup_session(username)
        self.scraper.cache.clear()
        print("Logged out and cache cleared.")
        return True

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
        
        console.print(f"\n[*] [bold green]Scanning {limit} followers of {self.target} for contact info...[/bold green]")
        console.print(f"[*] Results will be saved to [cyan]{csv_filename}[/cyan]")
        console.print("[yellow][!] Press Ctrl+C to stop scanning safely.[/yellow]\n")

        found_contacts = []
        try:
            mode = 'w'
            if os.path.exists(csv_filename):
                mode = 'a'
            
            with open(csv_filename, mode, newline='', encoding='utf-8') as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=["username", "full_name", "email", "phone"])
                if mode == 'w':
                    writer.writeheader()
                
                for contact in self.scraper.scan_followers_for_contact(self.target, limit):
                    writer.writerow(contact)
                    f.flush()
                    console.print(f"[bold green]+[/bold green] Found: [cyan]{contact['username']}[/cyan] | {contact['email']} | {contact['phone']}")
                    found_contacts.append(contact)
                    
        except KeyboardInterrupt:
            console.print("\n[bold red][!] Scan stopped by user.[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red][!] Error: {e}[/bold red]")
        finally:
            console.print(f"\n[*] Scan complete. Found [bold green]{len(found_contacts)}[/bold green] contacts.")
            self._save_report("followers_contacts", found_contacts)

    def do_fwingsemail(self, arg):
        """
        Scan followings for emails/phones: fwingsemail [limit]
        WARNING: Slow operation to ensure safety.
        """
        if not self.target:
            print("No target set.")
            return

        limit = 50
        if arg.isdigit():
            limit = int(arg)

        csv_filename = f"{self.target}_followings_contact.csv"
        
        console.print(f"\n[*] [bold green]Scanning {limit} followings of {self.target} for contact info...[/bold green]")
        console.print(f"[*] Results will be saved to [cyan]{csv_filename}[/cyan]")
        console.print("[yellow][!] Press Ctrl+C to stop scanning safely.[/yellow]\n")

        found_contacts = []
        try:
            mode = 'w'
            if os.path.exists(csv_filename):
                mode = 'a'
            
            with open(csv_filename, mode, newline='', encoding='utf-8') as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=["username", "full_name", "email", "phone"])
                if mode == 'w':
                    writer.writeheader()
                
                for contact in self.scraper.scan_followings_for_contact(self.target, limit):
                    writer.writerow(contact)
                    f.flush()
                    console.print(f"[bold green]+[/bold green] Found: [cyan]{contact['username']}[/cyan] | {contact['email']} | {contact['phone']}")
                    found_contacts.append(contact)
                    
        except KeyboardInterrupt:
            console.print("\n[bold red][!] Scan stopped by user.[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red][!] Error: {e}[/bold red]")
        finally:
            console.print(f"\n[*] Scan complete. Found [bold green]{len(found_contacts)}[/bold green] contacts.")
            self._save_report("followings_contacts", found_contacts)

    def do_commenters(self, arg):
        """Analyze top commenters from recent posts: commenters [limit_posts]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return

        limit = 10
        if arg.isdigit():
            limit = int(arg)

        with console.status(f"[bold green]Analyzing comments from last {limit} posts...") as status:
            try:
                comments = self.scraper.get_user_comments(self.target, limit)
                top_commenters = DataAnalyzer.get_top_commenters(comments)

                table = Table(title=f"Top Commenters: {self.target}")
                table.add_column("Username", style="cyan")
                table.add_column("Comment Count", style="white")

                for user, count in top_commenters:
                    table.add_row(user, str(count))

                console.print(table)
                self._save_report("commenters", dict(top_commenters))
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")


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
