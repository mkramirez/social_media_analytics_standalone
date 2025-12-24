"""
YouTube Monitoring Page
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db
from utils.credential_manager import CredentialManager
from utils.job_manager import JobManager
from src.platforms.youtube_integration import YouTubeDatabase, collect_youtube_data


st.set_page_config(page_title="YouTube", page_icon="📺", layout="wide")


def check_credentials():
    if not CredentialManager.has_youtube_credentials():
        st.warning("⚠️ YouTube credentials not configured")
        st.info("Please go to the **Setup** page to configure your YouTube API credentials")
        st.stop()


def main():
    st.title("📺 YouTube Monitoring")
    check_credentials()

    db = get_session_db()
    youtube_db = YouTubeDatabase(db)

    if st.session_state.get('selected_channel_yt'):
        show_channel_details(st.session_state.selected_channel_yt, youtube_db, db)
    else:
        show_add_channel(youtube_db, db)
        st.divider()
        show_channels_list(youtube_db)


def show_add_channel(youtube_db, db):
    st.subheader("📝 Add YouTube Channel")

    with st.form("add_channel_form"):
        search_query = st.text_input("Channel Name or ID", placeholder="MrBeast or UC...")
        is_channel_id = st.checkbox("This is a Channel ID (starts with UC...)")
        collect_immediately = st.checkbox("Collect data immediately", value=True)
        start_monitoring = st.checkbox("Start monitoring job", value=False)

        interval = 60
        if start_monitoring:
            interval = st.select_slider("Monitoring Interval", options=[30, 60, 120, 240, 480], value=120, format_func=lambda x: f"{x} min")

        if st.form_submit_button("Add Channel", use_container_width=True):
            if not search_query:
                st.error("Please enter a channel name or ID")
                return

            if collect_immediately:
                with st.spinner("Searching and collecting data..."):
                    success = collect_youtube_data(search_query, db, is_channel_id=is_channel_id)
                    if success:
                        st.success("✅ Channel added successfully!")
                        if start_monitoring:
                            # Get the channel we just added
                            channels = youtube_db.get_all_channels()
                            if channels:
                                latest_channel = channels[0]
                                JobManager.add_job("youtube", latest_channel['id'], latest_channel['channel_name'], interval)
                                youtube_db.set_monitoring(latest_channel['id'], True)
                                st.success(f"✅ Started monitoring (every {interval} min)")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to add channel")


def show_channels_list(youtube_db):
    st.subheader("📋 Monitored Channels")

    channels = youtube_db.get_all_channels()

    if not channels:
        st.info("No channels added yet")
        return

    for channel in channels:
        with st.expander(f"📺 **{channel['channel_name']}**"):
            stats = youtube_db.get_channel_statistics(channel['id'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Videos", stats['total_videos'] if stats else 0)
            with col2:
                st.metric("Total Views", f"{stats['total_views']:,}" if stats and stats['total_views'] else "0")
            with col3:
                jobs = [j for j in JobManager.get_jobs_by_platform("youtube") if j.entity_id == channel['id']]
                if jobs and jobs[0].is_active:
                    st.success("✅ Monitoring")

            st.divider()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🔄 Collect", key=f"collect_yt_{channel['id']}"):
                    with st.spinner("Collecting..."):
                        collect_youtube_data(channel['channel_id'], db, is_channel_id=True)
                        st.rerun()
            with c2:
                jobs = [j for j in JobManager.get_jobs_by_platform("youtube") if j.entity_id == channel['id']]
                if jobs:
                    if jobs[0].is_active:
                        if st.button("⏸️ Pause", key=f"pause_yt_{channel['id']}"):
                            JobManager.pause_job(jobs[0].id)
                            st.rerun()
                    else:
                        if st.button("▶️ Resume", key=f"resume_yt_{channel['id']}"):
                            JobManager.resume_job(jobs[0].id)
                            st.rerun()
                else:
                    if st.button("▶️ Start", key=f"start_yt_{channel['id']}"):
                        JobManager.add_job("youtube", channel['id'], channel['channel_name'], 120)
                        st.rerun()
            with c3:
                if st.button("📊 View", key=f"view_yt_{channel['id']}"):
                    st.session_state.selected_channel_yt = channel['id']
                    st.rerun()
            with c4:
                if st.button("🗑️ Delete", key=f"del_yt_{channel['id']}"):
                    if st.session_state.get(f"confirm_del_yt_{channel['id']}", False):
                        jobs = [j for j in JobManager.get_jobs_by_platform("youtube") if j.entity_id == channel['id']]
                        if jobs:
                            JobManager.remove_job(jobs[0].id)
                        youtube_db.delete_channel(channel['id'])
                        st.rerun()
                    else:
                        st.session_state[f"confirm_del_yt_{channel['id']}"] = True
                        st.warning("Click again")


def show_channel_details(channel_id, youtube_db, db):
    channels = youtube_db.get_all_channels()
    channel = next((c for c in channels if c['id'] == channel_id), None)

    if not channel:
        st.session_state.selected_channel_yt = None
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📊 {channel['channel_name']}")
    with col2:
        if st.button("← Back"):
            st.session_state.selected_channel_yt = None
            st.rerun()

    videos = youtube_db.get_videos(channel_id, limit=500)

    if not videos:
        st.warning("No videos yet")
        return

    df = pd.DataFrame(videos)
    df['published_at'] = pd.to_datetime(df['published_at'])

    stats = youtube_db.get_channel_statistics(channel_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Videos", stats['total_videos'])
    with col2:
        st.metric("Total Views", f"{stats['total_views']:,}")
    with col3:
        st.metric("Total Likes", f"{stats['total_likes']:,}")

    st.divider()

    tab1, tab2 = st.tabs(["📈 Performance", "📋 All Videos"])

    with tab1:
        fig = px.bar(df.nlargest(10, 'view_count'), x='title', y='view_count', title="Top 10 Videos by Views")
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        display_df = df[['published_at', 'title', 'view_count', 'like_count', 'comment_count']].sort_values('published_at', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name=f"youtube_{channel['channel_name']}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


if __name__ == "__main__":
    main()
