"""
Twitch Monitoring Page

Monitor Twitch channels and collect stream data.
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db
from utils.credential_manager import CredentialManager
from utils.job_manager import JobManager
from src.platforms.twitch_integration import (
    TwitchDatabase,
    collect_twitch_data
)


st.set_page_config(page_title="Twitch Monitoring", page_icon="🎮", layout="wide")


def check_credentials():
    """Check if Twitch credentials are configured."""
    if not CredentialManager.has_twitch_credentials():
        st.warning("⚠️ Twitch credentials not configured")
        st.info("Please go to the **Setup** page to configure your Twitch API credentials")
        st.stop()


def show_add_channel():
    """Show form to add a channel."""
    st.subheader("📝 Add Channel")

    with st.form("add_channel_form"):
        channel_name = st.text_input(
            "Channel Username",
            placeholder="Enter Twitch channel username (e.g., ninja, shroud)",
            help="Enter the username without the @ symbol"
        )

        col1, col2 = st.columns(2)

        with col1:
            collect_immediately = st.checkbox("Collect data immediately", value=True)

        with col2:
            start_monitoring = st.checkbox("Start monitoring job", value=False)

        if start_monitoring:
            interval = st.select_slider(
                "Monitoring Interval",
                options=[5, 10, 15, 30, 60],
                value=15,
                format_func=lambda x: f"{x} minutes"
            )
        else:
            interval = 15

        submitted = st.form_submit_button("Add Channel", use_container_width=True)

        if submitted:
            if not channel_name or len(channel_name) < 2:
                st.error("Please enter a valid channel username")
                return

            # Clean channel name
            channel_name = channel_name.strip().lower().replace("@", "")

            db = get_session_db()
            twitch_db = TwitchDatabase(db)

            # Check if already exists
            existing = twitch_db.get_channel(channel_name)
            if existing:
                st.warning(f"Channel **{channel_name}** already exists!")
                return

            # Add channel
            channel_id = twitch_db.add_channel(channel_name)

            # Collect data immediately
            if collect_immediately:
                with st.spinner(f"Collecting data for **{channel_name}**..."):
                    success = collect_twitch_data(channel_name, db)

                    if success:
                        st.success(f"✅ Successfully added and collected data for **{channel_name}**")
                    else:
                        st.error(f"Added channel but failed to collect data. Check your credentials.")

            # Start monitoring
            if start_monitoring:
                job_id = JobManager.add_job(
                    platform="twitch",
                    entity_id=channel_id,
                    entity_name=channel_name,
                    interval_minutes=interval
                )
                twitch_db.set_monitoring(channel_id, True)
                st.success(f"✅ Started monitoring job (every {interval} minutes)")

            st.balloons()
            st.rerun()


def show_channels_list():
    """Show list of all channels."""
    st.subheader("📋 Monitored Channels")

    db = get_session_db()
    twitch_db = TwitchDatabase(db)

    channels = twitch_db.get_all_channels()

    if not channels:
        st.info("No channels added yet. Add a channel above to get started!")
        return

    st.write(f"**Total channels:** {len(channels)}")

    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['channel_name']

        with st.expander(f"🎮 **{channel_name}**", expanded=False):
            # Get latest record
            latest = twitch_db.get_latest_record(channel_id)
            stats = twitch_db.get_channel_statistics(channel_id)

            # Display current status
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                if latest:
                    if latest['is_live']:
                        st.success("🔴 **LIVE**")
                        if latest['title']:
                            st.write(f"**Title:** {latest['title']}")
                        if latest['game_name']:
                            st.write(f"**Game:** {latest['game_name']}")
                        st.metric("Current Viewers", f"{latest['viewer_count']:,}")
                    else:
                        st.info("⚫ **OFFLINE**")
                else:
                    st.warning("No data collected yet")

            with col2:
                if stats and stats['total_records'] > 0:
                    st.metric("Total Records", stats['total_records'])
                    st.metric("Live Records", stats['live_count'])
                    if stats['avg_viewers'] > 0:
                        st.metric("Avg Viewers", f"{int(stats['avg_viewers']):,}")

            with col3:
                # Check if monitoring
                jobs = JobManager.get_jobs_by_platform("twitch")
                channel_jobs = [j for j in jobs if j.entity_id == channel_id]

                if channel_jobs:
                    job = channel_jobs[0]
                    if job.is_active:
                        st.success("✅ Monitoring")
                    else:
                        st.warning("⏸️ Paused")

            st.divider()

            # Actions
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button(f"🔄 Collect Data", key=f"collect_{channel_id}"):
                    with st.spinner("Collecting..."):
                        success = collect_twitch_data(channel_name, db)
                        if success:
                            st.success("Data collected!")
                            st.rerun()
                        else:
                            st.error("Failed to collect data")

            with action_col2:
                # Check if has job
                if channel_jobs:
                    job = channel_jobs[0]
                    if job.is_active:
                        if st.button(f"⏸️ Pause", key=f"pause_{channel_id}"):
                            JobManager.pause_job(job.id)
                            twitch_db.set_monitoring(channel_id, False)
                            st.success("Job paused")
                            st.rerun()
                    else:
                        if st.button(f"▶️ Resume", key=f"resume_{channel_id}"):
                            JobManager.resume_job(job.id)
                            twitch_db.set_monitoring(channel_id, True)
                            st.success("Job resumed")
                            st.rerun()
                else:
                    if st.button(f"▶️ Start Job", key=f"start_{channel_id}"):
                        job_id = JobManager.add_job(
                            platform="twitch",
                            entity_id=channel_id,
                            entity_name=channel_name,
                            interval_minutes=15
                        )
                        twitch_db.set_monitoring(channel_id, True)
                        st.success("Job started")
                        st.rerun()

            with action_col3:
                if st.button(f"📊 View Data", key=f"view_{channel_id}"):
                    st.session_state.selected_channel = channel_id
                    st.rerun()

            with action_col4:
                if st.button(f"🗑️ Delete", key=f"delete_{channel_id}"):
                    if st.session_state.get(f"confirm_delete_{channel_id}", False):
                        # Delete job if exists
                        if channel_jobs:
                            JobManager.remove_job(channel_jobs[0].id)

                        # Delete channel
                        twitch_db.delete_channel(channel_id)
                        st.success("Channel deleted")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{channel_id}"] = True
                        st.warning("Click again to confirm")


def show_channel_details(channel_id: int):
    """Show detailed data for a channel."""
    db = get_session_db()
    twitch_db = TwitchDatabase(db)

    # Get channel
    channels = twitch_db.get_all_channels()
    channel = next((c for c in channels if c['id'] == channel_id), None)

    if not channel:
        st.error("Channel not found")
        st.session_state.selected_channel = None
        return

    channel_name = channel['channel_name']

    # Header
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"📊 Data for **{channel_name}**")

    with col2:
        if st.button("← Back to List"):
            st.session_state.selected_channel = None
            st.rerun()

    # Get records
    records = twitch_db.get_stream_records(channel_id, limit=500)

    if not records:
        st.warning("No data collected yet")
        return

    # Convert to DataFrame
    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Statistics
    stats = twitch_db.get_channel_statistics(channel_id)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", stats['total_records'])

    with col2:
        st.metric("Live Records", stats['live_count'])

    with col3:
        if stats['avg_viewers']:
            st.metric("Avg Viewers (Live)", f"{int(stats['avg_viewers']):,}")
        else:
            st.metric("Avg Viewers (Live)", "N/A")

    with col4:
        if stats['peak_viewers']:
            st.metric("Peak Viewers", f"{stats['peak_viewers']:,}")
        else:
            st.metric("Peak Viewers", "N/A")

    st.divider()

    # Charts
    tab1, tab2, tab3 = st.tabs(["📈 Viewer Count Over Time", "📊 Live Status", "📋 Raw Data"])

    with tab1:
        st.subheader("Viewer Count Over Time")

        # Filter only live records for viewer chart
        df_live = df[df['is_live'] == 1].copy()

        if len(df_live) > 0:
            fig = px.line(
                df_live,
                x='timestamp',
                y='viewer_count',
                title=f"Viewer Count for {channel_name}",
                labels={'viewer_count': 'Viewers', 'timestamp': 'Time'}
            )

            fig.update_traces(mode='lines+markers')
            fig.update_layout(hovermode='x unified')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No live stream records yet")

    with tab2:
        st.subheader("Live Status Over Time")

        # Create live/offline chart
        df_status = df.copy()
        df_status['status'] = df_status['is_live'].map({1: 'Live', 0: 'Offline'})

        fig = px.scatter(
            df_status,
            x='timestamp',
            y='status',
            color='status',
            title=f"Stream Status for {channel_name}",
            labels={'status': 'Status', 'timestamp': 'Time'},
            color_discrete_map={'Live': 'green', 'Offline': 'gray'}
        )

        st.plotly_chart(fig, use_container_width=True)

        # Live percentage
        live_pct = (stats['live_count'] / stats['total_records']) * 100
        st.metric("Live Percentage", f"{live_pct:.1f}%")

    with tab3:
        st.subheader("Raw Data")

        # Show dataframe
        display_df = df[['timestamp', 'is_live', 'title', 'game_name', 'viewer_count']].copy()
        display_df['is_live'] = display_df['is_live'].map({1: '🔴 Live', 0: '⚫ Offline'})

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"twitch_{channel_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def main():
    """Main Twitch page."""
    st.title("🎮 Twitch Monitoring")

    # Check credentials
    check_credentials()

    # Check if viewing details
    if st.session_state.get('selected_channel'):
        show_channel_details(st.session_state.selected_channel)
    else:
        # Show add channel form
        show_add_channel()

        st.divider()

        # Show channels list
        show_channels_list()


if __name__ == "__main__":
    main()
