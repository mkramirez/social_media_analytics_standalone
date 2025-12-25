"""
Export Page

Download your data before closing the browser.
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db


st.set_page_config(page_title="Data Export", page_icon="📄", layout="wide")


def main():
    st.title("Export Data")

    st.write("""
    **Important:** All data is stored in memory and will be deleted when you close this browser tab.

    Use this page to download your data before closing the application.
    """)

    db = get_session_db()
    stats = db.get_statistics()

    st.divider()

    # Database overview
    st.subheader("Database Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_records = stats['twitch_records'] + stats['twitter_tweets'] + stats['youtube_videos'] + stats['reddit_posts']

    with col1:
        st.metric("Twitch Records", f"{stats['twitch_records']:,}")
    with col2:
        st.metric("Twitter Tweets", f"{stats['twitter_tweets']:,}")
    with col3:
        st.metric("YouTube Videos", f"{stats['youtube_videos']:,}")
    with col4:
        st.metric("Reddit Posts", f"{stats['reddit_posts']:,}")

    st.metric("**Total Records**", f"{total_records:,}")

    st.divider()

    # Export options
    st.subheader("Export Options")

    tab1, tab2, tab3 = st.tabs(["Complete Database", "CSV Exports", "Platform-Specific"])

    with tab1:
        st.write("""
        **Complete Database Export**

        Download the entire SQLite database as a SQL dump file.
        You can later import this into another SQLite database or use it for backup.
        """)

        if st.button("Download Complete Database (SQL)", use_container_width=True):
            try:
                sql_dump = db.export_to_file()

                st.download_button(
                    label="Download Database.sql",
                    data=sql_dump,
                    file_name=f"social_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                    mime="application/sql",
                    use_container_width=True
                )

                st.success("Database export ready for download!")

            except Exception as e:
                st.error(f"Error exporting database: {e}")

    with tab2:
        st.write("**Export all data as CSV files**")

        # Twitch
        if stats['twitch_records'] > 0:
            st.write("**Twitch Data**")

            db.execute("""
                SELECT
                    c.channel_name,
                    r.timestamp,
                    r.is_live,
                    r.title,
                    r.game_name,
                    r.viewer_count,
                    r.started_at
                FROM twitch_stream_records r
                JOIN twitch_channels c ON r.channel_id = c.id
                ORDER BY r.timestamp DESC
            """)
            twitch_data = db.fetchall()

            if twitch_data:
                df = pd.DataFrame(twitch_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    f"Download Twitch Data ({len(twitch_data)} records)",
                    data=csv,
                    file_name=f"twitch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        # Twitter
        if stats['twitter_tweets'] > 0:
            st.write("**Twitter Data**")

            db.execute("""
                SELECT
                    u.username,
                    t.created_at,
                    t.text,
                    t.like_count,
                    t.retweet_count,
                    t.reply_count,
                    t.quote_count
                FROM twitter_tweets t
                JOIN twitter_users u ON t.user_id = u.id
                ORDER BY t.created_at DESC
            """)
            twitter_data = db.fetchall()

            if twitter_data:
                df = pd.DataFrame(twitter_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    f"Download Twitter Data ({len(twitter_data)} tweets)",
                    data=csv,
                    file_name=f"twitter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        # YouTube
        if stats['youtube_videos'] > 0:
            st.write("**YouTube Data**")

            db.execute("""
                SELECT
                    c.channel_name,
                    v.title,
                    v.published_at,
                    v.view_count,
                    v.like_count,
                    v.comment_count
                FROM youtube_videos v
                JOIN youtube_channels c ON v.channel_id = c.id
                ORDER BY v.published_at DESC
            """)
            youtube_data = db.fetchall()

            if youtube_data:
                df = pd.DataFrame(youtube_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    f"Download YouTube Data ({len(youtube_data)} videos)",
                    data=csv,
                    file_name=f"youtube_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        # Reddit
        if stats['reddit_posts'] > 0:
            st.write("**Reddit Data**")

            db.execute("""
                SELECT
                    s.subreddit_name,
                    p.title,
                    p.author,
                    p.created_utc,
                    p.score,
                    p.num_comments,
                    p.upvote_ratio
                FROM reddit_posts p
                JOIN reddit_subreddits s ON p.subreddit_id = s.id
                ORDER BY p.created_utc DESC
            """)
            reddit_data = db.fetchall()

            if reddit_data:
                df = pd.DataFrame(reddit_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    f"Download Reddit Data ({len(reddit_data)} posts)",
                    data=csv,
                    file_name=f"reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        if total_records == 0:
            st.info("No data to export yet. Start monitoring some entities first!")

    with tab3:
        st.write("**Platform-Specific Exports**")

        st.info("Use the individual platform pages to export data for specific channels/users/subreddits with charts and visualizations.")

        st.write("Go to:")
        st.write("- **Twitch** page → View channel → Download CSV")
        st.write("- **Twitter** page → View user → Download CSV")
        st.write("- **YouTube** page → View channel → Download CSV")
        st.write("- **Reddit** page → View subreddit → Download CSV")

    st.divider()

    # Tips
    st.subheader("Tips")

    st.write("""
    - **Download regularly:** Export your data periodically during long sessions
    - **SQL dump:** Contains the complete database structure and data
    - **CSV files:** Easy to open in Excel, Google Sheets, or data analysis tools
    - **Platform-specific:** Get detailed exports with visualizations from platform pages
    """)


if __name__ == "__main__":
    main()
