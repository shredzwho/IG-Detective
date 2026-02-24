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
    def get_aggregate_stats(posts: list) -> dict:
        """Calculate aggregate statistics for a set of posts."""
        if not posts:
            return {}
        
        total_posts = len(posts)
        total_likes = sum(post.likes_count for post in posts)
        total_comments = sum(post.comments_count for post in posts)
        
        photos = sum(1 for post in posts if not post.is_video)
        videos = sum(1 for post in posts if post.is_video)
        
        return {
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_likes": total_likes / total_posts if total_posts > 0 else 0,
            "avg_comments": total_comments / total_posts if total_posts > 0 else 0,
            "photo_count": photos,
            "video_count": videos,
            "photo_ratio": photos / total_posts if total_posts > 0 else 0,
            "video_ratio": videos / total_posts if total_posts > 0 else 0
        }
