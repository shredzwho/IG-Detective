from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.core.models import User

console = Console()

def print_splash():
    """Renders the main logo and disclaimer."""
    splash = r"""
[bold cyan]    ___ ____      ____       _            _   _               
   |_ _/ ___|    |  _ \  ___| |_ ___  ___| |_(_)_   _____     
    | | |  _ ____| | | |/ _ \ __/ _ \/ __| __| \ \ / / _ \    
    | | |_| |____| |_| |  __/ ||  __/ (__| |_| |\ V /  __/    
   |___\____|    |____/ \___|\__\___|\___|\__|_| \_/ \___|    [/bold cyan]

[dim]Open Source Intelligence Tool for Instagram[/dim]
[italic]Disclaimer: For Educational & Authorized OSINT Use Only.[/italic]
    """
    console.print(splash)

def print_user_info(u: User):
    """Formats User data into a clean table."""
    table = Table(title=f"OSINT Profile: @{u.username}", border_style="cyan")
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(u.id))
    table.add_row("Full Name", u.full_name)
    table.add_row("Biography", u.biography or "N/A")
    table.add_row("Followers", f"{u.follower_count:,}")
    table.add_row("Following", f"{u.following_count:,}")
    table.add_row("Private", "[red]Yes[/red]" if u.is_private else "[green]No[/green]")
    table.add_row("Verified", "[cyan]Yes[/cyan]" if u.is_verified else "No")
    
    if u.business_email or u.business_phone or u.obfuscated_email or u.obfuscated_phone:
        table.add_row("Email", u.business_email or "None")
        table.add_row("Phone", u.business_phone or "None")
        table.add_row("Obfuscated Email", u.obfuscated_email or "None")
        table.add_row("Obfuscated Phone", u.obfuscated_phone or "None")
        
    console.print(Panel(table, expand=False))

def print_action_menu(target_username: str):
    """Displays the interactive post-login menu customized to the specific target."""
    table = Table(title=f"🕵️‍♂️ Target Locked: @{target_username}", border_style="green", expand=True)
    table.add_column("Command", style="bold green", justify="left")
    table.add_column("Category", style="magenta", justify="center")
    table.add_column("Description", style="white", justify="left")

    commands = [
        ("info", "Reconnaissance", "View basic profile information and metrics"),
        ("posts", "Reconnaissance", "Fetch recent timeline media and metadata"),
        ("addrs", "Advanced OSINT", "Extract geographical targets from embedded GPS"),
        ("data", "Investigation", "Export target footprints (media, followers) to a ZIP File"),
        ("surveillance", "Advanced OSINT", "Continuously monitor and trace target metrics/bio changes live"),
        ("temporal", "Analytics", "Calculate timezone and sleep behavior via DBSCAN"),
        ("stylometry", "Analytics", "Analyze linguistic fingerprints and emojis"),
        ("sna", "Analytics", "Build inner-circle network map from tags (Graph Theory)"),
        ("recovery", "Investigation", "Trigger account recovery enumeration to find masked emails/phones"),
        ("intersect", "Investigation", "Cross-reference GPS history of current target with another target"),
        ("audit", "Analytics", "Statistically assess the organic nature of interactions")
    ]
    
    for cmd, cat, desc in commands:
        table.add_row(cmd, cat, desc)
        
    console.print(table)
    console.print("\n[dim]✨ Type the command name (e.g. 'info') to execute it, or 'help' for the manual.[/dim]\n")
