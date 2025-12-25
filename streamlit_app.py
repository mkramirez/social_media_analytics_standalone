"""
Social Media Analytics - Standalone Version

A self-contained Streamlit app for social media analytics.
No external services required - runs entirely in your browser session.

Features:
- Multi-platform monitoring (Twitch, Twitter, YouTube, Reddit)
- Real-time analytics and insights
- Session-based storage (data deleted when browser closes)
- API credentials stored only for current session
- Export database before closing

Author: Social Media Analytics Team
Version: 2.0.0 (Standalone)
"""

import streamlit as st
from database.session_db import get_session_db, reset_session_db
from utils.credential_manager import CredentialManager
from utils.job_manager import JobManager, check_and_run_due_jobs


# Page configuration
st.set_page_config(
    page_title="Social Media Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session():
    """Initialize session state variables."""

    # Initialize database
    db = get_session_db()

    # Initialize session variables if not present
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.app_start_time = st.session_state.get('app_start_time', None)

        if st.session_state.app_start_time is None:
            from datetime import datetime
            st.session_state.app_start_time = datetime.now()


def show_sidebar():
    """Display sidebar with navigation and status."""

    with st.sidebar:
        st.title("Social Media Analytics")
        st.caption("Standalone Version 2.0")

        st.divider()

        # Setup status
        st.subheader("Setup Status")
        status = CredentialManager.get_setup_status()

        for platform, configured in status.items():
            if configured:
                st.success(f"✓ {platform.title()}")
            else:
                st.warning(f"⚠ {platform.title()} - Not configured")

        if not CredentialManager.is_any_platform_configured():
            st.info("Go to **Setup** to configure API credentials")

        st.divider()

        # Job statistics
        st.subheader("Monitoring Jobs")
        job_stats = JobManager.get_job_statistics()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active", job_stats['active_jobs'])
        with col2:
            st.metric("Paused", job_stats['paused_jobs'])

        if job_stats['total_runs'] > 0:
            st.caption(f"Total runs: {job_stats['total_runs']}")

        st.divider()

        # Global Monitoring Control
        st.subheader("Global Monitoring Control")

        # Monitoring interval input (in seconds)
        if 'monitoring_interval' not in st.session_state:
            st.session_state.monitoring_interval = 60  # Default 60 seconds

        interval = st.number_input(
            "Collection Interval (seconds)",
            min_value=5,
            max_value=86400,  # Max 24 hours
            value=st.session_state.monitoring_interval,
            step=5,
            help="How often to collect data for all monitored entities"
        )
        st.session_state.monitoring_interval = interval

        # Start/Stop All button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start All Monitoring", use_container_width=True):
                JobManager.start_all_jobs(interval_seconds=interval)
                st.session_state.monitoring_active = True
                st.success("Monitoring started!")
                st.rerun()

        with col2:
            if st.button("Stop All Monitoring", use_container_width=True):
                JobManager.stop_all_jobs()
                st.session_state.monitoring_active = False
                st.warning("Monitoring stopped")
                st.rerun()

        # Show status
        if st.session_state.get('monitoring_active', False):
            st.success(f"✓ Monitoring active (every {interval}s)")
        else:
            st.info("Monitoring inactive")

        st.divider()

        # Database statistics
        st.subheader("Database Stats")
        db = get_session_db()
        db_stats = db.get_statistics()

        total_records = (
            db_stats['twitch_records'] +
            db_stats['twitter_tweets'] +
            db_stats['youtube_videos'] +
            db_stats['reddit_posts']
        )

        st.metric("Total Records", f"{total_records:,}")

        with st.expander("Details"):
            st.write(f"**Twitch:** {db_stats['twitch_records']:,} streams")
            st.write(f"**Twitter:** {db_stats['twitter_tweets']:,} tweets")
            st.write(f"**YouTube:** {db_stats['youtube_videos']:,} videos")
            st.write(f"**Reddit:** {db_stats['reddit_posts']:,} posts")

        st.divider()

        # Session info
        st.subheader("Session Info")

        if st.session_state.app_start_time:
            from datetime import datetime
            uptime = datetime.now() - st.session_state.app_start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)

            st.info(f"Uptime: {hours}h {minutes}m")

        st.warning("""
        **Session Data**

        All data is stored in memory and will be **deleted** when you close this browser tab.

        Use the **Export** page to download your data before closing.
        """)

        st.divider()

        # Quick actions
        st.subheader("Quick Actions")

        if st.button("Refresh Data", use_container_width=True):
            st.rerun()

        if st.button("Clear All Data", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                reset_session_db()
                JobManager.clear_all_jobs()
                st.session_state.confirm_clear = False
                st.success("All data cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm")

        # Check for due jobs
        due_count = check_and_run_due_jobs()
        if due_count > 0:
            st.info(f"{due_count} job(s) ready to run")


def main():
    """Main application."""

    # Initialize session
    initialize_session()

    # Show sidebar
    show_sidebar()

    # Main content
    st.title("Welcome to Social Media Analytics")

    st.write("""
    This is a **standalone version** of the Social Media Analytics platform that runs entirely
    in your browser session. No external services, databases, or logins required!
    """)

    # Get setup status
    status = CredentialManager.get_setup_status()
    configured_platforms = CredentialManager.get_configured_platforms()

    if not configured_platforms:
        st.info("""
        ### Getting Started

        1. **Go to the Setup page** (in the sidebar) to configure your API credentials
        2. **Choose a platform** (Twitch, Twitter, YouTube, or Reddit)
        3. **Start monitoring** channels, users, or subreddits
        4. **View analytics** to gain insights
        5. **Export data** before closing your browser

        Your API credentials and data are stored **only in this browser session** and
        will be deleted when you close the tab.
        """)
    else:
        st.success(f"You have configured: **{', '.join(p.title() for p in configured_platforms)}**")

        # Show quick stats
        st.divider()

        st.subheader("Quick Overview")

        db = get_session_db()
        db_stats = db.get_statistics()
        job_stats = JobManager.get_job_statistics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Monitoring Jobs",
                job_stats['active_jobs'],
                delta=f"{job_stats['paused_jobs']} paused" if job_stats['paused_jobs'] > 0 else None
            )

        with col2:
            total_entities = (
                db_stats['twitch_channels'] +
                db_stats['twitter_users'] +
                db_stats['youtube_channels'] +
                db_stats['reddit_subreddits']
            )
            st.metric("Total Entities", total_entities)

        with col3:
            total_records = (
                db_stats['twitch_records'] +
                db_stats['twitter_tweets'] +
                db_stats['youtube_videos'] +
                db_stats['reddit_posts']
            )
            st.metric("Total Records", f"{total_records:,}")

        with col4:
            st.metric("Total Runs", job_stats['total_runs'])

        st.divider()

        # Platform breakdown
        st.subheader("Platform Breakdown")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**Twitch**")
            st.write(f"Channels: {db_stats['twitch_channels']}")
            st.write(f"Records: {db_stats['twitch_records']:,}")

        with col2:
            st.markdown("**Twitter**")
            st.write(f"Users: {db_stats['twitter_users']}")
            st.write(f"Tweets: {db_stats['twitter_tweets']:,}")

        with col3:
            st.markdown("**YouTube**")
            st.write(f"Channels: {db_stats['youtube_channels']}")
            st.write(f"Videos: {db_stats['youtube_videos']:,}")

        with col4:
            st.markdown("**Reddit**")
            st.write(f"Subreddits: {db_stats['reddit_subreddits']}")
            st.write(f"Posts: {db_stats['reddit_posts']:,}")

        st.divider()

        # Next steps
        st.subheader("Next Steps")

        st.write("""
        - **Add more entities** to monitor on platform pages
        - **Check the Analytics page** for insights and trends
        - **Export your data** on the Export page before closing
        - **Configure monitoring intervals** for each entity
        """)

    # Footer
    st.divider()

    st.caption("""
    **Social Media Analytics - Standalone Version 2.0**

    This application runs entirely in your browser. All data is stored in memory
    and will be deleted when you close this browser tab.

    No data is sent to external servers (except API calls to platforms you've configured).
    """)


if __name__ == "__main__":
    main()
