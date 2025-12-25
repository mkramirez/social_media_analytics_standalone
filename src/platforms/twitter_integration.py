"""
Twitter Integration

Simplified Twitter API integration for standalone version.
"""

import tweepy
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class TwitterAPI:
    """Twitter API client."""

    def __init__(self, bearer_token: str):
        """Initialize Twitter API client."""
        self.client = tweepy.Client(bearer_token=bearer_token)

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        try:
            user = self.client.get_user(username=username)
            if user.data:
                return {
                    "id": user.data.id,
                    "username": user.data.username,
                    "name": user.data.name
                }
            return None

        except Exception as e:
            st.error(f"Error fetching user info: {e}")
            return None

    def get_user_tweets(self, username: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent tweets from a user."""
        try:
            # Get user ID first
            user_info = self.get_user_info(username)
            if not user_info:
                return []

            user_id = user_info["id"]

            # Get tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics"],
                exclude=["retweets", "replies"]
            )

            if not tweets.data:
                return []

            result = []
            for tweet in tweets.data:
                metrics = tweet.public_metrics
                result.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "retweet_count": metrics.get("retweet_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "quote_count": metrics.get("quote_count", 0)
                })

            return result

        except Exception as e:
            st.error(f"Error fetching tweets: {e}")
            return []


class TwitterDatabase:
    """Database operations for Twitter data."""

    def __init__(self, db):
        """Initialize with session database."""
        self.db = db

    def add_user(self, username: str) -> int:
        """Add a user to monitor."""
        # Check if exists
        self.db.execute(
            "SELECT id FROM twitter_users WHERE username = ?",
            (username,)
        )
        existing = self.db.fetchone()

        if existing:
            return existing['id']

        # Insert new
        self.db.execute(
            "INSERT INTO twitter_users (username) VALUES (?)",
            (username,)
        )
        self.db.commit()

        return self.db.cursor.lastrowid

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        self.db.execute(
            "SELECT * FROM twitter_users WHERE username = ?",
            (username,)
        )
        return self.db.fetchone()

    def get_all_users(self) -> List[Dict]:
        """Get all users."""
        self.db.execute(
            "SELECT * FROM twitter_users ORDER BY added_at DESC"
        )
        return self.db.fetchall()

    def delete_user(self, user_id: int):
        """Delete a user and all their tweets."""
        self.db.execute(
            "DELETE FROM twitter_users WHERE id = ?",
            (user_id,)
        )
        self.db.commit()

    def add_tweet(
        self,
        user_id: int,
        tweet_id: str,
        created_at: str,
        text: str,
        retweet_count: int,
        like_count: int,
        reply_count: int,
        quote_count: int
    ):
        """Add a tweet (or update if exists)."""
        # Check if tweet exists
        self.db.execute(
            "SELECT id FROM twitter_tweets WHERE tweet_id = ?",
            (tweet_id,)
        )
        existing = self.db.fetchone()

        if existing:
            # Update metrics
            self.db.execute("""
                UPDATE twitter_tweets
                SET retweet_count = ?, like_count = ?, reply_count = ?, quote_count = ?
                WHERE tweet_id = ?
            """, (retweet_count, like_count, reply_count, quote_count, tweet_id))
        else:
            # Insert new
            self.db.execute("""
                INSERT INTO twitter_tweets
                (user_id, tweet_id, created_at, text, retweet_count, like_count, reply_count, quote_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, tweet_id, created_at, text, retweet_count, like_count, reply_count, quote_count))

        self.db.commit()

    def get_tweets(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get tweets for a user."""
        self.db.execute("""
            SELECT * FROM twitter_tweets
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        return self.db.fetchall()

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a user."""
        self.db.execute("""
            SELECT
                COUNT(*) as total_tweets,
                SUM(retweet_count) as total_retweets,
                SUM(like_count) as total_likes,
                SUM(reply_count) as total_replies,
                AVG(like_count) as avg_likes_per_tweet,
                MAX(like_count) as most_liked_count
            FROM twitter_tweets
            WHERE user_id = ?
        """, (user_id,))

        return self.db.fetchone()

    def set_monitoring(self, user_id: int, is_monitoring: bool):
        """Set monitoring status for a user."""
        self.db.execute(
            "UPDATE twitter_users SET is_monitoring = ? WHERE id = ?",
            (is_monitoring, user_id)
        )
        self.db.commit()


def collect_twitter_data(username: str, db) -> bool:
    """
    Collect data for a Twitter user.

    Args:
        username: Twitter username
        db: Session database instance

    Returns:
        bool: True if successful
    """
    from utils.credential_manager import CredentialManager

    # Get credentials
    creds = CredentialManager.get_twitter_credentials()
    if not creds:
        st.error("Twitter credentials not configured")
        return False

    try:
        # Initialize API
        api = TwitterAPI(creds.bearer_token)
        db_helper = TwitterDatabase(db)

        # Get or create user
        user = db_helper.get_user(username)
        if not user:
            user_id = db_helper.add_user(username)
        else:
            user_id = user['id']

        # Get tweets
        tweets = api.get_user_tweets(username, max_results=10)

        # Store tweets
        for tweet in tweets:
            db_helper.add_tweet(
                user_id=user_id,
                tweet_id=str(tweet['id']),
                created_at=tweet['created_at'],
                text=tweet['text'],
                retweet_count=tweet['retweet_count'],
                like_count=tweet['like_count'],
                reply_count=tweet['reply_count'],
                quote_count=tweet['quote_count']
            )

        return True

    except Exception as e:
        st.error(f"Error collecting Twitter data: {e}")
        return False
