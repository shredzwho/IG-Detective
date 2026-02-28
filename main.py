import sys
from rich.console import Console
from src.cli.formatters import print_splash
from src.api.client import InstagramClient
from src.cli.shell import IGDetectiveShell
from src.api.auth import SessionManager

console = Console()

def boot():
    """Starts the application."""
    print_splash()
    
    console.print("\n[bold cyan]Select an Authentication Strategy:[/bold cyan]")
    console.print("1. [bold white]Username & Password[/bold white] (Login and save session)")
    console.print("2. [bold white]Load Local Session[/bold white] (Uses Instaloader/ig-detective cookie file)")
    console.print("3. [bold white]Guest Mode[/bold white] (Anonymous, severe rate-limits)")
    console.print("4. [bold white]Exit[/bold white]")
    
    choice = input("\nEnter choice [1-4]: ").strip()
    
    if choice == '4':
        sys.exit(0)
        
    client = None
    if choice == '1':
        import getpass
        username = input("Enter Instagram Username: ").strip()
        password = getpass.getpass("Enter Instagram Password: ")
        console.print(f"[dim]Attempting authentication for {username}...[/dim]")
        try:
            SessionManager.perform_login(username, password)
            client = InstagramClient(username=username)
            if client.is_authenticated:
                console.print("[bold green]✅ Success: Logged in and session saved![/bold green]")
            else:
                console.print("[bold yellow]⚠️ Logged in, but session might be limited (No CSRF token found).[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to login: {e}[/bold red]")
            client = InstagramClient() # Fallback
            
    elif choice == '2':
        username = input("Enter the username of the saved session: ").strip()
        console.print(f"[dim]Attempting to load cookies for {username}...[/dim]")
        try:
            client = InstagramClient(username=username)
            if client.is_authenticated:
                console.print("[bold green]✅ Success: Session restored![/bold green]")
            else:
                console.print("[bold yellow]⚠️ Loaded, but session might be expired (No CSRF token found).[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to load session: {e}[/bold red]")
            client = InstagramClient() # Fallback to guest
    else:
        # Guest Mode
        client = InstagramClient() 

    # Launch CLI
    shell = IGDetectiveShell(client)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupt received, exiting.[/bold red]")
        
if __name__ == "__main__":
    boot()
