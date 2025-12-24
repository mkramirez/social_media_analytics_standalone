"""
Enhanced Twitch Integration

Includes chat message collection via IRC.
"""

import requests
import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class TwitchIRCClient:
    """Twitch IRC client for collecting chat messages."""

    def __init__(self, channel: str, oauth_token: str):
        """Initialize IRC client."""
        self.channel = channel.lower()
        self.oauth_token = oauth_token
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.nickname = "justinfan12345"  # Anonymous user
        self.sock = None
        self.running = False
        self.messages = []
        self.message_count = 0

    def connect(self):
        """Connect to Twitch IRC."""
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))

        # Authenticate
        self.sock.send(f"PASS oauth:{self.oauth_token}\r\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
        self.sock.send(f"JOIN #{self.channel}\r\n".encode('utf-8'))

        self.running = True

    def collect_messages(self, duration_seconds: int = 60):
        """Collect messages for a specified duration."""
        if not self.sock:
            self.connect()

        start_time = time.time()

        while time.time() - start_time < duration_seconds and self.running:
            try:
                response = self.sock.recv(2048).decode('utf-8', errors='ignore')

                # Handle PING/PONG
                if response.startswith('PING'):
                    self.sock.send("PONG\r\n".encode('utf-8'))
                    continue

                # Parse messages
                for line in response.split('\r\n'):
                    if 'PRIVMSG' in line:
                        self.message_count += 1

                        # Parse username and message
                        try:
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                username = parts[1].split('!')[0]
                                message = parts[2]

                                self.messages.append({
                                    'username': username,
                                    'message': message,
                                    'timestamp': datetime.now().isoformat()
                                })
                        except:
                            pass

            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error collecting messages: {e}")
                break

        return {
            'message_count': self.message_count,
            'messages': self.messages
        }

    def disconnect(self):
        """Disconnect from IRC."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass


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
            return None

    def get_stream_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get current stream information."""
        user_info = self.get_user_info(username)
        if not user_info:
            return None

        user_id = user_info["id"]
        url = f"{self.BASE_URL}/streams"
        params = {"user_id": user_id}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()

            if data["data"]:
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
            return None


class TwitchDatabase:
    """Database operations for Twitch data."""

    def __init__(self, db):
        """Initialize with session database."""
        self.db = db
        self._ensure_chat_table()

    def _ensure_chat_table(self):
        """Ensure chat messages table exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS twitch_chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (record_id) REFERENCES twitch_stream_records(id) ON DELETE CASCADE
            )
        """)

        # Add chat_message_count column if it doesn't exist
        try:
            self.db.execute("""
                ALTER TABLE twitch_stream_records
                ADD COLUMN chat_message_count INTEGER DEFAULT 0
            """)
            self.db.commit()
        except:
            pass  # Column already exists

    def add_channel(self, channel_name: str) -> int:
        """Add a channel to monitor."""
        self.db.execute(
            "SELECT id FROM twitch_channels WHERE channel_name = ?",
            (channel_name,)
        )
        existing = self.db.fetchone()

        if existing:
            return existing['id']

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
        started_at: str = None,
        chat_message_count: int = 0
    ) -> int:
        """Add a stream record and return its ID."""
        self.db.execute("""
            INSERT INTO twitch_stream_records
            (channel_id, is_live, title, game_name, viewer_count, started_at, chat_message_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (channel_id, is_live, title, game_name, viewer_count, started_at, chat_message_count))
        self.db.commit()
        return self.db.cursor.lastrowid

    def add_chat_messages(self, record_id: int, messages: List[Dict]):
        """Add chat messages for a stream record."""
        for msg in messages:
            self.db.execute("""
                INSERT INTO twitch_chat_messages
                (record_id, username, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (record_id, msg['username'], msg['message'], msg['timestamp']))
        self.db.commit()

    def get_chat_messages(self, record_id: int) -> List[Dict]:
        """Get chat messages for a stream record."""
        self.db.execute("""
            SELECT * FROM twitch_chat_messages
            WHERE record_id = ?
            ORDER BY timestamp ASC
        """, (record_id,))
        return self.db.fetchall()

    def get_stream_records(self, channel_id: int, limit: int = 100) -> List[Dict]:
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
                SUM(chat_message_count) as total_chat_messages,
                AVG(CASE WHEN is_live = 1 AND chat_message_count > 0 THEN chat_message_count ELSE NULL END) as avg_chat_per_interval,
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


def collect_twitch_data(channel_name: str, db, collect_chat: bool = False, chat_duration: int = 60) -> bool:
    """
    Collect data for a Twitch channel.

    Args:
        channel_name: Channel username
        db: Session database instance
        collect_chat: Whether to collect chat messages
        chat_duration: Duration to collect chat (seconds)

    Returns:
        bool: True if successful
    """
    from utils.credential_manager import CredentialManager

    creds = CredentialManager.get_twitch_credentials()
    if not creds:
        return False

    try:
        api = TwitchAPI(creds.client_id, creds.client_secret)
        db_helper = TwitchDatabase(db)

        stream_info = api.get_stream_info(channel_name)
        if not stream_info:
            return False

        channel = db_helper.get_channel(channel_name)
        if not channel:
            channel_id = db_helper.add_channel(channel_name)
        else:
            channel_id = channel['id']

        chat_count = 0
        chat_messages = []

        # Collect chat if stream is live and requested
        if collect_chat and stream_info['is_live']:
            try:
                irc_client = TwitchIRCClient(channel_name, api.access_token)
                chat_data = irc_client.collect_messages(duration_seconds=chat_duration)
                chat_count = chat_data['message_count']
                chat_messages = chat_data['messages']
                irc_client.disconnect()
            except Exception as e:
                print(f"Error collecting chat: {e}")
                chat_count = 0

        # Add stream record
        record_id = db_helper.add_stream_record(
            channel_id=channel_id,
            is_live=stream_info['is_live'],
            title=stream_info.get('title'),
            game_name=stream_info.get('game_name'),
            viewer_count=stream_info.get('viewer_count', 0),
            started_at=stream_info.get('started_at'),
            chat_message_count=chat_count
        )

        # Add chat messages if collected
        if chat_messages:
            db_helper.add_chat_messages(record_id, chat_messages)

        return True

    except Exception as e:
        print(f"Error collecting Twitch data: {e}")
        return False
