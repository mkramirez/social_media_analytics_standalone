"""
Twitch Integration

Simplified Twitch API integration for standalone version.
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class TwitchAPI:
    """Twitch API client."""

    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(self, client_id: str, client_secret: str):
        """Initialize Twitch API client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        """Get OAuth access token."""
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        response = requests.post(url, params=params)
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username."""
        url = f"{self.BASE_URL}/users"
        params = {"login": username}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            if data["data"]:
                return data["data"][0]
            return None

        except Exception as e:
            st.error(f"Error fetching user info: {e}")
            return None

    def get_stream_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get current stream information."""
        # First get user ID
        user_info = self.get_user_info(username)
        if not user_info:
            return None

        user_id = user_info["id"]

        # Get stream info
        url = f"{self.BASE_URL}/streams"
        params = {"user_id": user_id}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()

            if data["data"]:
                # Stream is live
                stream = data["data"][0]
                return {
                    "is_live": True,
                    "title": stream.get("title"),
                    "game_name": stream.get("game_name"),
                    "viewer_count": stream.get("viewer_count", 0),
                    "started_at": stream.get("started_at"),
                    "username": username,
                    "user_id": user_id
                }
            else:
                # Stream is offline
                return {
                    "is_live": False,
                    "title": None,
                    "game_name": None,
                    "viewer_count": 0,
                    "started_at": None,
                    "username": username,
                    "user_id": user_id
                }

        except Exception as e:
            st.error(f"Error fetching stream info: {e}")
            return None


class TwitchDatabase:
    """Database operations for Twitch data."""

    def __init__(self, db):
        """Initialize with session database."""
        self.db = db

    def add_channel(self, channel_name: str) -> int:
        """Add a channel to monitor."""
        # Check if exists
        self.db.execute(
            "SELECT id FROM twitch_channels WHERE channel_name = ?",
            (channel_name,)
        )
        existing = self.db.fetchone()

        if existing:
            return existing['id']

        # Insert new
        self.db.execute(
            "INSERT INTO twitch_channels (channel_name) VALUES (?)",
            (channel_name,)
        )
        self.db.commit()

        return self.db.cursor.lastrowid

    def get_channel(self, channel_name: str) -> Optional[Dict]:
        """Get channel by name."""
        self.db.execute(
            "SELECT * FROM twitch_channels WHERE channel_name = ?",
            (channel_name,)
        )
        return self.db.fetchone()

    def get_all_channels(self) -> List[Dict]:
        """Get all channels."""
        self.db.execute(
            "SELECT * FROM twitch_channels ORDER BY added_at DESC"
        )
        return self.db.fetchall()

    def delete_channel(self, channel_id: int):
        """Delete a channel and all its records."""
        self.db.execute(
            "DELETE FROM twitch_channels WHERE id = ?",
            (channel_id,)
        )
        self.db.commit()

    def add_stream_record(
        self,
        channel_id: int,
        is_live: bool,
        title: str = None,
        game_name: str = None,
        viewer_count: int = 0,
        started_at: str = None
    ):
        """Add a stream record."""
        self.db.execute("""
            INSERT INTO twitch_stream_records
            (channel_id, is_live, title, game_name, viewer_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (channel_id, is_live, title, game_name, viewer_count, started_at))
        self.db.commit()

    def get_stream_records(
        self,
        channel_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """Get stream records for a channel."""
        self.db.execute("""
            SELECT * FROM twitch_stream_records
            WHERE channel_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (channel_id, limit))
        return self.db.fetchall()

    def get_latest_record(self, channel_id: int) -> Optional[Dict]:
        """Get the latest record for a channel."""
        self.db.execute("""
            SELECT * FROM twitch_stream_records
            WHERE channel_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (channel_id,))
        return self.db.fetchone()

    def get_channel_statistics(self, channel_id: int) -> Dict[str, Any]:
        """Get statistics for a channel."""
        self.db.execute("""
            SELECT
                COUNT(*) as total_records,
                SUM(CASE WHEN is_live = 1 THEN 1 ELSE 0 END) as live_count,
                AVG(CASE WHEN is_live = 1 THEN viewer_count ELSE 0 END) as avg_viewers,
                MAX(viewer_count) as peak_viewers,
                MIN(timestamp) as first_record,
                MAX(timestamp) as last_record
            FROM twitch_stream_records
            WHERE channel_id = ?
        """, (channel_id,))

        return self.db.fetchone()

    def set_monitoring(self, channel_id: int, is_monitoring: bool):
        """Set monitoring status for a channel."""
        self.db.execute(
            "UPDATE twitch_channels SET is_monitoring = ? WHERE id = ?",
            (is_monitoring, channel_id)
        )
        self.db.commit()


def collect_twitch_data(channel_name: str, db) -> bool:
    """
    Collect data for a Twitch channel.

    Args:
        channel_name: Channel username
        db: Session database instance

    Returns:
        bool: True if successful
    """
    from utils.credential_manager import CredentialManager

    # Get credentials
    creds = CredentialManager.get_twitch_credentials()
    if not creds:
        st.error("Twitch credentials not configured")
        return False

    try:
        # Initialize API
        api = TwitchAPI(creds.client_id, creds.client_secret)
        db_helper = TwitchDatabase(db)

        # Get stream info
        stream_info = api.get_stream_info(channel_name)
        if not stream_info:
            return False

        # Get or create channel
        channel = db_helper.get_channel(channel_name)
        if not channel:
            channel_id = db_helper.add_channel(channel_name)
        else:
            channel_id = channel['id']

        # Add record
        db_helper.add_stream_record(
            channel_id=channel_id,
            is_live=stream_info['is_live'],
            title=stream_info.get('title'),
            game_name=stream_info.get('game_name'),
            viewer_count=stream_info.get('viewer_count', 0),
            started_at=stream_info.get('started_at')
        )

        return True

    except Exception as e:
        st.error(f"Error collecting Twitch data: {e}")
        return False
