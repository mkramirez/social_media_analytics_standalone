"""
YouTube Integration

Simplified YouTube API integration for standalone version.
"""

from googleapiclient.discovery import build
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class YouTubeAPI:
    """YouTube API client."""

    def __init__(self, api_key: str):
        """Initialize YouTube API client."""
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_channel_info(self, channel_id: str = None, username: str = None) -> Optional[Dict[str, Any]]:
        """Get channel information."""
        try:
            if channel_id:
                request = self.youtube.channels().list(
                    part="snippet,statistics",
                    id=channel_id
                )
            elif username:
                request = self.youtube.channels().list(
                    part="snippet,statistics",
                    forUsername=username
                )
            else:
                return None

            response = request.execute()

            if response['items']:
                channel = response['items'][0]
                return {
                    "id": channel['id'],
                    "title": channel['snippet']['title'],
                    "subscriber_count": int(channel['statistics'].get('subscriberCount', 0)),
                    "video_count": int(channel['statistics'].get('videoCount', 0)),
                    "view_count": int(channel['statistics'].get('viewCount', 0))
                }

            return None

        except Exception as e:
            st.error(f"Error fetching channel info: {e}")
            return None

    def search_channel(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a channel by name."""
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="channel",
                maxResults=1
            )

            response = request.execute()

            if response['items']:
                item = response['items'][0]
                channel_id = item['snippet']['channelId']
                return self.get_channel_info(channel_id=channel_id)

            return None

        except Exception as e:
            st.error(f"Error searching for channel: {e}")
            return None

    def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent videos from a channel."""
        try:
            # Get uploads playlist ID
            request = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            )
            response = request.execute()

            if not response['items']:
                return []

            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get videos from uploads playlist
            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            response = request.execute()

            video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]

            if not video_ids:
                return []

            # Get video statistics
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=','.join(video_ids)
            )
            response = request.execute()

            result = []
            for video in response['items']:
                stats = video['statistics']
                result.append({
                    "id": video['id'],
                    "title": video['snippet']['title'],
                    "published_at": video['snippet']['publishedAt'],
                    "view_count": int(stats.get('viewCount', 0)),
                    "like_count": int(stats.get('likeCount', 0)),
                    "comment_count": int(stats.get('commentCount', 0))
                })

            return result

        except Exception as e:
            st.error(f"Error fetching videos: {e}")
            return []


class YouTubeDatabase:
    """Database operations for YouTube data."""

    def __init__(self, db):
        """Initialize with session database."""
        self.db = db

    def add_channel(self, channel_id: str, channel_name: str) -> int:
        """Add a channel to monitor."""
        # Check if exists
        self.db.execute(
            "SELECT id FROM youtube_channels WHERE channel_id = ?",
            (channel_id,)
        )
        existing = self.db.fetchone()

        if existing:
            return existing['id']

        # Insert new
        self.db.execute(
            "INSERT INTO youtube_channels (channel_id, channel_name) VALUES (?, ?)",
            (channel_id, channel_name)
        )
        self.db.commit()

        return self.db.cursor.lastrowid

    def get_channel(self, channel_id: str) -> Optional[Dict]:
        """Get channel by ID."""
        self.db.execute(
            "SELECT * FROM youtube_channels WHERE channel_id = ?",
            (channel_id,)
        )
        return self.db.fetchone()

    def get_all_channels(self) -> List[Dict]:
        """Get all channels."""
        self.db.execute(
            "SELECT * FROM youtube_channels ORDER BY added_at DESC"
        )
        return self.db.fetchall()

    def delete_channel(self, db_channel_id: int):
        """Delete a channel and all its videos."""
        self.db.execute(
            "DELETE FROM youtube_channels WHERE id = ?",
            (db_channel_id,)
        )
        self.db.commit()

    def add_video(
        self,
        channel_id: int,
        video_id: str,
        title: str,
        published_at: str,
        view_count: int,
        like_count: int,
        comment_count: int
    ):
        """Add a video (or update if exists)."""
        # Check if video exists
        self.db.execute(
            "SELECT id FROM youtube_videos WHERE video_id = ?",
            (video_id,)
        )
        existing = self.db.fetchone()

        if existing:
            # Update metrics
            self.db.execute("""
                UPDATE youtube_videos
                SET view_count = ?, like_count = ?, comment_count = ?
                WHERE video_id = ?
            """, (view_count, like_count, comment_count, video_id))
        else:
            # Insert new
            self.db.execute("""
                INSERT INTO youtube_videos
                (channel_id, video_id, title, published_at, view_count, like_count, comment_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, video_id, title, published_at, view_count, like_count, comment_count))

        self.db.commit()

    def get_videos(self, channel_id: int, limit: int = 100) -> List[Dict]:
        """Get videos for a channel."""
        self.db.execute("""
            SELECT * FROM youtube_videos
            WHERE channel_id = ?
            ORDER BY published_at DESC
            LIMIT ?
        """, (channel_id, limit))
        return self.db.fetchall()

    def get_channel_statistics(self, channel_id: int) -> Dict[str, Any]:
        """Get statistics for a channel."""
        self.db.execute("""
            SELECT
                COUNT(*) as total_videos,
                SUM(view_count) as total_views,
                SUM(like_count) as total_likes,
                SUM(comment_count) as total_comments,
                AVG(view_count) as avg_views_per_video,
                MAX(view_count) as most_viewed_count
            FROM youtube_videos
            WHERE channel_id = ?
        """, (channel_id,))

        return self.db.fetchone()

    def set_monitoring(self, channel_id: int, is_monitoring: bool):
        """Set monitoring status for a channel."""
        self.db.execute(
            "UPDATE youtube_channels SET is_monitoring = ? WHERE id = ?",
            (is_monitoring, channel_id)
        )
        self.db.commit()


def collect_youtube_data(channel_query: str, db, is_channel_id: bool = False) -> bool:
    """
    Collect data for a YouTube channel.

    Args:
        channel_query: Channel ID or name to search
        db: Session database instance
        is_channel_id: Whether query is a channel ID or name

    Returns:
        bool: True if successful
    """
    from utils.credential_manager import CredentialManager

    # Get credentials
    creds = CredentialManager.get_youtube_credentials()
    if not creds:
        st.error("YouTube credentials not configured")
        return False

    try:
        # Initialize API
        api = YouTubeAPI(creds.api_key)
        db_helper = YouTubeDatabase(db)

        # Get channel info
        if is_channel_id:
            channel_info = api.get_channel_info(channel_id=channel_query)
        else:
            channel_info = api.search_channel(channel_query)

        if not channel_info:
            st.error("Channel not found")
            return False

        # Get or create channel
        channel = db_helper.get_channel(channel_info['id'])
        if not channel:
            db_channel_id = db_helper.add_channel(channel_info['id'], channel_info['title'])
        else:
            db_channel_id = channel['id']

        # Get videos
        videos = api.get_channel_videos(channel_info['id'], max_results=10)

        # Store videos
        for video in videos:
            db_helper.add_video(
                channel_id=db_channel_id,
                video_id=video['id'],
                title=video['title'],
                published_at=video['published_at'],
                view_count=video['view_count'],
                like_count=video['like_count'],
                comment_count=video['comment_count']
            )

        return True

    except Exception as e:
        st.error(f"Error collecting YouTube data: {e}")
        return False
