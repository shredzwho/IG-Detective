import click
from src.python.core.scraper import InstagramScraper

@click.group()
def cli():
    """IG-Detective CLI"""
    pass

@cli.command()
@click.argument('username')
def profile(username):
    """Fetch profile information for a given username."""
    click.echo(f"Fetching profile for {username}...")
    scraper = InstagramScraper()
    user = scraper.get_profile(username)
    if user:
        click.echo(f"Username: {user.username}")
        click.echo(f"Name: {user.full_name}")
        click.echo(f"Bio: {user.biography}")
        click.echo(f"Followers: {user.follower_count}")
        click.echo(f"Following: {user.following_count}")
        click.echo(f"Verified: {user.is_verified}")
        click.echo(f"Private: {user.is_private}")

@cli.command()
@click.argument('username')
def posts(username):
    """Fetch recent posts for a given username."""
    click.echo(f"Fetching posts for {username}...")
    scraper = InstagramScraper()
    posts = scraper.get_posts(username)
    for post in posts:
        click.echo("-" * 20)
        click.echo(f"ID: {post.id}")
        click.echo(f"Caption: {post.caption}")
        click.echo(f"Likes: {post.likes_count}")
        click.echo(f"Comments: {post.comments_count}")
        click.echo(f"Is Video: {post.is_video}")

if __name__ == '__main__':
    cli()
