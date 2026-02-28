import sys
import cmd2
from src.core.models import User
from src.api.client import InstagramClient
from src.modules.recon import ReconEngine
from src.modules.analytics import AnalyticsEngine
from src.cli.formatters import console, print_splash, print_user_info, print_action_menu

class IGDetectiveShell(cmd2.Cmd):
    """The main interactive presentation interface for IG-Detective."""
    
    def __init__(self, client: InstagramClient):
        super().__init__(persistent_history_file="~/.config/ig-detective/.history")
        self.api = client
        self.recon = ReconEngine(client)
        self.target_username = None
        
        # UI Setup
        self.intro = ""
        self.prompt = "\n[ig-detective] > "
        
    def preloop(self):
        """Executes before the cmd loop begins (Target Selection UX Flow)."""
        if self.api.is_authenticated:
            console.print("[bold green][*] Successfully Loaded Session cookies![/bold green]")
        else:
            console.print("[yellow][!] Warning: Running continuously As Unauthenticated Guest.[/yellow]")
            
        while not self.target_username:
            target = input("\n🎯 Enter Target Instagram Username (or 'exit' to quit): ").strip()
            if target.lower() == 'exit':
                sys.exit(0)
            if target:
                self.do_target(target)
                
        # UX Flow: Display menu only after target is set
        print_action_menu(self.target_username)

    def do_target(self, args):
        """Set a new target to investigate. Example: target shredzwho"""
        username = args.strip()
        if not username:
            console.print("[red]Error: You must provide a username. Usage: target <username>[/red]")
            return
            
        console.print(f"[*] Validating target '@{username}' via OSINT extraction...")
        try:
            with console.status("[bold cyan]Fetching profile metadata...", spinner="dots"):
                user = self.recon.get_user_profile(username)
                
            self.target_username = user.username
            self.prompt = f"\n[ig-detective] [bold magenta]@{self.target_username}[/bold magenta] > "
            console.print(f"[bold green][*] Target successfully set to @{self.target_username}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Error setting target: {e}[/bold red]")
            self.target_username = None
            
    def do_info(self, args):
        """View basic profile intelligence via target web info."""
        if not self.target_username:
            console.print("[red]Set a target first using 'target <username>'[/red]")
            return
            
        with console.status(f"[bold cyan]Scraping info for @{self.target_username}...", spinner="dots"):
            user = self.recon.get_user_profile(self.target_username)
            print_user_info(user)
            
    def do_posts(self, args):
        """Fetch the target's recent timeline activity."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Scraping recent posts...", spinner="dots"):
            posts = self.recon.get_recent_posts(self.target_username, 12)
            
        if not posts:
            console.print("[yellow]No posts found or account is private/blocked.[/yellow]")
            return
            
        console.print(f"[bold green]Found {len(posts)} recent media posts.[/bold green]")
        stats = AnalyticsEngine.get_aggregate_stats(posts)
        if stats:
            console.print(f"  📸 Photos: {stats['photo_count']} | 🎥 Videos: {stats['video_count']}")
            console.print(f"  ❤️ Avg Likes: {stats['avg_likes']:.1f} | 💬 Avg Comments: {stats['avg_comments']:.1f}")

    def do_sna(self, args):
        """Perform Social Network Analysis (Inner Circle Extraction) based on post interactions."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Executing Graph Theory SNA Analysis...", spinner="dots"):
            posts = self.recon.get_recent_posts(self.target_username, 12)
            tagged_groups = [p.tagged_users for p in posts if p.tagged_users]
            inner_circle = AnalyticsEngine.perform_sna(self.target_username, tagged_groups)
        
        if not inner_circle:
            console.print("[yellow]Insufficient tags found to build a social network graph.[/yellow]")
            return
            
        console.print("\n[bold cyan]🧠 Top Inner Circle (Degree Centrality):[/bold cyan]")
        for user, score in inner_circle:
            console.print(f"  ➡️ @{user} (Weight/Interaction Score: {score})")
            
    def do_stylometry(self, args):
        """Perform linguistic profiling on textual footprint (captions)."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Extracting Linguistic footprint...", spinner="dots"):
            posts = self.recon.get_recent_posts(self.target_username, 12)
            signature = AnalyticsEngine.get_linguistic_signature(posts)
            
        if not signature:
            console.print("[yellow]Not enough text data available for stylometry.[/yellow]")
            return
            
        from rich.table import Table
        t = Table(title="Linguistic Signature (Stylometry)", show_header=False)
        t.add_column("Metric", style="cyan bold")
        t.add_column("Value", style="white")
        
        t.add_row("Lexical Diversity", f"{signature['lexical_diversity']:.2f} (0-1.0)")
        
        emojis = ", ".join([f"{e} (x{c})" for e, c in signature.get('top_emojis', [])])
        t.add_row("Top Emojis", emojis or "None")
        
        bigrams = ", ".join(signature.get('top_bigrams', []))
        t.add_row("Favored Bigrams", bigrams or "None")
        
        punct = signature.get('punctuation_habits', {})
        t.add_row("Excessive '!'", str(punct.get('multiple_excl', 0)))
        t.add_row("Excessive '?'", str(punct.get('multiple_qmark', 0)))
        
        console.print(t)

    def do_help(self, arg):
        """Displays interactive /help menu."""
        if not arg:
            print_action_menu(self.target_username or "???")
            return
            
        cmd = arg.strip().lower()
        if cmd == "info":
            console.print("[bold cyan]INFO COMMAND[/bold cyan]: Extracts web profile OSINT (bio, hidden business emails, external IDs).")
            console.print("Usage: type `info`, no arguments needed.")
        elif cmd == "sna":
            console.print("[bold cyan]SNA COMMAND[/bold cyan]: Builds an interactive connection graph via NetworkX (Social Network Analysis). Extracts the target's 'real' connections weighted by interactions.")
            console.print("Usage: type `sna`, no arguments needed.")
        elif cmd == "stylometry":
            console.print("[bold cyan]STYLOMETRY COMMAND[/bold cyan]: NLP linguistic profiling. Scans n-grams, common punctuation errors, and emojis across the user's captions to fingerprint writing styles.")
        else:
            super().do_help(arg)

    def do_exit(self, args):
        """Exit the utility cleanly."""
        console.print("[bold green]Tearing down ig-detective instances... Goodbye![/bold green]")
        return True
