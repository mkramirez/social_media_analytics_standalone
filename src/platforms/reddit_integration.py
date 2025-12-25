"""
Reddit Integration

Simplified Reddit API integration for standalone version.
"""

import praw
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class RedditAPI:
    """Reddit API client."""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API client."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def get_subreddit_info(self, subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Get subreddit information."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                "name": subreddit.display_name,
                "subscribers": subreddit.subscribers,
                "description": subreddit.public_description
            }

        except Exception as e:
            st.error(f"Error fetching subreddit info: {e}")
            return None

    def get_subreddit_posts(self, subreddit_name: str, limit: int = 25, sort: str = "hot") -> List[Dict[str, Any]]:
        """Get posts from a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Get posts based on sort
            if sort == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort == "new":
                posts = subreddit.new(limit=limit)
            elif sort == "top":
                posts = subreddit.top(limit=limit, time_filter="day")
            else:
                posts = subreddit.hot(limit=limit)

            result = []
            for post in posts:
                result.append({
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author) if post.author else "[deleted]",
                    "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "upvote_ratio": post.upvote_ratio,
                    "url": post.url,
                    "is_self": post.is_self
                })

            return result

        except Exception as e:
            st.error(f"Error fetching posts: {e}")
            return []


class RedditDatabase:
    """Database operations for Reddit data."""

    def __init__(self, db):
        """Initialize with session database."""
        self.db = db

    def add_subreddit(self, subreddit_name: str) -> int:
        """Add a subreddit to monitor."""
        # Check if exists
        self.db.execute(
            "SELECT id FROM reddit_subreddits WHERE subreddit_name = ?",
            (subreddit_name,)
        )
        existing = self.db.fetchone()

        if existing:
            return existing['id']

        # Insert new
        self.db.execute(
            "INSERT INTO reddit_subreddits (subreddit_name) VALUES (?)",
            (subreddit_name,)
        )
        self.db.commit()

        return self.db.cursor.lastrowid

    def get_subreddit(self, subreddit_name: str) -> Optional[Dict]:
        """Get subreddit by name."""
        self.db.execute(
            "SELECT * FROM reddit_subreddits WHERE subreddit_name = ?",
            (subreddit_name,)
        )
        return self.db.fetchone()

    def get_all_subreddits(self) -> List[Dict]:
        """Get all subreddits."""
        self.db.execute(
            "SELECT * FROM reddit_subreddits ORDER BY added_at DESC"
        )
        return self.db.fetchall()

    def delete_subreddit(self, subreddit_id: int):
        """Delete a subreddit and all its posts."""
        self.db.execute(
            "DELETE FROM reddit_subreddits WHERE id = ?",
            (subreddit_id,)
        )
        self.db.commit()

    def add_post(
        self,
        subreddit_id: int,
        post_id: str,
        title: str,
        author: str,
        created_utc: str,
        score: int,
        num_comments: int,
        upvote_ratio: float
    ):
        """Add a post (or update if exists)."""
        # Check if post exists
        self.db.execute(
            "SELECT id FROM reddit_posts WHERE post_id = ?",
            (post_id,)
        )
        existing = self.db.fetchone()

        if existing:
            # Update metrics
            self.db.execute("""
                UPDATE reddit_posts
                SET score = ?, num_comments = ?, upvote_ratio = ?
                WHERE post_id = ?
            """, (score, num_comments, upvote_ratio, post_id))
        else:
            # Insert new
            self.db.execute("""
                INSERT INTO reddit_posts
                (subreddit_id, post_id, title, author, created_utc, score, num_comments, upvote_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (subreddit_id, post_id, title, author, created_utc, score, num_comments, upvote_ratio))

        self.db.commit()

    def get_posts(self, subreddit_id: int, limit: int = 100) -> List[Dict]:
        """Get posts for a subreddit."""
        self.db.execute("""
            SELECT * FROM reddit_posts
            WHERE subreddit_id = ?
            ORDER BY created_utc DESC
            LIMIT ?
        """, (subreddit_id, limit))
        return self.db.fetchall()

    def get_subreddit_statistics(self, subreddit_id: int) -> Dict[str, Any]:
        """Get statistics for a subreddit."""
        self.db.execute("""
            SELECT
                COUNT(*) as total_posts,
                SUM(score) as total_score,
                SUM(num_comments) as total_comments,
                AVG(score) as avg_score_per_post,
                AVG(upvote_ratio) as avg_upvote_ratio,
                MAX(score) as highest_score
            FROM reddit_posts
            WHERE subreddit_id = ?
        """, (subreddit_id,))

        return self.db.fetchone()

    def set_monitoring(self, subreddit_id: int, is_monitoring: bool):
        """Set monitoring status for a subreddit."""
        self.db.execute(
            "UPDATE reddit_subreddits SET is_monitoring = ? WHERE id = ?",
            (is_monitoring, subreddit_id)
        )
        self.db.commit()


def collect_reddit_data(subreddit_name: str, db, limit: int = 25, sort: str = "hot") -> bool:
    """
    Collect data for a Reddit subreddit.

    Args:
        subreddit_name: Subreddit name (without r/)
        db: Session database instance
        limit: Number of posts to fetch
        sort: Sort method (hot, new, top)

    Returns:
        bool: True if successful
    """
    from utils.credential_manager import CredentialManager

    # Get credentials
    creds = CredentialManager.get_reddit_credentials()
    if not creds:
        st.error("Reddit credentials not configured")
        return False

    try:
        # Initialize API
        api = RedditAPI(creds.client_id, creds.client_secret, creds.user_agent)
        db_helper = RedditDatabase(db)

        # Get or create subreddit
        subreddit = db_helper.get_subreddit(subreddit_name)
        if not subreddit:
            subreddit_id = db_helper.add_subreddit(subreddit_name)
        else:
            subreddit_id = subreddit['id']

        # Get posts
        posts = api.get_subreddit_posts(subreddit_name, limit=limit, sort=sort)

        # Store posts
        for post in posts:
            db_helper.add_post(
                subreddit_id=subreddit_id,
                post_id=post['id'],
                title=post['title'],
                author=post['author'],
                created_utc=post['created_utc'],
                score=post['score'],
                num_comments=post['num_comments'],
                upvote_ratio=post['upvote_ratio']
            )

        return True

    except Exception as e:
        st.error(f"Error collecting Reddit data: {e}")
        return False
