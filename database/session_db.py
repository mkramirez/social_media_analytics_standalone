"""
Session Database Manager

Manages an in-memory SQLite database for the current Streamlit session.
All data is lost when the browser session ends.
"""

import sqlite3
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime
import io


class SessionDatabase:
    """Manages in-memory SQLite database for current session."""

    def __init__(self):
        """Initialize in-memory database connection."""
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create all necessary database tables."""

        # Twitch tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitch_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_monitoring BOOLEAN DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitch_stream_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_live BOOLEAN,
                title TEXT,
                game_name TEXT,
                viewer_count INTEGER,
                started_at TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES twitch_channels(id) ON DELETE CASCADE
            )
        """)

        # Twitter tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitter_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_monitoring BOOLEAN DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitter_tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tweet_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP,
                text TEXT,
                retweet_count INTEGER,
                like_count INTEGER,
                reply_count INTEGER,
                quote_count INTEGER,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES twitter_users(id) ON DELETE CASCADE
            )
        """)

        # YouTube tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_monitoring BOOLEAN DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                video_id TEXT UNIQUE NOT NULL,
                title TEXT,
                published_at TIMESTAMP,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES youtube_channels(id) ON DELETE CASCADE
            )
        """)

        # Reddit tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_subreddits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit_name TEXT UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_monitoring BOOLEAN DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit_id INTEGER NOT NULL,
                post_id TEXT UNIQUE NOT NULL,
                title TEXT,
                author TEXT,
                created_utc TIMESTAMP,
                score INTEGER,
                num_comments INTEGER,
                upvote_ratio REAL,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subreddit_id) REFERENCES reddit_subreddits(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query."""
        return self.cursor.execute(query, params)

    def fetchone(self) -> Optional[Dict]:
        """Fetch one row as dictionary."""
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self) -> List[Dict]:
        """Fetch all rows as list of dictionaries."""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self):
        """Commit transaction."""
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def export_to_file(self) -> bytes:
        """
        Export entire database to a downloadable .db file.

        Returns:
            bytes: Database file as bytes
        """
        # Create a temporary in-memory file
        temp_file = io.BytesIO()

        # Backup current database to temp file
        temp_conn = sqlite3.connect(':memory:')

        # Copy all data
        for line in self.conn.iterdump():
            temp_conn.execute(line)

        temp_conn.commit()

        # Write to bytes
        with sqlite3.connect(':memory:') as disk_conn:
            for line in self.conn.iterdump():
                disk_conn.execute(line)
            disk_conn.commit()

            # Serialize to bytes
            temp_db = sqlite3.connect(':memory:')
            for line in disk_conn.iterdump():
                temp_db.execute(line)

            # Get the database as bytes
            query = "SELECT * FROM sqlite_master"

        # Alternative: Use backup API
        backup_conn = sqlite3.connect(':memory:')
        self.conn.backup(backup_conn)

        # Convert to bytes
        temp_path = io.BytesIO()

        # Write using backup
        with sqlite3.connect(':memory:') as backup_db:
            self.conn.backup(backup_db)
            backup_db.commit()

            # Get SQL dump as string
            sql_dump = ""
            for line in backup_db.iterdump():
                sql_dump += f"{line}\n"

        return sql_dump.encode('utf-8')

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        # Twitch
        self.execute("SELECT COUNT(*) as count FROM twitch_channels")
        stats['twitch_channels'] = self.fetchone()['count']

        self.execute("SELECT COUNT(*) as count FROM twitch_stream_records")
        stats['twitch_records'] = self.fetchone()['count']

        # Twitter
        self.execute("SELECT COUNT(*) as count FROM twitter_users")
        stats['twitter_users'] = self.fetchone()['count']

        self.execute("SELECT COUNT(*) as count FROM twitter_tweets")
        stats['twitter_tweets'] = self.fetchone()['count']

        # YouTube
        self.execute("SELECT COUNT(*) as count FROM youtube_channels")
        stats['youtube_channels'] = self.fetchone()['count']

        self.execute("SELECT COUNT(*) as count FROM youtube_videos")
        stats['youtube_videos'] = self.fetchone()['count']

        # Reddit
        self.execute("SELECT COUNT(*) as count FROM reddit_subreddits")
        stats['reddit_subreddits'] = self.fetchone()['count']

        self.execute("SELECT COUNT(*) as count FROM reddit_posts")
        stats['reddit_posts'] = self.fetchone()['count']

        return stats


def get_session_db() -> SessionDatabase:
    """
    Get or create session database.

    Stores database in Streamlit session state so it persists
    across reruns within the same browser session.
    """
    if 'database' not in st.session_state:
        st.session_state.database = SessionDatabase()

    return st.session_state.database


def reset_session_db():
    """Reset the session database (clear all data)."""
    if 'database' in st.session_state:
        st.session_state.database.close()
        del st.session_state.database

    # Create new database
    st.session_state.database = SessionDatabase()
