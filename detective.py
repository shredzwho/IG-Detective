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
import folium
from typing import Any

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
        # Ensure we are saving only inside the application report directory
        if not os.path.abspath(target_dir).startswith(os.path.abspath(self.report_dir)):
            console.print("[bold red]Path Traversal Prevented.[/bold red]")
            return
            
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
        
        import re
        username = arg.strip()
        
        # Sanitize username against path traversal or injection
        sanitized_username = re.sub(r'[^a-zA-Z0-9_\.]', '', username)
        if not sanitized_username:
            print("[bold red]Invalid username format.[/bold red]")
            return
        
        print(f"Checking if user '{sanitized_username}' exists...")
        try:
            self.target_data = self.scraper.get_user_info(sanitized_username)
            self.target = sanitized_username
            self.prompt = f'(ig-detective: {sanitized_username}) '
            print(f"Target set to: {sanitized_username}")
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
                
                # Task 3: Interactive Mapping with Folium
                target_dir = os.path.join(self.report_dir, self.target)
                m = folium.Map(location=[locations[0]["lat"], locations[0]["lng"]], zoom_start=12)
                for loc in locations:
                    if loc["lat"] and loc["lng"]:
                        folium.Marker(
                            [loc["lat"], loc["lng"]], 
                            popup=f"{loc['name']}\n{loc['address']}",
                            tooltip=loc["timestamp"].strftime("%Y-%m-%d %H:%M")
                        ).add_to(m)
                
                map_path = os.path.join(target_dir, "interactive_map.html")
                m.save(map_path)
                console.print(f"[bold green][*] Interactive map generated:[/bold green] [cyan]{map_path}[/cyan]")
                
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

    def do_sna(self, arg):
        """Social Network Analysis (Inner Circle): sna [post_limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
        
        limit = 20
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Performing SNA on {self.target} interactions...") as status:
            try:
                comments = self.scraper.get_user_comments(self.target, limit)
                tagged = self.scraper.get_tagged_users(self.target, limit)
                inner_circle = DataAnalyzer.perform_sna(self.target, comments, tagged)
                
                table = Table(title=f"The Inner Circle: {self.target} (Engagement Rank)")
                table.add_column("Rank", style="dim")
                table.add_column("User", style="cyan")
                table.add_column("Influence Score", style="white")
                
                for idx, (user, score) in enumerate(inner_circle, 1):
                    table.add_row(str(idx), user, f"{score:.4f}")
                    
                console.print(table)
                self._save_report("sna_inner_circle", inner_circle)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_temporal(self, arg):
        """Temporal Behavior & Timezone Prediction: temporal [limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
            
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Analyzing temporal patterns for {self.target}...") as status:
            try:
                posts = self.scraper.get_posts(self.target, limit)
                analysis = DataAnalyzer.analyze_temporal_behavior(posts)
                
                table = Table(title=f"Temporal Analysis: {self.target}", show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Sleep Gap Start", f"{analysis['sleep_start_hour']}:00 (Local Activity Trough)")
                table.add_row("Gap Duration", f"{analysis['sleep_gap_duration']} hours")
                table.add_row("Predicted Timezone", f"[bold green]{analysis['predicted_timezone']}[/bold green]")
                
                console.print(table)
                self._save_report("temporal_analysis", analysis)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_batch(self, arg):
        """Autonomous batch processing from file: batch <targets.txt>"""
        if not arg or not os.path.exists(arg):
            console.print(f"[bold red]Usage: batch <filename.txt>[/bold red]")
            return
            
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                targets = [line.strip() for line in f if line.strip()]
        except Exception as e:
            console.print(f"[bold red]Error reading batch file:[/bold red] {e}")
            return
            
        console.print(f"[bold cyan]Starting batch process for {len(targets)} targets...[/bold cyan]")
        for user in targets:
            console.print(f"\n[bold yellow]>>> Processing: {user}[/bold yellow]")
            self.do_target(user)
            if self.target:
                self.do_info("")
                self.do_stats("50")
                self.do_addrs("20")
                self.do_sna("20")
                self.do_temporal("50")
            console.print(f"[dim green]<<< Finished: {user}[/dim green]")
        
        console.print(f"\n[bold green][*] Batch process complete![/bold green]")

    def do_recovery(self, arg):
        """Account Recovery Enumeration (Forgot PWD Pivot): recovery"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
            
        with console.status(f"[bold green]Triggering recovery flow for {self.target}...") as status:
            try:
                info = self.scraper.get_recovery_info(self.target)
                if "error" in info:
                    console.print(f"[bold red]{info['error']}[/bold red]")
                    return
                
                panel = Panel(
                    f"[cyan]Status:[/cyan] {info['status']}\n"
                    f"[cyan]Message:[/cyan] {info['message']}\n"
                    f"[cyan]Tip:[/cyan] {info.get('body') or 'N/A'}",
                    title=f"Recovery Recon: {self.target}",
                    expand=False
                )
                console.print(panel)
                self._save_report("recovery_recon", info)
                
                # Check if we have an email in bio to verify
                if self.target_data.get('business_email'):
                    email = self.target_data['business_email']
                    console.print(f"\n[*] Target has business email: [bold cyan]{email}[/bold cyan]")
                    console.print("[*] Compare this against the Tip above to verify ownership.")
                
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_intersect(self, arg):
        """Geospatial Co-Visitation Analysis: intersect <username2>"""
        if not self.target or not arg:
            console.print("[bold red]Usage: intersect <username2>[/bold red]")
            return
            
        user2 = arg.strip()
        with console.status(f"[bold green]Analyzing intersections between {self.target} and {user2}...") as status:
            try:
                # Fetch locations for both
                locs1 = self.scraper.get_locations(self.target, 50)
                locs2 = self.scraper.get_locations(user2, 50)
                
                intersections = DataAnalyzer.find_location_intersections(locs1, locs2)
                
                if not intersections:
                    console.print(f"[yellow]No geospatial intersections found within 2-hour windows.[/yellow]")
                    return
                
                table = Table(title=f"Co-Visitation Analysis: {self.target} ∩ {user2}")
                table.add_column("Location", style="cyan")
                table.add_column("T1 (Target)", style="dim")
                table.add_column("T2 (Pivot)", style="dim")
                table.add_column("Gap (min)", style="white")
                
                for intersect in intersections:
                    table.add_row(
                        intersect['location_name'],
                        intersect['t1'].strftime("%Y-%m-%d %H:%M"),
                        intersect['t2'].strftime("%Y-%m-%d %H:%M"),
                        f"{intersect['time_diff_min']:.1f}"
                    )
                
                console.print(table)
                self._save_report(f"intersection_{user2}", intersections)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_stylometry(self, arg):
        """Stylometry & Linguistic Profiling: stylometry [limit_posts]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
            
        limit = 50
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Generating linguistic signature for {self.target}...") as status:
            try:
                posts = self.scraper.get_posts(self.target, limit)
                sig = DataAnalyzer.get_linguistic_signature(posts)
                
                if not sig:
                    console.print("[yellow]Not enough text data to generate signature.[/yellow]")
                    return
                
                console.print(f"\n[bold cyan]Linguistic Signature: {self.target}[/bold cyan]")
                
                # Emojis
                emoji_table = Table(title="Emoji Fingerprint", show_header=False)
                for emoji, count in sig['top_emojis']:
                    emoji_table.add_row(emoji, "█" * count + f" ({count})")
                console.print(emoji_table)
                
                # Bigrams
                console.print(f"\n[bold]Top Phrasal Bigrams:[/bold]")
                for b in sig['top_bigrams']:
                    console.print(f" - {b}")
                
                # Habits
                habits = sig['punctuation_habits']
                console.print(f"\n[bold]Punctuation Habits:[/bold]")
                console.print(f" - Multiple !!!: {habits['multiple_excl']} occurrences")
                console.print(f" - Ellipsal ...: {habits['ellipsis']} occurrences")
                console.print(f" - ALL CAPS Words: {habits['all_caps_words']}")
                console.print(f" - Lexical Diversity: {sig['lexical_diversity']:.2f}")

                self._save_report("stylometry_signature", sig)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def do_audit(self, arg):
        """Botnet & Inauthentic Engagement Audit: audit [posts_limit]"""
        if not self.target:
            console.print("[bold red]No target set.[/bold red]")
            return
            
        limit = 10
        if arg.isdigit():
            limit = int(arg)
            
        with console.status(f"[bold green]Auditing engagement authenticity for {self.target}...") as status:
            try:
                comments = self.scraper.get_user_comments(self.target, limit)
                audit = DataAnalyzer.audit_engagement(comments)
                
                if not audit:
                    console.print("[yellow]No comments found to audit.[/yellow]")
                    return
                
                table = Table(title=f"Engagement Audit: {self.target}", show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Temporal Variation (Jitter)", f"{audit['temporal_variation_std']:.4f}")
                table.add_row("Duplicate Ratio", f"{audit['duplicate_content_ratio']:.2%}")
                
                status_color = "red" if audit['is_suspicious'] else "green"
                table.add_row("Authenticity Status", f"[{status_color}]" + ("SUSPICIOUS" if audit['is_suspicious'] else "ORGANIC") + f"[/{status_color}]")
                
                console.print(table)
                if audit['is_suspicious']:
                    for r in audit['flagged_reasons']:
                        console.print(f" [red]![/red] {r}")
                
                self._save_report("engagement_audit", audit)
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
