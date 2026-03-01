import sqlite3
import datetime
from src.core.models import User
from src.core.config import settings

class SurveillanceEngine:
    """Manages the persistence and delta tracking for target surveillance."""
    
    def __init__(self):
        import os
        self.db_path = os.path.join(settings.SESSION_DIR, "surveillance.db")
        self._init_db()
        
    def _init_db(self):
        """Initializes the SQLite schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    follower_count INTEGER,
                    following_count INTEGER,
                    mediacount INTEGER,
                    biography TEXT
                )
            ''')
            conn.commit()

    def _get_last_snapshot(self, username: str) -> dict:
        """Retrieves the most recent data snapshot for a given target."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM target_snapshots
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def save_snapshot(self, user: User):
        """Saves current metrics as a new snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO target_snapshots (username, follower_count, following_count, mediacount, biography)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.username, user.follower_count, user.following_count, getattr(user, 'mediacount', 0), user.biography))
            conn.commit()

    def compare_and_log(self, new_user: User) -> list:
        """Compares the current user properties to the last snapshot. Returns a list of delta messages."""
        last_snap = self._get_last_snapshot(new_user.username)
        
        # If no prior snapshot, consider this the baseline
        if not last_snap:
            self.save_snapshot(new_user)
            return ["Baseline snapshot established. Commencing active polling..."]
            
        deltas = []
        
        # Check Follower fluctuations
        if new_user.follower_count != last_snap['follower_count']:
            diff = new_user.follower_count - last_snap['follower_count']
            sign = "+" if diff > 0 else "-"
            deltas.append(f"Follower Count Changed: {last_snap['follower_count']} -> {new_user.follower_count} ({sign}{abs(diff)})")
            
        # Check Following fluctuations 
        if new_user.following_count != last_snap['following_count']:
            diff = new_user.following_count - last_snap['following_count']
            sign = "+" if diff > 0 else "-"
            deltas.append(f"Following Count Changed: {last_snap['following_count']} -> {new_user.following_count} ({sign}{abs(diff)})")
            
        # Check Media/Post fluctuations
        new_media = getattr(new_user, 'mediacount', 0)
        old_media = last_snap.get('mediacount', 0)
        if new_media != old_media:
            diff = new_media - old_media
            if diff > 0:
                deltas.append(f"Target Uploaded Media! (+{diff} posts)")
            else:
                deltas.append(f"Target Deleted Media! (-{abs(diff)} posts)")

        # Check Biography edits
        if new_user.biography != last_snap['biography']:
            deltas.append(f"Bio Edited: '{last_snap['biography']}' -> '{new_user.biography}'")

        # Only save a new snapshot if something actually changed
        if deltas:
            self.save_snapshot(new_user)
            
        return deltas
