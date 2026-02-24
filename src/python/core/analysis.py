from collections import Counter
import re
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from datetime import datetime, timezone, timedelta
import nltk
from nltk.util import ngrams

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

    @staticmethod
    def find_location_intersections(locs1: list, locs2: list, time_delta_hours: int = 2) -> list[dict]:
        """
        Research-Driven OSINT: Geospatial Co-Visitation Analysis.
        Finds occurrences where two targets were at the same location within a time window.
        """
        intersections = []
        for l1 in locs1:
            for l2 in locs2:
                # Check for same GPS (with small float tolerance)
                if abs(l1['lat'] - l2['lat']) < 0.0001 and abs(l1['lng'] - l2['lng']) < 0.0001:
                    # Check temporal proximity
                    t1, t2 = l1['timestamp'], l2['timestamp']
                    if abs((t1 - t2).total_seconds()) <= (time_delta_hours * 3600):
                        intersections.append({
                            "location_name": l1['name'],
                            "lat": l1['lat'],
                            "lng": l1['lng'],
                            "t1": t1,
                            "t2": t2,
                            "time_diff_min": abs((t1 - t2).total_seconds()) / 60
                        })
        return intersections

    @staticmethod
    def get_linguistic_signature(posts: list) -> dict:
        """
        Research-Driven OSINT: Stylometry & Linguistic Profiling.
        Analyzes punctuation, emojis, and bigrams to create a digital fingerprint.
        """
        all_text = " ".join([p.caption for p in posts if p.caption])
        if not all_text:
            return {}

        # Emoji analysis
        emojis = re.findall(r'[^\w\s,.]', all_text)
        emoji_dist = Counter(emojis).most_common(10)

        # Punctuation styling
        punctuation = {
            "multiple_excl": len(re.findall(r'!!+', all_text)),
            "multiple_qmark": len(re.findall(r'\?\?+', all_text)),
            "ellipsis": len(re.findall(r'\.\.\.', all_text)),
            "all_caps_words": len(re.findall(r'\b[A-Z]{2,}\b', all_text))
        }

        # Bigram frequency (basic)
        words = re.findall(r'\b\w+\b', all_text.lower())
        bigrams = list(ngrams(words, 2))
        top_bigrams = Counter(bigrams).most_common(10)

        return {
            "top_emojis": emoji_dist,
            "punctuation_habits": punctuation,
            "top_bigrams": [f"{b[0]} {b[1]}" for b, count in top_bigrams],
            "lexical_diversity": len(set(words)) / len(words) if words else 0
        }

    @staticmethod
    def audit_engagement(comments: list[dict]) -> dict:
        """
        Research-Driven OSINT: Botnet & Inauthentic Engagement Audit.
        Analyzes comment timing and user quality.
        """
        if not comments:
            return {}

        df = pd.DataFrame(comments)
        df['created_at_utc'] = pd.to_datetime(df['created_at_utc'])
        
        # 1. Comment Jitter (Variance in timing)
        # Low variance in time differences suggests automated posting
        df = df.sort_values('created_at_utc')
        time_diffs = df['created_at_utc'].diff().dropna().dt.total_seconds()
        
        jitter_score = time_diffs.std() if len(time_diffs) > 1 else -1

        # 2. Duplicate Content
        text_counts = df['text'].value_counts()
        duplicate_ratio = (text_counts[text_counts > 1].sum() / len(df)) if len(df) > 0 else 0

        # Flagging
        is_suspicious = False
        reasons = []
        if jitter_score > 0 and jitter_score < 2: # Very low variance
            is_suspicious = True
            reasons.append("Ultra-low temporal variance (Bot-like precision)")
        if duplicate_ratio > 0.4:
            is_suspicious = True
            reasons.append("High content duplication")

        return {
            "total_comments_audited": len(comments),
            "temporal_variation_std": jitter_score,
            "duplicate_content_ratio": duplicate_ratio,
            "is_suspicious": is_suspicious,
            "flagged_reasons": reasons
        }
