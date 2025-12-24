"""
Setup Page

Configure API credentials for each platform.
Credentials are stored only in session state (deleted when browser closes).
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credential_manager import CredentialManager


st.set_page_config(page_title="Setup", layout="wide")


def show_twitch_setup():
    """Show Twitch credential setup."""
    st.subheader(" Twitch API Setup")

    if CredentialManager.has_twitch_credentials():
        st.success(" Twitch credentials are configured")

        creds = CredentialManager.get_twitch_credentials()
        st.write(f"**Client ID:** {creds.client_id[:8]}...")

        if st.button("️ Clear Twitch Credentials", key="clear_twitch"):
            if st.session_state.get('confirm_clear_twitch', False):
                if 'twitch_credentials' in st.session_state:
                    del st.session_state.twitch_credentials
                st.session_state.confirm_clear_twitch = False
                st.success("Twitch credentials cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_twitch = True
                st.warning("Click again to confirm")

    else:
        with st.expander("ℹ️ How to get Twitch API credentials", expanded=False):
            st.markdown("""
            1. Go to https://dev.twitch.tv/console
            2. Log in with your Twitch account
            3. Click **"Register Your Application"**
            4. Fill in:
               - **Name:** Your app name (e.g., "My Analytics App")
               - **OAuth Redirect URLs:** http://localhost
               - **Category:** Analytics Tool
            5. Click **"Create"**
            6. Click **"Manage"** on your application
            7. Copy the **Client ID** and **Client Secret**
            """)

        with st.form("twitch_form"):
            st.write("Enter your Twitch API credentials:")

            client_id = st.text_input(
                "Client ID",
                type="password",
                help="Your Twitch application Client ID"
            )

            client_secret = st.text_input(
                "Client Secret",
                type="password",
                help="Your Twitch application Client Secret"
            )

            submitted = st.form_submit_button("Save Twitch Credentials", use_container_width=True)

            if submitted:
                if not client_id or not client_secret:
                    st.error("Both Client ID and Client Secret are required")
                elif len(client_id) < 10 or len(client_secret) < 10:
                    st.error("Invalid credentials (too short)")
                else:
                    CredentialManager.set_twitch_credentials(client_id, client_secret)
                    st.success(" Twitch credentials saved!")
                    st.balloons()
                    st.rerun()


def show_twitter_setup():
    """Show Twitter credential setup."""
    st.subheader(" Twitter API Setup")

    if CredentialManager.has_twitter_credentials():
        st.success(" Twitter credentials are configured")

        creds = CredentialManager.get_twitter_credentials()
        st.write(f"**Bearer Token:** {creds.bearer_token[:15]}...")

        if st.button("️ Clear Twitter Credentials", key="clear_twitter"):
            if st.session_state.get('confirm_clear_twitter', False):
                if 'twitter_credentials' in st.session_state:
                    del st.session_state.twitter_credentials
                st.session_state.confirm_clear_twitter = False
                st.success("Twitter credentials cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_twitter = True
                st.warning("Click again to confirm")

    else:
        with st.expander("ℹ️ How to get Twitter API credentials", expanded=False):
            st.markdown("""
            1. Go to https://developer.twitter.com/
            2. Log in with your Twitter account
            3. Apply for a **Developer Account** (if you don't have one)
            4. Create a **new project and app**
            5. Navigate to **"Keys and Tokens"** tab
            6. Under **"Authentication Tokens"**, click **"Generate"** next to Bearer Token
            7. Copy the **Bearer Token** (it starts with "AAAA...")

            **Note:** Twitter API v2 Essential access is free (500k tweets/month).
            """)

        with st.form("twitter_form"):
            st.write("Enter your Twitter API credentials:")

            bearer_token = st.text_input(
                "Bearer Token",
                type="password",
                help="Your Twitter API Bearer Token (starts with AAAA...)"
            )

            submitted = st.form_submit_button("Save Twitter Credentials", use_container_width=True)

            if submitted:
                if not bearer_token:
                    st.error("Bearer Token is required")
                elif len(bearer_token) < 20:
                    st.error("Invalid Bearer Token (too short)")
                else:
                    CredentialManager.set_twitter_credentials(bearer_token)
                    st.success(" Twitter credentials saved!")
                    st.balloons()
                    st.rerun()


def show_youtube_setup():
    """Show YouTube credential setup."""
    st.subheader(" YouTube API Setup")

    if CredentialManager.has_youtube_credentials():
        st.success(" YouTube credentials are configured")

        creds = CredentialManager.get_youtube_credentials()
        st.write(f"**API Key:** {creds.api_key[:15]}...")

        if st.button("️ Clear YouTube Credentials", key="clear_youtube"):
            if st.session_state.get('confirm_clear_youtube', False):
                if 'youtube_credentials' in st.session_state:
                    del st.session_state.youtube_credentials
                st.session_state.confirm_clear_youtube = False
                st.success("YouTube credentials cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_youtube = True
                st.warning("Click again to confirm")

    else:
        with st.expander("ℹ️ How to get YouTube API credentials", expanded=False):
            st.markdown("""
            1. Go to https://console.cloud.google.com/
            2. Log in with your Google account
            3. Create a **new project** (top bar, click project dropdown)
            4. Enable **"YouTube Data API v3"**:
               - Go to **"APIs & Services" → "Library"**
               - Search for "YouTube Data API v3"
               - Click **"Enable"**
            5. Create credentials:
               - Go to **"APIs & Services" → "Credentials"**
               - Click **"Create Credentials" → "API Key"**
               - Copy the **API Key**
            6. (Optional) Click **"Restrict Key"** to add restrictions

            **Note:** YouTube API has a free quota of 10,000 units/day.
            """)

        with st.form("youtube_form"):
            st.write("Enter your YouTube API credentials:")

            api_key = st.text_input(
                "API Key",
                type="password",
                help="Your YouTube Data API v3 API Key"
            )

            submitted = st.form_submit_button("Save YouTube Credentials", use_container_width=True)

            if submitted:
                if not api_key:
                    st.error("API Key is required")
                elif len(api_key) < 20:
                    st.error("Invalid API Key (too short)")
                else:
                    CredentialManager.set_youtube_credentials(api_key)
                    st.success(" YouTube credentials saved!")
                    st.balloons()
                    st.rerun()


def show_reddit_setup():
    """Show Reddit credential setup."""
    st.subheader(" Reddit API Setup")

    if CredentialManager.has_reddit_credentials():
        st.success(" Reddit credentials are configured")

        creds = CredentialManager.get_reddit_credentials()
        st.write(f"**Client ID:** {creds.client_id[:8]}...")
        st.write(f"**User Agent:** {creds.user_agent}")

        if st.button("️ Clear Reddit Credentials", key="clear_reddit"):
            if st.session_state.get('confirm_clear_reddit', False):
                if 'reddit_credentials' in st.session_state:
                    del st.session_state.reddit_credentials
                st.session_state.confirm_clear_reddit = False
                st.success("Reddit credentials cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_reddit = True
                st.warning("Click again to confirm")

    else:
        with st.expander("ℹ️ How to get Reddit API credentials", expanded=False):
            st.markdown("""
            1. Go to https://www.reddit.com/prefs/apps
            2. Log in with your Reddit account
            3. Scroll to bottom and click **"Create App"** or **"Create Another App"**
            4. Fill in:
               - **Name:** Your app name (e.g., "My Analytics App")
               - **App type:** Select **"script"**
               - **Description:** (optional)
               - **About URL:** (optional)
               - **Redirect URI:** http://localhost:8080
            5. Click **"Create app"**
            6. Copy:
               - **Client ID:** (under the app name, looks random)
               - **Client Secret:** (labeled "secret")
            7. Create a User Agent:
               - Format: `platform:app_name:version (by /u/your_username)`
               - Example: `web:my-analytics:v1.0 (by /u/johndoe)`

            **Note:** Reddit API is free with rate limits (60 requests/minute).
            """)

        with st.form("reddit_form"):
            st.write("Enter your Reddit API credentials:")

            client_id = st.text_input(
                "Client ID",
                type="password",
                help="Your Reddit application Client ID"
            )

            client_secret = st.text_input(
                "Client Secret",
                type="password",
                help="Your Reddit application Client Secret"
            )

            user_agent = st.text_input(
                "User Agent",
                placeholder="web:my-analytics:v1.0 (by /u/yourusername)",
                help="A unique identifier for your app"
            )

            submitted = st.form_submit_button("Save Reddit Credentials", use_container_width=True)

            if submitted:
                if not client_id or not client_secret or not user_agent:
                    st.error("All fields are required")
                elif len(client_id) < 10 or len(client_secret) < 10:
                    st.error("Invalid credentials (too short)")
                elif len(user_agent) < 10:
                    st.error("Invalid User Agent (too short)")
                else:
                    CredentialManager.set_reddit_credentials(client_id, client_secret, user_agent)
                    st.success(" Reddit credentials saved!")
                    st.balloons()
                    st.rerun()


def main():
    """Main setup page."""
    st.title("️ Setup - API Credentials")

    st.write("""
    Configure your API credentials for each platform you want to monitor.

    **Important:**
    - Credentials are stored **only in this browser session**
    - They will be **deleted when you close the browser tab**
    - You'll need to re-enter them next time you use the app
    - Your credentials are **never sent to external servers** (except to the respective platforms)
    """)

    st.divider()

    # Show setup status
    st.subheader(" Setup Status")

    status = CredentialManager.get_setup_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status['twitch']:
            st.success(" Twitch")
        else:
            st.warning("️ Twitch")

    with col2:
        if status['twitter']:
            st.success(" Twitter")
        else:
            st.warning("️ Twitter")

    with col3:
        if status['youtube']:
            st.success(" YouTube")
        else:
            st.warning("️ YouTube")

    with col4:
        if status['reddit']:
            st.success(" Reddit")
        else:
            st.warning("️ Reddit")

    st.divider()

    # Platform tabs
    tab1, tab2, tab3, tab4 = st.tabs([" Twitch", " Twitter", " YouTube", " Reddit"])

    with tab1:
        show_twitch_setup()

    with tab2:
        show_twitter_setup()

    with tab3:
        show_youtube_setup()

    with tab4:
        show_reddit_setup()

    st.divider()

    # Quick actions
    st.subheader(" Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("️ Clear All Credentials", use_container_width=True):
            if st.session_state.get('confirm_clear_all', False):
                CredentialManager.clear_all_credentials()
                st.session_state.confirm_clear_all = False
                st.success("All credentials cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("Click again to confirm")

    with col2:
        configured = [p for p, c in status.items() if c]
        if configured:
            st.success(f" {len(configured)}/4 platforms configured")
        else:
            st.info("Configure at least one platform to get started")


if __name__ == "__main__":
    main()
