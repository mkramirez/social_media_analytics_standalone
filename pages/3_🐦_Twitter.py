"""
Twitter Monitoring Page

Monitor Twitter users and collect tweet data.
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
from src.platforms.twitter_integration import TwitterDatabase, collect_twitter_data


st.set_page_config(page_title="Twitter Monitoring", page_icon="🐦", layout="wide")


def check_credentials():
    if not CredentialManager.has_twitter_credentials():
        st.warning("⚠️ Twitter credentials not configured")
        st.info("Please go to the **Setup** page to configure your Twitter API credentials")
        st.stop()


def show_add_user():
    st.subheader("📝 Add Twitter User")

    with st.form("add_user_form"):
        username = st.text_input(
            "Twitter Username",
            placeholder="Enter Twitter username (e.g., elonmusk, NASA)",
            help="Enter the username without the @ symbol"
        )

        collect_immediately = st.checkbox("Collect data immediately", value=True)
        start_monitoring = st.checkbox("Start monitoring job", value=False)

        if start_monitoring:
            interval = st.select_slider(
                "Monitoring Interval",
                options=[15, 30, 60, 120, 240],
                value=60,
                format_func=lambda x: f"{x} minutes"
            )
        else:
            interval = 60

        submitted = st.form_submit_button("Add User", use_container_width=True)

        if submitted:
            if not username or len(username) < 2:
                st.error("Please enter a valid username")
                return

            username = username.strip().lower().replace("@", "")

            db = get_session_db()
            twitter_db = TwitterDatabase(db)

            existing = twitter_db.get_user(username)
            if existing:
                st.warning(f"User **@{username}** already exists!")
                return

            user_id = twitter_db.add_user(username)

            if collect_immediately:
                with st.spinner(f"Collecting tweets for **@{username}**..."):
                    success = collect_twitter_data(username, db)
                    if success:
                        st.success(f"✅ Successfully added and collected data for **@{username}**")
                    else:
                        st.error("Added user but failed to collect data")

            if start_monitoring:
                job_id = JobManager.add_job(
                    platform="twitter",
                    entity_id=user_id,
                    entity_name=username,
                    interval_minutes=interval
                )
                twitter_db.set_monitoring(user_id, True)
                st.success(f"✅ Started monitoring job (every {interval} minutes)")

            st.balloons()
            st.rerun()


def show_users_list():
    st.subheader("📋 Monitored Users")

    db = get_session_db()
    twitter_db = TwitterDatabase(db)

    users = twitter_db.get_all_users()

    if not users:
        st.info("No users added yet. Add a user above to get started!")
        return

    st.write(f"**Total users:** {len(users)}")

    for user in users:
        user_id = user['id']
        username = user['username']

        with st.expander(f"🐦 **@{username}**", expanded=False):
            stats = twitter_db.get_user_statistics(user_id)

            col1, col2, col3 = st.columns(3)

            with col1:
                if stats and stats['total_tweets']:
                    st.metric("Total Tweets", stats['total_tweets'])
                    st.metric("Total Likes", f"{stats['total_likes']:,}")
                else:
                    st.warning("No data collected yet")

            with col2:
                if stats and stats['total_tweets']:
                    st.metric("Total Retweets", f"{stats['total_retweets']:,}")
                    st.metric("Avg Likes/Tweet", f"{int(stats['avg_likes_per_tweet']):,}")

            with col3:
                jobs = JobManager.get_jobs_by_platform("twitter")
                user_jobs = [j for j in jobs if j.entity_id == user_id]

                if user_jobs and user_jobs[0].is_active:
                    st.success("✅ Monitoring")
                elif user_jobs:
                    st.warning("⏸️ Paused")

            st.divider()

            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button(f"🔄 Collect Data", key=f"collect_{user_id}"):
                    with st.spinner("Collecting..."):
                        success = collect_twitter_data(username, db)
                        if success:
                            st.success("Data collected!")
                            st.rerun()

            with action_col2:
                user_jobs = [j for j in JobManager.get_jobs_by_platform("twitter") if j.entity_id == user_id]
                if user_jobs:
                    job = user_jobs[0]
                    if job.is_active:
                        if st.button(f"⏸️ Pause", key=f"pause_{user_id}"):
                            JobManager.pause_job(job.id)
                            twitter_db.set_monitoring(user_id, False)
                            st.rerun()
                    else:
                        if st.button(f"▶️ Resume", key=f"resume_{user_id}"):
                            JobManager.resume_job(job.id)
                            twitter_db.set_monitoring(user_id, True)
                            st.rerun()
                else:
                    if st.button(f"▶️ Start Job", key=f"start_{user_id}"):
                        JobManager.add_job("twitter", user_id, username, 60)
                        twitter_db.set_monitoring(user_id, True)
                        st.rerun()

            with action_col3:
                if st.button(f"📊 View Data", key=f"view_{user_id}"):
                    st.session_state.selected_user = user_id
                    st.rerun()

            with action_col4:
                if st.button(f"🗑️ Delete", key=f"delete_{user_id}"):
                    if st.session_state.get(f"confirm_delete_{user_id}", False):
                        user_jobs = [j for j in JobManager.get_jobs_by_platform("twitter") if j.entity_id == user_id]
                        if user_jobs:
                            JobManager.remove_job(user_jobs[0].id)
                        twitter_db.delete_user(user_id)
                        st.success("User deleted")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{user_id}"] = True
                        st.warning("Click again to confirm")


def show_user_details(user_id: int):
    db = get_session_db()
    twitter_db = TwitterDatabase(db)

    users = twitter_db.get_all_users()
    user = next((u for u in users if u['id'] == user_id), None)

    if not user:
        st.error("User not found")
        st.session_state.selected_user = None
        return

    username = user['username']

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📊 Data for **@{username}**")
    with col2:
        if st.button("← Back to List"):
            st.session_state.selected_user = None
            st.rerun()

    tweets = twitter_db.get_tweets(user_id, limit=500)

    if not tweets:
        st.warning("No data collected yet")
        return

    df = pd.DataFrame(tweets)
    df['created_at'] = pd.to_datetime(df['created_at'])

    stats = twitter_db.get_user_statistics(user_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tweets", stats['total_tweets'])
    with col2:
        st.metric("Total Likes", f"{stats['total_likes']:,}")
    with col3:
        st.metric("Total Retweets", f"{stats['total_retweets']:,}")
    with col4:
        st.metric("Avg Likes/Tweet", f"{int(stats['avg_likes_per_tweet']):,}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📈 Engagement Over Time", "🏆 Top Tweets", "📋 All Tweets"])

    with tab1:
        st.subheader("Engagement Over Time")

        fig = px.line(
            df.sort_values('created_at'),
            x='created_at',
            y='like_count',
            title="Likes Over Time",
            labels={'like_count': 'Likes', 'created_at': 'Date'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Top Tweets by Likes")

        top_tweets = df.nlargest(10, 'like_count')

        for idx, tweet in top_tweets.iterrows():
            with st.container():
                st.write(f"**{tweet['text'][:200]}...**" if len(tweet['text']) > 200 else f"**{tweet['text']}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"❤️ {tweet['like_count']:,} likes")
                with col2:
                    st.caption(f"🔁 {tweet['retweet_count']:,} retweets")
                with col3:
                    st.caption(f"💬 {tweet['reply_count']:,} replies")
                with col4:
                    st.caption(f"📅 {pd.to_datetime(tweet['created_at']).strftime('%Y-%m-%d')}")
                st.divider()

    with tab3:
        st.subheader("All Tweets")

        display_df = df[['created_at', 'text', 'like_count', 'retweet_count', 'reply_count']].copy()
        display_df = display_df.sort_values('created_at', ascending=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download as CSV",
            data=csv,
            file_name=f"twitter_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def main():
    st.title("🐦 Twitter Monitoring")

    check_credentials()

    if st.session_state.get('selected_user'):
        show_user_details(st.session_state.selected_user)
    else:
        show_add_user()
        st.divider()
        show_users_list()


if __name__ == "__main__":
    main()
