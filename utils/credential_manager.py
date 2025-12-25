"""
Credential Manager

Manages API credentials in Streamlit session state.
Credentials are stored only for the current browser session and deleted when closed.
"""

import streamlit as st
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TwitchCredentials:
    """Twitch API credentials."""
    client_id: str
    client_secret: str


@dataclass
class TwitterCredentials:
    """Twitter API credentials."""
    bearer_token: str


@dataclass
class YouTubeCredentials:
    """YouTube API credentials."""
    api_key: str


@dataclass
class RedditCredentials:
    """Reddit API credentials."""
    client_id: str
    client_secret: str
    user_agent: str


@dataclass
class AnthropicCredentials:
    """Anthropic API credentials."""
    api_key: str


class CredentialManager:
    """Manages API credentials in session state."""

    @staticmethod
    def set_twitch_credentials(client_id: str, client_secret: str):
        """Store Twitch credentials."""
        st.session_state.twitch_credentials = TwitchCredentials(
            client_id=client_id,
            client_secret=client_secret
        )

    @staticmethod
    def get_twitch_credentials() -> Optional[TwitchCredentials]:
        """Get Twitch credentials."""
        return st.session_state.get('twitch_credentials')

    @staticmethod
    def has_twitch_credentials() -> bool:
        """Check if Twitch credentials are set."""
        return 'twitch_credentials' in st.session_state

    @staticmethod
    def set_twitter_credentials(bearer_token: str):
        """Store Twitter credentials."""
        st.session_state.twitter_credentials = TwitterCredentials(
            bearer_token=bearer_token
        )

    @staticmethod
    def get_twitter_credentials() -> Optional[TwitterCredentials]:
        """Get Twitter credentials."""
        return st.session_state.get('twitter_credentials')

    @staticmethod
    def has_twitter_credentials() -> bool:
        """Check if Twitter credentials are set."""
        return 'twitter_credentials' in st.session_state

    @staticmethod
    def set_youtube_credentials(api_key: str):
        """Store YouTube credentials."""
        st.session_state.youtube_credentials = YouTubeCredentials(
            api_key=api_key
        )

    @staticmethod
    def get_youtube_credentials() -> Optional[YouTubeCredentials]:
        """Get YouTube credentials."""
        return st.session_state.get('youtube_credentials')

    @staticmethod
    def has_youtube_credentials() -> bool:
        """Check if YouTube credentials are set."""
        return 'youtube_credentials' in st.session_state

    @staticmethod
    def set_reddit_credentials(client_id: str, client_secret: str, user_agent: str):
        """Store Reddit credentials."""
        st.session_state.reddit_credentials = RedditCredentials(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    @staticmethod
    def get_reddit_credentials() -> Optional[RedditCredentials]:
        """Get Reddit credentials."""
        return st.session_state.get('reddit_credentials')

    @staticmethod
    def has_reddit_credentials() -> bool:
        """Check if Reddit credentials are set."""
        return 'reddit_credentials' in st.session_state

    @staticmethod
    def set_anthropic_credentials(api_key: str):
        """Store Anthropic credentials."""
        st.session_state.anthropic_credentials = AnthropicCredentials(
            api_key=api_key
        )

    @staticmethod
    def get_anthropic_credentials() -> Optional[AnthropicCredentials]:
        """Get Anthropic credentials."""
        return st.session_state.get('anthropic_credentials')

    @staticmethod
    def has_anthropic_credentials() -> bool:
        """Check if Anthropic credentials are set."""
        return 'anthropic_credentials' in st.session_state

    @staticmethod
    def clear_all_credentials():
        """Clear all stored credentials."""
        keys_to_delete = [
            'twitch_credentials',
            'twitter_credentials',
            'youtube_credentials',
            'reddit_credentials',
            'anthropic_credentials'
        ]

        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def get_setup_status() -> Dict[str, bool]:
        """Get setup status for all platforms."""
        return {
            'twitch': CredentialManager.has_twitch_credentials(),
            'twitter': CredentialManager.has_twitter_credentials(),
            'youtube': CredentialManager.has_youtube_credentials(),
            'reddit': CredentialManager.has_reddit_credentials(),
            'anthropic': CredentialManager.has_anthropic_credentials()
        }

    @staticmethod
    def is_any_platform_configured() -> bool:
        """Check if any platform is configured."""
        status = CredentialManager.get_setup_status()
        return any(status.values())

    @staticmethod
    def get_configured_platforms() -> list:
        """Get list of configured platform names."""
        status = CredentialManager.get_setup_status()
        return [platform for platform, configured in status.items() if configured]
