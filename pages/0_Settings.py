"""
Global Settings Page

Configure global monitoring settings and app preferences.
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.job_manager import JobManager


st.set_page_config(page_title="Settings", layout="wide")


def main():
    st.title("Settings")

    st.write("""
    Configure global monitoring settings and controls for all platforms.
    """)

    st.divider()

    # Global Monitoring Control Section
    st.header("Global Monitoring Control")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Monitoring Interval")

        # Initialize session state for interval
        if 'monitoring_interval' not in st.session_state:
            st.session_state.monitoring_interval = 60  # Default 60 seconds

        # Interval input
        interval = st.number_input(
            "Collection Interval (seconds)",
            min_value=5,
            max_value=86400,  # Max 24 hours
            value=st.session_state.monitoring_interval,
            step=5,
            help="How often to collect data for all monitored entities across all platforms"
        )
        st.session_state.monitoring_interval = interval

        # Show interval in friendly format
        if interval < 60:
            st.caption(f"Interval: {interval} seconds")
        elif interval < 3600:
            st.caption(f"Interval: {interval // 60} minutes, {interval % 60} seconds")
        else:
            hours = interval // 3600
            minutes = (interval % 3600) // 60
            st.caption(f"Interval: {hours} hours, {minutes} minutes")

    with col2:
        st.subheader("Quick Presets")

        if st.button("30 seconds", use_container_width=True):
            st.session_state.monitoring_interval = 30
            st.rerun()

        if st.button("1 minute", use_container_width=True):
            st.session_state.monitoring_interval = 60
            st.rerun()

        if st.button("5 minutes", use_container_width=True):
            st.session_state.monitoring_interval = 300
            st.rerun()

        if st.button("15 minutes", use_container_width=True):
            st.session_state.monitoring_interval = 900
            st.rerun()

    st.divider()

    # Start/Stop Controls
    st.subheader("Monitoring Controls")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start All Monitoring", type="primary", use_container_width=True):
            JobManager.start_all_jobs(interval_seconds=st.session_state.monitoring_interval)
            st.session_state.monitoring_active = True
            st.success("✓ Monitoring started for all platforms!")
            st.rerun()

    with col2:
        if st.button("Stop All Monitoring", type="secondary", use_container_width=True):
            JobManager.stop_all_jobs()
            st.session_state.monitoring_active = False
            st.warning("Monitoring stopped for all platforms")
            st.rerun()

    # Show current status
    st.divider()

    if st.session_state.get('monitoring_active', False):
        st.success(f"✓ **Monitoring is ACTIVE** - Collecting data every {interval} seconds")

        # Show job statistics
        job_stats = JobManager.get_job_statistics()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Active Jobs", job_stats['active_jobs'])

        with col2:
            st.metric("Total Runs", job_stats['total_runs'])

        with col3:
            st.metric("Paused Jobs", job_stats['paused_jobs'])

        # Show platform breakdown
        if job_stats['total_jobs'] > 0:
            st.subheader("Jobs by Platform")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Twitch", job_stats['jobs_by_platform']['twitch'])

            with col2:
                st.metric("Twitter", job_stats['jobs_by_platform']['twitter'])

            with col3:
                st.metric("YouTube", job_stats['jobs_by_platform']['youtube'])

            with col4:
                st.metric("Reddit", job_stats['jobs_by_platform']['reddit'])

            if job_stats['jobs_with_errors'] > 0:
                st.warning(f"⚠ {job_stats['jobs_with_errors']} job(s) have errors")
    else:
        st.info("Monitoring is currently inactive. Click 'Start All Monitoring' to begin.")

        # Show how many jobs are configured
        job_stats = JobManager.get_job_statistics()

        if job_stats['total_jobs'] > 0:
            st.write(f"You have **{job_stats['total_jobs']} monitoring job(s)** configured and ready to start.")
        else:
            st.write("No monitoring jobs configured yet. Add channels/users on the platform pages to get started.")

    st.divider()

    # Information section
    st.header("How Monitoring Works")

    st.write("""
    **Automatic Data Collection:**
    - When monitoring is active, the app automatically collects data from all configured entities
    - Each platform page (Twitch, Twitter, YouTube, Reddit) checks for due jobs when you navigate to it
    - Jobs run based on the interval you set above
    - Data is collected in the background and stored in your session

    **Important Notes:**
    - ⚠ All data is stored in browser memory and will be deleted when you close the tab
    - Use the Export page to download your data before closing
    - Monitoring continues as long as you keep the browser tab open
    - Navigate between pages to trigger job execution
    """)


if __name__ == "__main__":
    main()
