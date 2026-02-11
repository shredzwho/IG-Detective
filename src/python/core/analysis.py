from collections import Counter
import re

class DataAnalyzer:
    @staticmethod
    def get_most_used_hashtags(posts: list, top_n: int = 10) -> list[tuple]:
        """Extract and count hashtags from a list of posts."""
        all_hashtags = []
        for post in posts:
            if post.caption:
                hashtags = re.findall(r"#(\w+)", post.caption)
                all_hashtags.extend(hashtags)
        
        return Counter(all_hashtags).most_common(top_n)

    @staticmethod
    def get_top_commenters(comments: list[dict], top_n: int = 10) -> list[tuple]:
        """Count comments per user."""
        commenters = [c['owner_username'] for c in comments]
        return Counter(commenters).most_common(top_n)

    @staticmethod
    def get_average_likes(posts: list) -> float:
        """Calculate average likes per post."""
        if not posts:
            return 0.0
        total_likes = sum(post.likes_count for post in posts)
        return total_likes / len(posts)
