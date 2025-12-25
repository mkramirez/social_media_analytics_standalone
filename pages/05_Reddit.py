"""
Reddit Monitoring Page
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
from src.platforms.reddit_integration import RedditDatabase, collect_reddit_data


st.set_page_config(page_title="Reddit Monitoring", page_icon="🔴", layout="wide")


def check_credentials():
    if not CredentialManager.has_reddit_credentials():
        st.warning("⚠️ Reddit credentials not configured")
        st.info("Please go to the **Setup** page")
        st.stop()


def main():
    st.title("🔴 Reddit Monitoring")
    check_credentials()

    db = get_session_db()
    reddit_db = RedditDatabase(db)

    if st.session_state.get('selected_subreddit'):
        show_subreddit_details(st.session_state.selected_subreddit, reddit_db, db)
    else:
        show_add_subreddit(reddit_db, db)
        st.divider()
        show_subreddits_list(reddit_db)


def show_add_subreddit(reddit_db, db):
    st.subheader("📝 Add Subreddit")

    with st.form("add_subreddit_form"):
        subreddit_name = st.text_input("Subreddit Name", placeholder="funny, gaming, news (without r/)")

        col1, col2 = st.columns(2)
        with col1:
            collect_immediately = st.checkbox("Collect data immediately", value=True)
        with col2:
            start_monitoring = st.checkbox("Start monitoring job", value=False)

        interval = 30
        if start_monitoring:
            interval = st.select_slider("Interval", options=[15, 30, 60, 120], value=30, format_func=lambda x: f"{x} min")

        if st.form_submit_button("Add Subreddit", use_container_width=True):
            if not subreddit_name:
                st.error("Enter subreddit name")
                return

            subreddit_name = subreddit_name.strip().lower().replace("r/", "")

            if reddit_db.get_subreddit(subreddit_name):
                st.warning(f"r/{subreddit_name} already exists!")
                return

            subreddit_id = reddit_db.add_subreddit(subreddit_name)

            if collect_immediately:
                with st.spinner(f"Collecting posts from r/{subreddit_name}..."):
                    success = collect_reddit_data(subreddit_name, db, limit=25, sort="hot")
                    if success:
                        st.success(f"✅ Added r/{subreddit_name}")
                        if start_monitoring:
                            JobManager.add_job("reddit", subreddit_id, subreddit_name, interval)
                            reddit_db.set_monitoring(subreddit_id, True)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to collect data")


def show_subreddits_list(reddit_db):
    st.subheader("📋 Monitored Subreddits")

    subreddits = reddit_db.get_all_subreddits()

    if not subreddits:
        st.info("No subreddits added yet")
        return

    for subreddit in subreddits:
        with st.expander(f"🔴 **r/{subreddit['subreddit_name']}**"):
            stats = reddit_db.get_subreddit_statistics(subreddit['id'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Posts", stats['total_posts'] if stats else 0)
            with col2:
                st.metric("Total Score", f"{stats['total_score']:,}" if stats and stats['total_score'] else "0")
            with col3:
                jobs = [j for j in JobManager.get_jobs_by_platform("reddit") if j.entity_id == subreddit['id']]
                if jobs and jobs[0].is_active:
                    st.success("✅ Monitoring")

            st.divider()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🔄 Collect", key=f"collect_r_{subreddit['id']}"):
                    with st.spinner("Collecting..."):
                        collect_reddit_data(subreddit['subreddit_name'], db, limit=25, sort="hot")
                        st.rerun()
            with c2:
                jobs = [j for j in JobManager.get_jobs_by_platform("reddit") if j.entity_id == subreddit['id']]
                if jobs:
                    if jobs[0].is_active:
                        if st.button("⏸️ Pause", key=f"pause_r_{subreddit['id']}"):
                            JobManager.pause_job(jobs[0].id)
                            st.rerun()
                    else:
                        if st.button("▶️ Resume", key=f"resume_r_{subreddit['id']}"):
                            JobManager.resume_job(jobs[0].id)
                            st.rerun()
                else:
                    if st.button("▶️ Start", key=f"start_r_{subreddit['id']}"):
                        JobManager.add_job("reddit", subreddit['id'], subreddit['subreddit_name'], 30)
                        st.rerun()
            with c3:
                if st.button("📊 View", key=f"view_r_{subreddit['id']}"):
                    st.session_state.selected_subreddit = subreddit['id']
                    st.rerun()
            with c4:
                if st.button("🗑️ Delete", key=f"del_r_{subreddit['id']}"):
                    if st.session_state.get(f"confirm_del_r_{subreddit['id']}", False):
                        jobs = [j for j in JobManager.get_jobs_by_platform("reddit") if j.entity_id == subreddit['id']]
                        if jobs:
                            JobManager.remove_job(jobs[0].id)
                        reddit_db.delete_subreddit(subreddit['id'])
                        st.rerun()
                    else:
                        st.session_state[f"confirm_del_r_{subreddit['id']}"] = True
                        st.warning("Click again")


def show_subreddit_details(subreddit_id, reddit_db, db):
    subreddits = reddit_db.get_all_subreddits()
    subreddit = next((s for s in subreddits if s['id'] == subreddit_id), None)

    if not subreddit:
        st.session_state.selected_subreddit = None
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📊 r/{subreddit['subreddit_name']}")
    with col2:
        if st.button("← Back"):
            st.session_state.selected_subreddit = None
            st.rerun()

    posts = reddit_db.get_posts(subreddit_id, limit=500)

    if not posts:
        st.warning("No posts yet")
        return

    df = pd.DataFrame(posts)
    df['created_utc'] = pd.to_datetime(df['created_utc'])

    stats = reddit_db.get_subreddit_statistics(subreddit_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Posts", stats['total_posts'])
    with col2:
        st.metric("Total Score", f"{stats['total_score']:,}")
    with col3:
        st.metric("Avg Score", f"{int(stats['avg_score_per_post']):,}")
    with col4:
        st.metric("Avg Upvote %", f"{stats['avg_upvote_ratio']*100:.1f}%")

    st.divider()

    tab1, tab2 = st.tabs(["🏆 Top Posts", "📋 All Posts"])

    with tab1:
        st.subheader("Top Posts by Score")

        top_posts = df.nlargest(10, 'score')

        for idx, post in top_posts.iterrows():
            with st.container():
                st.write(f"**{post['title']}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"⬆️ {post['score']:,} score")
                with col2:
                    st.caption(f"💬 {post['num_comments']:,} comments")
                with col3:
                    st.caption(f"📈 {post['upvote_ratio']*100:.0f}% upvoted")
                with col4:
                    st.caption(f"👤 u/{post['author']}")
                st.divider()

    with tab2:
        st.subheader("All Posts")

        display_df = df[['created_utc', 'title', 'author', 'score', 'num_comments', 'upvote_ratio']].sort_values('created_utc', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name=f"reddit_{subreddit['subreddit_name']}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


if __name__ == "__main__":
    main()
