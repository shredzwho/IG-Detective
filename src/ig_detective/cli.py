import typer
import sys
import os
import getpass
import instaloader
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
from pathlib import Path

from src.ig_detective.config import settings
from src.ig_detective.core.scraper import InstagramScraper
from src.ig_detective.core.models import User

# Initialize Rich Console
console = Console()
app = typer.Typer(help="IG-Detective: Advanced OSINT Tool for Instagram")

class IGDetectiveShell:
    def __init__(self):
        self.L = instaloader.Instaloader()
        self.scraper: Optional[InstagramScraper] = None
        self.target: Optional[str] = None
        self.target_data: Optional[User] = None

    def login(self):
        console.print(Panel.fit("Login to Instagram", style="bold blue"))
        
        while True:
            choice = Prompt.ask("Choose login method", choices=["1", "2", "3"], default="1", 
                              show_choices=False, 
                              prompt_display="[1] Username/Password\n[2] Load Session\n[3] Exit\nChoice")
            
            if choice == '1':
                username = Prompt.ask("Username")
                password = getpass.getpass("Password: ")
                
                try:
                    with console.status("[bold green]Logging in...", spinner="dots"):
                        self.L.login(username, password)
                    console.print("[bold green]Login successful![/]")
                    self._save_session(username)
                    self.scraper = InstagramScraper(self.L)
                    return
                except instaloader.TwoFactorAuthRequiredException:
                    code = Prompt.ask("Enter 2FA Code")
                    try:
                        self.L.two_factor_login(code)
                        self._save_session(username)
                        self.scraper = InstagramScraper(self.L)
                        return
                    except Exception as e:
                        console.print(f"[bold red]2FA Failed: {e}[/]")
                except Exception as e:
                    console.print(f"[bold red]Login Failed: {e}[/]")
            
            elif choice == '2':
                username = Prompt.ask("Username for session")
                session_path = settings.SESSION_DIR / f"session-{username}"
                try:
                    with console.status(f"[bold green]Loading session for {username}...", spinner="dots"):
                        self.L.load_session_from_file(username, filename=session_path)
                    console.print("[bold green]Session loaded![/]")
                    self.scraper = InstagramScraper(self.L)
                    return
                except FileNotFoundError:
                    console.print(f"[bold red]Session file not found at {session_path}[/]")
                except Exception as e:
                    console.print(f"[bold red]Error loading session: {e}[/]")
            
            elif choice == '3':
                sys.exit(0)

    def _save_session(self, username):
        session_file = settings.SESSION_DIR / f"session-{username}"
        self.L.save_session_to_file(filename=session_file)
        os.chmod(session_file, 0o600)
        console.print(f"[dim]Session saved to {session_file}[/]")

    def set_target(self, username: str):
        try:
            with console.status(f"[bold cyan]Fetching profile for {username}...", spinner="dots"):
                self.target_data = self.scraper.get_profile(username)
                self.target = username
            console.print(f"[bold green]Target set to: {username}[/]")
        except Exception as e:
            console.print(f"[bold red]Error setting target: {e}[/]")

    def print_info(self):
        if not self.target_data:
            console.print("[red]No target set.[/]")
            return

        table = Table(title=f"User Info: {self.target}", show_header=False)
        table.add_row("ID", str(self.target_data.username)) # using username as ID for display for now, or fetch ID
        table.add_row("Full Name", self.target_data.full_name)
        table.add_row("Bio", self.target_data.biography)
        table.add_row("Followers", str(self.target_data.follower_count))
        table.add_row("Following", str(self.target_data.following_count))
        table.add_row("Private", str(self.target_data.is_private))
        table.add_row("Business", f"{self.target_data.business_category}")
        console.print(table)

    def scan_contacts(self, limit: int):
        if not self.target:
             console.print("[red]No target set.[/]")
             return
        
        output_file = settings.OUTPUT_DIR / f"{self.target}_contacts.csv"
        console.print(f"[bold yellow]Starting contact scan for {limit} followers...[/]")
        console.print(f"[dim]Results will be saved to {output_file}[/]")

        import csv
        file_exists = output_file.exists()
        
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "full_name", "email", "phone"])
            if not file_exists:
                writer.writeheader()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Scanning...", total=limit)
                
                try:
                    count = 0
                    for contact in self.scraper.scan_followers_for_contact(self.target, limit):
                        writer.writerow(contact)
                        f.flush()
                        console.print(f"[green]Found: {contact['username']} | {contact['email']} | {contact['phone']}[/]")
                        count += 1
                        progress.update(task, advance=1, description=f"[cyan]Found {count} contacts...")
                except KeyboardInterrupt:
                    console.print("[bold red]Scan interrupted by user.[/]")
                except Exception as e:
                    console.print(f"[bold red]Error during scan: {e}[/]")

    def get_followers(self, limit: int):
        if not self.target:
             console.print("[red]No target set.[/]")
             return
        
        try:
            with console.status(f"[cyan]Fetching {limit} followers...", spinner="dots"):
                users = self.scraper.get_followers(self.target, limit)
            
            table = Table(title=f"Followers of {self.target}")
            table.add_column("#", style="dim")
            table.add_column("Username", style="bold")
            table.add_column("Full Name")
            
            for idx, user in enumerate(users, 1):
                table.add_row(str(idx), user.username, user.full_name or "")
            console.print(table)
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/]")

    def get_posts(self, limit: int):
        if not self.target:
             console.print("[red]No target set.[/]")
             return
        
        try:
            with console.status(f"[cyan]Fetching {limit} posts...", spinner="dots"):
                posts = self.scraper.get_posts(self.target, limit)
            
            for post in posts:
                p = Panel(
                    f"[bold]Date:[/] {post.timestamp}\n[bold]Likes:[/] {post.likes_count} | [bold]Comments:[/] {post.comments_count}\n[italic]{post.caption[:100]}...[/]",
                    title=f"Post {post.shortcode}",
                    subtitle=f"Video: {post.is_video}"
                )
                console.print(p)
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/]")

    def interactive_loop(self):
        self.login()
        console.print(Panel.fit("Welcome to IG-Detective Shell\nType 'help' for commands", style="bold magenta"))
        
        while True:
            # Dynamic prompt
            prompt_str = f"[bold cyan]ig-detective:{self.target or 'none'}>[/] " 
            cmd_input = Prompt.ask(prompt_str).strip().split()
            
            if not cmd_input:
                continue
            
            cmd = cmd_input[0].lower()
            args = cmd_input[1:]
            
            if cmd in ["exit", "quit", "logout"]:
                console.print("[bold red]Exiting...[/]")
                break
                
            elif cmd == "target":
                if args:
                    self.set_target(args[0])
                else:
                    console.print("[red]Usage: target <username>[/]")
            
            elif cmd == "info":
                self.print_info()

            elif cmd == "followers":
                limit = 50
                if args and args[0].isdigit():
                    limit = int(args[0])
                self.get_followers(limit)

            elif cmd == "posts":
                limit = 10
                if args and args[0].isdigit():
                    limit = int(args[0])
                self.get_posts(limit)
            
            elif cmd == "scan":
                limit = 50
                if args and args[0].isdigit():
                    limit = int(args[0])
                self.scan_contacts(limit)

            elif cmd == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                
            elif cmd == "help":
                table = Table(title="Available Commands")
                table.add_column("Command", style="cyan")
                table.add_column("Description")
                table.add_row("target <user>", "Set target user")
                table.add_row("info", "Show target info")
                table.add_row("followers [n]", "List n followers")
                table.add_row("posts [n]", "Show n recent posts")
                table.add_row("scan [limit]", "Scan followers for contacts (Safe Mode)")
                table.add_row("clear", "Clear screen")
                table.add_row("exit", "Exit tool")
                console.print(table)
            
            else:
                console.print(f"[red]Unknown command: {cmd}[/]")

@app.command()
def main():
    """Start the IG-Detective Interactive Shell"""
    shell = IGDetectiveShell()
    shell.interactive_loop()

if __name__ == "__main__":
    app()
