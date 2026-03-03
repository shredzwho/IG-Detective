import sys
import cmd2
from src.core.models import User
from src.api.client import InstagramClient
from src.modules.recon import ReconEngine
from src.modules.analytics import AnalyticsEngine
from src.modules.surveillance import SurveillanceEngine
from src.modules.exporter import DataExporter
from src.cli.formatters import console, print_splash, print_user_info, print_action_menu

class IGDetectiveShell(cmd2.Cmd):
    """The main interactive presentation interface for IG-Detective."""
    
    def __init__(self, client: InstagramClient):
        super().__init__(persistent_history_file="~/.config/ig-detective/.history")
        self.api = client
        self.recon = ReconEngine(client)
        self.surveillance = SurveillanceEngine()
        self.exporter = DataExporter(client, self.recon)
        self.target_username = None
        
        # UI Setup
        self.intro = ""
        self.prompt = "\n[IG-detective] > "
        
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
        except Exception as e:
            console.print(f"[bold yellow]⚠️ Warning: Failed to extract full web profile info: {e}[/bold yellow]")
            console.print("[dim]Target locked regardless. Proceeding to advanced enumeration modules.[/dim]")
            
        self.target_username = username
        self.prompt = f"\n[IG-detective] \033[1;35m@{self.target_username}\033[0m > "
        console.print(f"[bold green][*] Target successfully set to @{self.target_username}[/bold green]")
            
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

    def do_addrs(self, args):
        """Extract geographical targets from embedded GPS."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Extracting location data...", spinner="dots"):
            locations = self.recon.get_locations(self.target_username)
            
        if not locations:
            console.print("[yellow]No location data found in recent posts.[/yellow]")
            return
            
        from rich.table import Table
        t = Table(title="Extracted Targets (Locations)")
        t.add_column("Location Name", style="cyan")
        t.add_column("Coordinates", style="magenta")
        t.add_column("Address", style="white")
        
        for loc in locations:
            coords = f"{loc['lat']:.4f}, {loc['lng']:.4f}" if loc['lat'] else "Unknown GPS"
            t.add_row(loc['name'], coords, loc['address'] or "Reverse Geolocating Failed")
            
        console.print(t)

    def do_data(self, args):
        """Export the victim's data to a ZIP archive (Posts, Followers, Following, Stories)."""
        if not self.target_username:
            console.print("[red]Set a target first using 'target <username>'[/red]")
            return
            
        with console.status(f"[bold cyan]Initializing Data Export for @{self.target_username}...[/bold cyan]", spinner="arrow3") as status:
            try:
                def update_status(msg):
                    status.update(f"[bold cyan]{msg}[/bold cyan]")
                    
                zip_path = self.exporter.export_target_data(self.target_username, callback=update_status)
                console.print(f"\n[bold green]✅ Export completed successfully![/bold green]")
                console.print(f"📦 Archive saved at: [bold magenta]{zip_path}[/bold magenta]")
            except Exception as e:
                console.print(f"\n[bold red]❌ Process failed during data export: {e}[/bold red]")

    def do_surveillance(self, args):
        """Continuously monitor target profile for metric and bio modifications."""
        import time
        from src.modules.evasion import poisson_jitter
        
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        console.print(f"\n[bold green]👁️ Initiating Active Surveillance on @{self.target_username}[/bold green]")
        console.print("[dim]Tracking Follower diffs, Following diffs, Media Uploads, and Bio adjustments.[/dim]")
        console.print("[dim]Press Ctrl+C at any time to break the loop and return to the main menu.[/dim]\n")
        
        # We will use poisson_jitter(mean_delay=90)
        
        try:
            while True:
                with console.status(f"[cyan]Polling live profile...[/cyan]"):
                    user = self.recon.get_user_profile(self.target_username)
                
                # The engine handles comparisons and saving automatically
                deltas = self.surveillance.compare_and_log(user)
                
                if deltas:
                    import datetime
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    console.print(f"\n[bold yellow][{now}] 🚨 Surveillance Alerts:[/bold yellow]")
                    for delta in deltas:
                        console.print(f"  ➡️ {delta}")
                        
                # Sleep organically
                sleep_sec = poisson_jitter(90)
                with console.status(f"[dim]Sleeping for {sleep_sec}s to evade detection...[/dim]"):
                    time.sleep(sleep_sec)
                    
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Surveillance Disengaged.[/bold cyan]")
            
    def do_temporal(self, args):
        """Calculate timezone and sleep behavior via DBSCAN."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Analyzing temporal behavior...", spinner="dots"):
            posts = self.recon.get_recent_posts(self.target_username, 12)
            temp_data = AnalyticsEngine.analyze_temporal_behavior(posts)
            
        if not temp_data or temp_data.get("sleep_gap_duration", 0) == 0:
            console.print("[yellow]Not enough temporal variation to calculate a sleep cycle.[/yellow]")
            return
            
        console.print(f"[bold cyan]Predicted Timezone:[/bold cyan] {temp_data['predicted_timezone']}")
        console.print(f"[bold cyan]Estimated Sleep Start:[/bold cyan] {temp_data['sleep_start_hour']}:00 (Relative to 24h clock)")
        console.print(f"[bold cyan]Estimated Sleep Duration:[/bold cyan] {temp_data['sleep_gap_duration']} hours")

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

    def do_recovery(self, args):
        """Trigger account recovery enumeration to find masked emails/phones."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Initiating password reset pivot...", spinner="dots"):
            try:
                recovery_data = self.recon.trigger_recovery_flow(self.target_username)
            except Exception as e:
                console.print(f"[bold red]❌ Recovery failed: {e}[/bold red]")
                return
            
        if not recovery_data.get("has_recovery"):
            console.print("[yellow]No recovery points found.[/yellow]")
            return
            
        console.print("\n[bold cyan]🔓 Account Recovery Enumeration Results:[/bold cyan]")
        for email in recovery_data.get("emails", []):
            console.print(f"  📧 Masked Email: {email}")
        for phone in recovery_data.get("phones", []):
            console.print(f"  📱 Masked Phone: {phone}")

    def do_intersect(self, args):
        """Cross-reference GPS history of current target with another target."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        target2 = args.strip()
        if not target2:
            console.print("[red]Usage: intersect <username2>[/red]")
            return
            
        with console.status(f"[bold cyan]Cross-referencing {self.target_username} vs {target2}...", spinner="dots"):
            locs1 = self.recon.get_locations(self.target_username)
            locs2 = self.recon.get_locations(target2)
            intersections = AnalyticsEngine.compare_locations(locs1, locs2)
            
        if not intersections:
            console.print(f"[yellow]No temporal/spatial intersections found between {self.target_username} and {target2}.[/yellow]")
            return
            
        console.print(f"\n[bold red]⚠️ Co-Visitation Intersections Detected![/bold red]")
        for i, match in enumerate(intersections, 1):
            console.print(f"  [{i}] Location: {match['location_1']['name']}")
            console.print(f"      Distance offset: {match['distance_meters']:.1f}m")
            console.print(f"      Time offset: {match['time_diff']}")

    def do_audit(self, args):
        """Statistically assess the organic nature of interactions."""
        if not self.target_username:
            console.print("[red]Set a target first.[/red]")
            return
            
        with console.status("[bold cyan]Running Inauthentic Engagement Audit...", spinner="dots"):
            posts = self.recon.get_recent_posts(self.target_username, 24)
            audit_results = AnalyticsEngine.audit_engagement(posts)
            
        if audit_results.get("status") == "Insufficient data":
            console.print("[yellow]Insufficient timeline data for an audit.[/yellow]")
            return
            
        console.print("\n[bold cyan]🤖 Engagement Audit Results:[/bold cyan]")
        console.print(f"  Temporal Jitter Variance: {audit_results['temporal_jitter_variance']:.2f}")
        console.print(f"  Content Duplication Ratio: {audit_results['duplicate_content_ratio']:.2f}")
        bot_style = "red bold" if audit_results['bot_probability'] == 'High' else "green"
        console.print(f"  Bot/Inauthentic Probability: [{bot_style}]{audit_results['bot_probability']}[/{bot_style}]")
        
        flags = [f for f in audit_results.get('flags', []) if f]
        if flags:
            console.print("  [bold red]Red Flags Triggered:[/bold red]")
            for flag in flags:
                console.print(f"    - {flag}")

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
        elif cmd == "recovery":
            console.print("[bold cyan]RECOVERY COMMAND[/bold cyan]: Triggers password reset pivot to enumerate masked admin emails/phones.")
        elif cmd == "intersect":
            console.print("[bold cyan]INTERSECT COMMAND[/bold cyan]: Cross-references GPS history. Usage: `intersect <target2>`")
        elif cmd == "audit":
            console.print("[bold cyan]AUDIT COMMAND[/bold cyan]: Statistically assesses inorganic/bot interactions via jitter anomalies.")
        else:
            super().do_help(arg)

    def do_exit(self, args):
        """Exit the utility cleanly."""
        console.print("[bold green]Tearing down ig-detective instances... Goodbye![/bold green]")
        try:
            self.api.close()
        except Exception:
            pass
        return True
