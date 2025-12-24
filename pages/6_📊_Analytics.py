"""
Analytics Page

Cross-platform analytics and insights.
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db


st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment using TextBlob."""
    try:
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "polarity": polarity,
            "sentiment": sentiment
        }
    except:
        return {"polarity": 0, "sentiment": "neutral"}


def main():
    st.title("📊 Analytics Dashboard")

    db = get_session_db()
    stats = db.get_statistics()

    # Overview
    st.subheader("📈 Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_records = stats['twitch_records'] + stats['twitter_tweets'] + stats['youtube_videos'] + stats['reddit_posts']
    total_entities = stats['twitch_channels'] + stats['twitter_users'] + stats['youtube_channels'] + stats['reddit_subreddits']

    with col1:
        st.metric("Total Entities", total_entities)
    with col2:
        st.metric("Total Records", f"{total_records:,}")
    with col3:
        configured = len([p for p, c in st.session_state.get('credential_manager', {}).items() if c])
        st.metric("Platforms Configured", f"{configured}/4")
    with col4:
        from utils.job_manager import JobManager
        job_stats = JobManager.get_job_statistics()
        st.metric("Active Jobs", job_stats['active_jobs'])

    st.divider()

    # Platform breakdown
    st.subheader("🌐 Platform Breakdown")

    platform_data = {
        'Platform': ['Twitch', 'Twitter', 'YouTube', 'Reddit'],
        'Entities': [stats['twitch_channels'], stats['twitter_users'], stats['youtube_channels'], stats['reddit_subreddits']],
        'Records': [stats['twitch_records'], stats['twitter_tweets'], stats['youtube_videos'], stats['reddit_posts']]
    }

    df_platforms = pd.DataFrame(platform_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(df_platforms, x='Platform', y='Entities', title="Entities by Platform", color='Platform')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(df_platforms, values='Records', names='Platform', title="Records by Platform")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Twitter sentiment analysis
    if stats['twitter_tweets'] > 0:
        st.subheader("💭 Twitter Sentiment Analysis")

        db.execute("""
            SELECT text, like_count, retweet_count, created_at
            FROM twitter_tweets
            ORDER BY created_at DESC
            LIMIT 100
        """)
        tweets = db.fetchall()

        if tweets:
            sentiments = []
            for tweet in tweets:
                sentiment_data = analyze_sentiment(tweet['text'])
                sentiments.append({
                    'text': tweet['text'][:100],
                    'sentiment': sentiment_data['sentiment'],
                    'polarity': sentiment_data['polarity'],
                    'likes': tweet['like_count'],
                    'retweets': tweet['retweet_count']
                })

            df_sentiment = pd.DataFrame(sentiments)

            col1, col2 = st.columns([1, 2])

            with col1:
                sentiment_counts = df_sentiment['sentiment'].value_counts()

                st.write("**Sentiment Distribution:**")
                for sentiment, count in sentiment_counts.items():
                    emoji = "😊" if sentiment == "positive" else "😐" if sentiment == "neutral" else "😞"
                    st.write(f"{emoji} **{sentiment.title()}:** {count} ({count/len(df_sentiment)*100:.1f}%)")

            with col2:
                fig = px.histogram(df_sentiment, x='sentiment', title="Sentiment Distribution",
                                 color='sentiment',
                                 color_discrete_map={'positive': 'green', 'neutral': 'gray', 'negative': 'red'})
                st.plotly_chart(fig, use_container_width=True)

            # Top positive and negative tweets
            st.write("**Most Positive Tweet:**")
            most_positive = df_sentiment.nlargest(1, 'polarity').iloc[0]
            st.info(f"💚 {most_positive['text']}... (Polarity: {most_positive['polarity']:.2f})")

            st.write("**Most Negative Tweet:**")
            most_negative = df_sentiment.nsmallest(1, 'polarity').iloc[0]
            st.warning(f"💔 {most_negative['text']}... (Polarity: {most_negative['polarity']:.2f})")

    st.divider()

    # Engagement metrics
    st.subheader("📈 Engagement Metrics")

    tab1, tab2, tab3 = st.tabs(["Twitter", "YouTube", "Reddit"])

    with tab1:
        if stats['twitter_tweets'] > 0:
            db.execute("""
                SELECT
                    AVG(like_count) as avg_likes,
                    AVG(retweet_count) as avg_retweets,
                    MAX(like_count) as max_likes,
                    SUM(like_count) as total_likes
                FROM twitter_tweets
            """)
            twitter_stats = db.fetchone()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Likes", f"{int(twitter_stats['avg_likes']):,}")
            with col2:
                st.metric("Avg Retweets", f"{int(twitter_stats['avg_retweets']):,}")
            with col3:
                st.metric("Max Likes", f"{twitter_stats['max_likes']:,}")
            with col4:
                st.metric("Total Likes", f"{twitter_stats['total_likes']:,}")
        else:
            st.info("No Twitter data yet")

    with tab2:
        if stats['youtube_videos'] > 0:
            db.execute("""
                SELECT
                    AVG(view_count) as avg_views,
                    AVG(like_count) as avg_likes,
                    MAX(view_count) as max_views,
                    SUM(view_count) as total_views
                FROM youtube_videos
            """)
            youtube_stats = db.fetchone()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Views", f"{int(youtube_stats['avg_views']):,}")
            with col2:
                st.metric("Avg Likes", f"{int(youtube_stats['avg_likes']):,}")
            with col3:
                st.metric("Max Views", f"{youtube_stats['max_views']:,}")
            with col4:
                st.metric("Total Views", f"{youtube_stats['total_views']:,}")
        else:
            st.info("No YouTube data yet")

    with tab3:
        if stats['reddit_posts'] > 0:
            db.execute("""
                SELECT
                    AVG(score) as avg_score,
                    AVG(num_comments) as avg_comments,
                    AVG(upvote_ratio) as avg_upvote_ratio,
                    MAX(score) as max_score
                FROM reddit_posts
            """)
            reddit_stats = db.fetchone()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Score", f"{int(reddit_stats['avg_score']):,}")
            with col2:
                st.metric("Avg Comments", f"{int(reddit_stats['avg_comments']):,}")
            with col3:
                st.metric("Avg Upvote %", f"{reddit_stats['avg_upvote_ratio']*100:.1f}%")
            with col4:
                st.metric("Max Score", f"{reddit_stats['max_score']:,}")
        else:
            st.info("No Reddit data yet")


if __name__ == "__main__":
    main()
