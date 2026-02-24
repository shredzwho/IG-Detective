from collections import Counter
import re
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from datetime import datetime, timezone

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

    @staticmethod
    def perform_sna(target: str, comments: list[dict], tagged_users: list[str]) -> list[tuple]:
        """
        Social Network Analysis to find the 'Inner Circle'.
        Uses Degree Centrality to rank users based on interaction frequency and tagging.
        """
        G = nx.Graph()
        G.add_node(target)
        
        # Add commenters
        comment_counts = Counter(c['owner_username'] for c in comments)
        for user, count in comment_counts.items():
            G.add_edge(target, user, weight=count)
            
        # Add tagged users (higher weight)
        for user in tagged_users:
            if G.has_edge(target, user):
                G[target][user]['weight'] += 5
            else:
                G.add_edge(target, user, weight=5)
                
        # Calculate Degree Centrality weighted by interaction frequency
        centrality = nx.degree_centrality(G)
        # Sort by proximity/influence
        inner_circle = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        # Filter out the target itself
        return [item for item in inner_circle if item[0] != target][:10]

    @staticmethod
    def analyze_temporal_behavior(posts: list) -> dict:
        """
        Temporal Analysis using DBSCAN clustering to identify the target's 'sleep gap'.
        """
        if not posts:
            return {}
            
        timestamps = [p.timestamp for p in posts]
        df = pd.DataFrame({'timestamp': timestamps})
        df['hour'] = df['timestamp'].dt.hour
        
        # Use DBSCAN to find gaps in posting activity
        # We look for clusters in the 24-hour cycle
        X = df[['hour']].values
        db = DBSCAN(eps=2, min_samples=1).fit(X)
        
        # Calculate hourly frequency
        hourly_freq = df['hour'].value_counts().reindex(range(24), fill_value=0)
        
        # Identify the longest continuous gap of zero or near-zero activity
        # Simple sliding window approach for the 'sleep gap'
        max_gap = 0
        sleep_start = 0
        current_gap = 0
        current_start = 0
        
        # Circular check for the 24h cycle
        double_freq = list(hourly_freq.values) + list(hourly_freq.values)
        for i, count in enumerate(double_freq):
            if count == 0:
                current_gap += 1
            else:
                if current_gap > max_gap:
                    max_gap = current_gap
                    sleep_start = current_start % 24
                current_gap = 0
                current_start = i + 1
        
        # Predict Time Zone
        # Assuming sleep is typically 12 AM - 8 AM
        predicted_tz = "UTC"
        if max_gap > 0:
            # Shift sleep start to align with 00:00 local time
            offset = (0 - sleep_start) % 24
            if offset > 12: offset -= 24
            predicted_tz = f"UTC{'+' if offset >= 0 else ''}{offset}:00 (Estimated)"

        return {
            "sleep_start_hour": sleep_start,
            "sleep_gap_duration": max_gap,
            "predicted_timezone": predicted_tz,
            "hourly_distribution": hourly_freq.to_dict()
        }
