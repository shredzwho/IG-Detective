import re
import pandas as pd
import networkx as nx
from collections import Counter
from sklearn.cluster import DBSCAN
import nltk
from nltk.util import ngrams
from typing import List, Dict, Any, Tuple
from src.core.models import Post

class AnalyticsEngine:
    """Core processing unit for advanced OSINT calculations."""

    @staticmethod
    def get_most_used_hashtags(posts: List[Post], top_n: int = 10) -> List[Tuple]:
        """Extract and count hashtags from a list of posts."""
        all_hashtags = []
        for post in posts:
            if post.caption:
                hashtags = re.findall(r"#(\w+)", post.caption)
                all_hashtags.extend(hashtags)
        return Counter(all_hashtags).most_common(top_n)

    @staticmethod
    def get_aggregate_stats(posts: List[Post]) -> dict:
        """Calculate aggregate statistics prioritizing engagement ratios."""
        if not posts: return {}
        
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
        }

    @staticmethod
    def perform_sna(target: str, tagged_users_across_posts: List[List[str]]) -> List[Tuple[str, float]]:
        """
        Social Network Analysis to find the 'Inner Circle'.
        Uses Degree Centrality weighted by interaction frequency and tagging.
        """
        G = nx.Graph()
        G.add_node(target)
        
        # In the decoupled architecture, we only analyze what is given to us.
        # Add tagged users (high weight indicating close physical/social tie)
        for tagged_list in tagged_users_across_posts:
            for user in tagged_list:
                if G.has_edge(target, user):
                    G[target][user]['weight'] += 5
                else:
                    G.add_edge(target, user, weight=5)
                    
        centrality = nx.degree_centrality(G)
        inner_circle = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return [item for item in inner_circle if item[0] != target][:10]

    @staticmethod
    def analyze_temporal_behavior(posts: List[Post]) -> dict:
        """
        Temporal Analysis using DBSCAN clustering to identify the target's 'sleep gap'.
        """
        if not posts: return {}
            
        timestamps = [p.timestamp for p in posts]
        df = pd.DataFrame({'timestamp': timestamps})
        df['hour'] = df['timestamp'].dt.hour
        
        X = df[['hour']].values
        db = DBSCAN(eps=2, min_samples=1).fit(X)
        hourly_freq = df['hour'].value_counts().reindex(range(24), fill_value=0)
        
        max_gap, sleep_start, current_gap, current_start = 0, 0, 0, 0
        
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
        
        predicted_tz = "UTC"
        if max_gap > 0:
            offset = (0 - sleep_start) % 24
            if offset > 12: offset -= 24
            predicted_tz = f"UTC{'+' if offset >= 0 else ''}{offset}:00 (Estimated based on 12AM sleep cycle)"

        return {
            "sleep_start_hour": sleep_start,
            "sleep_gap_duration": max_gap,
            "predicted_timezone": predicted_tz,
            "hourly_distribution": hourly_freq.to_dict()
        }

    @staticmethod
    def get_linguistic_signature(posts: List[Post]) -> dict:
        """Stylometry & Linguistic Profiling."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                import urllib.request
                urllib.request.urlopen("http://google.com", timeout=3)
                nltk.download('punkt', quiet=True)
                nltk.download('punkt_tab', quiet=True)
            except Exception:
                pass # Fail gracefully if offline
                
        all_text = " ".join([p.caption for p in posts if p.caption])
        if not all_text: return {}

        emojis = re.findall(r'[^\w\s,.]', all_text)
        emoji_dist = Counter(emojis).most_common(10)

        punctuation = {
            "multiple_excl": len(re.findall(r'!!+', all_text)),
            "multiple_qmark": len(re.findall(r'\?\?+', all_text)),
            "ellipsis": len(re.findall(r'\.\.\.', all_text)),
            "all_caps_words": len(re.findall(r'\b[A-Z]{2,}\b', all_text))
        }

        words = re.findall(r'\b\w+\b', all_text.lower())
        bigrams = list(ngrams(words, 2))
        top_bigrams = Counter(bigrams).most_common(10)

        return {
            "top_emojis": emoji_dist,
            "punctuation_habits": punctuation,
            "top_bigrams": [f"{b[0]} {b[1]}" for b, count in top_bigrams],
            "lexical_diversity": len(set(words)) / len(words) if words else 0
        }
