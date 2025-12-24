"""
Enhanced Twitch Monitoring Page

Features:
- Bulk user addition
- Automated collection with intervals
- Chat message collection
- Multi-sheet Excel export (one sheet per user)
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db
from utils.credential_manager import CredentialManager
from utils.job_manager import JobManager
from src.platforms.twitch_integration_enhanced import (
    TwitchDatabase,
    TwitchAPI,
    collect_twitch_data
)


st.set_page_config(page_title="Twitch", layout="wide")


def check_credentials():
    """Check if Twitch credentials are configured."""
    if not CredentialManager.has_twitch_credentials():
        st.warning("️ Twitch credentials not configured")
        st.info("Please go to the **Setup** page to configure your Twitch API credentials")
        st.stop()


def auto_run_jobs():
    """Auto-run jobs that are due."""
    due_jobs = JobManager.get_jobs_due_for_run()

    if due_jobs:
        db = get_session_db()

        for job in due_jobs:
            if job.platform == "twitch":
                # Get chat collection setting
                collect_chat = st.session_state.get(f"collect_chat_{job.entity_id}", False)
                chat_duration = st.session_state.get(f"chat_duration_{job.entity_id}", 60)

                success = collect_twitch_data(
                    job.entity_name,
                    db,
                    collect_chat=collect_chat,
                    chat_duration=chat_duration
                )

                JobManager.mark_job_run(job.id, success=success)


def show_bulk_add():
    """Show bulk user addition form."""
    st.subheader(" Add Channels (Bulk)")

    with st.form("bulk_add_form"):
        st.write("**Add multiple channels at once**")

        channels_text = st.text_area(
            "Channel Usernames (one per line)",
            placeholder="ninja\nshroud\nxqc\npokimane",
            height=150,
            help="Enter one channel username per line"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            verify_first = st.checkbox("Verify channels exist", value=True)

        with col2:
            collect_immediately = st.checkbox("Collect data immediately", value=True)

        with col3:
            start_monitoring = st.checkbox("Start monitoring jobs", value=True)

        st.divider()

        st.write("**Monitoring Settings**")

        col1, col2 = st.columns(2)

        with col1:
            interval = st.select_slider(
                "Collection Interval",
                options=[5, 10, 15, 30, 60, 120, 180, 240],
                value=15,
                format_func=lambda x: f"{x} minutes"
            )

        with col2:
            collect_chat = st.checkbox("Collect chat messages", value=True)

        if collect_chat:
            chat_duration = st.slider(
                "Chat Collection Duration (seconds)",
                min_value=30,
                max_value=300,
                value=60,
                step=30,
                help="How long to collect chat messages when the stream is live"
            )
        else:
            chat_duration = 60

        submitted = st.form_submit_button("Add Channels", use_container_width=True)

        if submitted:
            if not channels_text.strip():
                st.error("Please enter at least one channel username")
                return

            # Parse channels
            channel_names = [
                name.strip().lower().replace("@", "")
                for name in channels_text.split("\n")
                if name.strip()
            ]

            if not channel_names:
                st.error("No valid channel names found")
                return

            db = get_session_db()
            twitch_db = TwitchDatabase(db)
            creds = CredentialManager.get_twitch_credentials()
            api = TwitchAPI(creds.client_id, creds.client_secret)

            results = {
                'success': [],
                'already_exists': [],
                'not_found': [],
                'errors': []
            }

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, channel_name in enumerate(channel_names):
                status_text.text(f"Processing {channel_name}... ({idx + 1}/{len(channel_names)})")

                # Check if already exists
                existing = twitch_db.get_channel(channel_name)
                if existing:
                    results['already_exists'].append(channel_name)
                    progress_bar.progress((idx + 1) / len(channel_names))
                    continue

                # Verify channel exists
                if verify_first:
                    user_info = api.get_user_info(channel_name)
                    if not user_info:
                        results['not_found'].append(channel_name)
                        progress_bar.progress((idx + 1) / len(channel_names))
                        continue

                try:
                    # Add channel
                    channel_id = twitch_db.add_channel(channel_name)

                    # Store chat settings
                    st.session_state[f"collect_chat_{channel_id}"] = collect_chat
                    st.session_state[f"chat_duration_{channel_id}"] = chat_duration

                    # Collect data immediately
                    if collect_immediately:
                        success = collect_twitch_data(
                            channel_name,
                            db,
                            collect_chat=collect_chat,
                            chat_duration=chat_duration
                        )

                    # Start monitoring
                    if start_monitoring:
                        job_id = JobManager.add_job(
                            platform="twitch",
                            entity_id=channel_id,
                            entity_name=channel_name,
                            interval_minutes=interval
                        )
                        twitch_db.set_monitoring(channel_id, True)

                    results['success'].append(channel_name)

                except Exception as e:
                    results['errors'].append(f"{channel_name}: {str(e)}")

                progress_bar.progress((idx + 1) / len(channel_names))

            # Clear progress
            progress_bar.empty()
            status_text.empty()

            # Show results
            if results['success']:
                st.success(f" Successfully added {len(results['success'])} channels:")
                st.write(", ".join(results['success']))

            if results['already_exists']:
                st.info(f"ℹ️ {len(results['already_exists'])} channels already exist:")
                st.write(", ".join(results['already_exists']))

            if results['not_found']:
                st.warning(f"️ {len(results['not_found'])} channels not found:")
                st.write(", ".join(results['not_found']))

            if results['errors']:
                st.error(f" {len(results['errors'])} errors:")
                for error in results['errors']:
                    st.write(f"- {error}")

            if results['success']:
                st.balloons()
                time.sleep(2)
                st.rerun()


def show_channels_list():
    """Show list of all channels with auto-refresh."""
    st.subheader(" Monitored Channels")

    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        auto_refresh = st.checkbox(
            " Auto-refresh (runs jobs automatically)",
            value=st.session_state.get('auto_refresh_twitch', False),
            help="Automatically run due jobs and refresh the page"
        )
        st.session_state['auto_refresh_twitch'] = auto_refresh

    with col2:
        if auto_refresh:
            refresh_interval = st.select_slider(
                "Refresh every",
                options=[30, 60, 120, 180, 300],
                value=60,
                format_func=lambda x: f"{x}s"
            )
        else:
            refresh_interval = 60

    db = get_session_db()
    twitch_db = TwitchDatabase(db)
    channels = twitch_db.get_all_channels()

    if not channels:
        st.info("No channels added yet. Add channels above to get started!")
        return

    st.write(f"**Total channels:** {len(channels)}")

    # Run due jobs if auto-refresh is on
    if auto_refresh:
        auto_run_jobs()

    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['channel_name']

        with st.expander(f" **{channel_name}**", expanded=False):
            latest = twitch_db.get_latest_record(channel_id)
            stats = twitch_db.get_channel_statistics(channel_id)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                if latest:
                    if latest['is_live']:
                        st.success(" **LIVE**")
                        if latest['title']:
                            st.write(f"**Title:** {latest['title']}")
                        if latest['game_name']:
                            st.write(f"**Game:** {latest['game_name']}")
                        st.metric("Current Viewers", f"{latest['viewer_count']:,}")
                        if latest['chat_message_count']:
                            st.metric("Chat Messages (last interval)", latest['chat_message_count'])
                    else:
                        st.info(" **OFFLINE**")
                else:
                    st.warning("No data collected yet")

            with col2:
                if stats and stats['total_records'] > 0:
                    st.metric("Total Records", stats['total_records'])
                    st.metric("Live Records", stats['live_count'])
                    if stats['avg_viewers'] and stats['avg_viewers'] > 0:
                        st.metric("Avg Viewers", f"{int(stats['avg_viewers']):,}")
                    if stats['total_chat_messages'] and stats['total_chat_messages'] > 0:
                        st.metric("Total Chat Messages", f"{stats['total_chat_messages']:,}")

            with col3:
                jobs = JobManager.get_jobs_by_platform("twitch")
                channel_jobs = [j for j in jobs if j.entity_id == channel_id]

                if channel_jobs:
                    job = channel_jobs[0]
                    if job.is_active:
                        st.success(" Monitoring")
                        st.caption(f"Every {job.interval_minutes}m")

                        # Show next run time
                        if job.next_run:
                            time_until = (job.next_run - datetime.now()).total_seconds()
                            if time_until > 0:
                                st.caption(f"Next: {int(time_until/60)}m {int(time_until%60)}s")
                    else:
                        st.warning("⏸️ Paused")

            st.divider()

            # Settings
            collect_chat = st.checkbox(
                "Collect chat messages",
                value=st.session_state.get(f"collect_chat_{channel_id}", False),
                key=f"chat_toggle_{channel_id}"
            )
            st.session_state[f"collect_chat_{channel_id}"] = collect_chat

            if collect_chat:
                chat_duration = st.slider(
                    "Chat duration (seconds)",
                    30, 300, 60, 30,
                    key=f"chat_duration_{channel_id}"
                )
                st.session_state[f"chat_duration_{channel_id}"] = chat_duration

            st.divider()

            # Actions
            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                if st.button(f" Collect", key=f"collect_{channel_id}"):
                    with st.spinner("Collecting..."):
                        success = collect_twitch_data(
                            channel_name,
                            db,
                            collect_chat=collect_chat,
                            chat_duration=chat_duration if collect_chat else 60
                        )
                        if success:
                            st.success(" Data collected!")
                            time.sleep(1)
                            st.rerun()

            with c2:
                channel_jobs = [j for j in JobManager.get_jobs_by_platform("twitch") if j.entity_id == channel_id]
                if channel_jobs:
                    job = channel_jobs[0]
                    if job.is_active:
                        if st.button(f"⏸️ Pause", key=f"pause_{channel_id}"):
                            JobManager.pause_job(job.id)
                            twitch_db.set_monitoring(channel_id, False)
                            st.rerun()
                    else:
                        if st.button(f"▶️ Resume", key=f"resume_{channel_id}"):
                            JobManager.resume_job(job.id)
                            twitch_db.set_monitoring(channel_id, True)
                            st.rerun()
                else:
                    if st.button(f"▶️ Start", key=f"start_{channel_id}"):
                        job_id = JobManager.add_job("twitch", channel_id, channel_name, 15)
                        twitch_db.set_monitoring(channel_id, True)
                        st.rerun()

            with c3:
                if st.button(f" View", key=f"view_{channel_id}"):
                    st.session_state.selected_channel = channel_id
                    st.rerun()

            with c4:
                # Export button
                if st.button(f" Export", key=f"export_{channel_id}"):
                    export_channel_data(channel_id, channel_name, twitch_db)

            with c5:
                if st.button(f"️ Delete", key=f"delete_{channel_id}"):
                    if st.session_state.get(f"confirm_delete_{channel_id}", False):
                        if channel_jobs:
                            JobManager.remove_job(channel_jobs[0].id)
                        twitch_db.delete_channel(channel_id)
                        st.success("Channel deleted")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{channel_id}"] = True
                        st.warning("Click again to confirm")

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


def export_channel_data(channel_id: int, channel_name: str, twitch_db):
    """Export channel data to Excel with multiple sheets."""
    import io

    try:
        # Get records
        records = twitch_db.get_stream_records(channel_id, limit=1000)

        if not records:
            st.warning("No data to export")
            return

        # Create Excel writer
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Stream data
            df_streams = pd.DataFrame(records)
            df_streams.to_excel(writer, sheet_name='Stream Data', index=False)

            # Sheet 2: Chat messages (if any)
            all_chat_messages = []
            for record in records:
                chat_msgs = twitch_db.get_chat_messages(record['id'])
                for msg in chat_msgs:
                    all_chat_messages.append({
                        'record_timestamp': record['timestamp'],
                        'username': msg['username'],
                        'message': msg['message'],
                        'timestamp': msg['timestamp']
                    })

            if all_chat_messages:
                df_chat = pd.DataFrame(all_chat_messages)
                df_chat.to_excel(writer, sheet_name='Chat Messages', index=False)

        output.seek(0)

        st.download_button(
            label=f" Download {channel_name}_data.xlsx",
            data=output,
            file_name=f"twitch_{channel_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error exporting data: {e}")


def export_all_channels():
    """Export all channels to multi-sheet Excel (one sheet per channel)."""
    db = get_session_db()
    twitch_db = TwitchDatabase(db)
    channels = twitch_db.get_all_channels()

    if not channels:
        st.warning("No channels to export")
        return

    import io

    try:
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for channel in channels:
                records = twitch_db.get_stream_records(channel['id'], limit=1000)

                if records:
                    df = pd.DataFrame(records)
                    # Sanitize sheet name (max 31 chars, no special chars)
                    sheet_name = channel['channel_name'][:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)

        st.download_button(
            label=" Download All Channels Data (Multi-Sheet Excel)",
            data=output,
            file_name=f"twitch_all_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error exporting: {e}")


def main():
    """Main Twitch page."""
    st.title(" Twitch Monitoring")

    check_credentials()

    if st.session_state.get('selected_channel'):
        # Show channel details (implement similar to original)
        st.write("Channel details view - implement as needed")
        if st.button("← Back to List"):
            st.session_state.selected_channel = None
            st.rerun()
    else:
        # Bulk add section
        show_bulk_add()

        st.divider()

        # Export all button
        col1, col2 = st.columns([3, 1])
        with col2:
            export_all_channels()

        st.divider()

        # Channels list with auto-refresh
        show_channels_list()


if __name__ == "__main__":
    main()
