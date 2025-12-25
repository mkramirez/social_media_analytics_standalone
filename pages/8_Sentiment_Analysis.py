"""
Sentiment Analysis Page

Analyze sentiment of collected chat messages, tweets, and comments.
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session_db import get_session_db


st.set_page_config(page_title="Sentiment Analysis", layout="wide")


def analyze_sentiment_textblob(text: str) -> dict:
    """
    Analyze sentiment using TextBlob (fallback method).
    Returns polarity (-1 to 1) and subjectivity (0 to 1).
    """
    try:
        from textblob import TextBlob

        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Classify sentiment
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment
        }
    except ImportError:
        st.error("TextBlob is not installed. Install it with: pip install textblob")
        return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
    except Exception as e:
        return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}


def analyze_sentiment_claude(text: str) -> dict:
    """
    Analyze sentiment using Claude API.
    Returns polarity (-1 to 1), subjectivity (0 to 1), and sentiment classification.
    """
    try:
        from anthropic import Anthropic
        from utils.credential_manager import CredentialManager

        # Get API key
        creds = CredentialManager.get_anthropic_credentials()
        if not creds:
            st.error("Anthropic API key not configured. Please configure it in the Setup page.")
            return {'polarity': 0, 'subjectivity': 0.5, 'sentiment': 'neutral'}

        # Initialize client
        client = Anthropic(api_key=creds.api_key)

        # Create prompt for sentiment analysis
        prompt = f"""Analyze the sentiment of the following text and provide:
1. A sentiment classification (positive, negative, or neutral)
2. A polarity score from -1 (very negative) to +1 (very positive)
3. A subjectivity score from 0 (very objective) to 1 (very subjective)

Text: "{text}"

Respond ONLY with a JSON object in this exact format:
{{"sentiment": "positive|negative|neutral", "polarity": 0.0, "subjectivity": 0.0}}

Be concise and accurate. Consider the overall tone, emotions, and context."""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        import json
        response_text = message.content[0].text.strip()

        # Extract JSON from response (in case Claude adds explanatory text)
        if '{' in response_text and '}' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rindex('}') + 1
            response_text = response_text[json_start:json_end]

        result = json.loads(response_text)

        return {
            'polarity': float(result.get('polarity', 0)),
            'subjectivity': float(result.get('subjectivity', 0.5)),
            'sentiment': result.get('sentiment', 'neutral').lower()
        }

    except ImportError:
        st.error("Anthropic package is not installed. Install it with: pip install anthropic")
        return {'polarity': 0, 'subjectivity': 0.5, 'sentiment': 'neutral'}
    except Exception as e:
        st.warning(f"Claude API error: {str(e)}. Falling back to TextBlob.")
        return analyze_sentiment_textblob(text)


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment using Claude API if available, otherwise fall back to TextBlob.
    """
    from utils.credential_manager import CredentialManager

    if CredentialManager.has_anthropic_credentials():
        return analyze_sentiment_claude(text)
    else:
        return analyze_sentiment_textblob(text)


def save_sentiment_result(db, table: str, item_id: int, result: dict, method: str = 'textblob'):
    """
    Save sentiment analysis result to database.

    Args:
        db: Database connection
        table: Sentiment table name (sentiment_twitch_chat, sentiment_twitter, sentiment_reddit)
        item_id: ID of the analyzed item
        result: Sentiment analysis result dict
        method: Analysis method used ('claude' or 'textblob')
    """
    # Check if already analyzed
    if table == 'sentiment_twitch_chat':
        id_col = 'message_id'
    elif table == 'sentiment_twitter':
        id_col = 'tweet_id'
    else:
        id_col = 'post_id'

    existing = db.execute_query(f"SELECT id FROM {table} WHERE {id_col} = ?", (item_id,))

    if existing:
        # Update existing record
        db.execute(f"""
            UPDATE {table}
            SET polarity = ?, subjectivity = ?, sentiment = ?,
                analyzed_at = CURRENT_TIMESTAMP, analysis_method = ?
            WHERE {id_col} = ?
        """, (result['polarity'], result['subjectivity'], result['sentiment'], method, item_id))
    else:
        # Insert new record
        db.execute(f"""
            INSERT INTO {table} ({id_col}, polarity, subjectivity, sentiment, analysis_method)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, result['polarity'], result['subjectivity'], result['sentiment'], method))

    db.commit()


def analyze_twitch_chat():
    """Analyze Twitch chat messages."""
    st.subheader("Twitch Chat Sentiment")

    db = get_session_db()
    from utils.credential_manager import CredentialManager

    # Get chat messages with IDs
    chat_data = db.execute_query("""
        SELECT tcm.id, tcm.message, tcm.username, tcm.timestamp, tc.channel_name
        FROM twitch_chat_messages tcm
        JOIN twitch_stream_records tsr ON tcm.record_id = tsr.id
        JOIN twitch_channels tc ON tsr.channel_id = tc.id
        ORDER BY tcm.timestamp DESC
        LIMIT 1000
    """)

    if not chat_data:
        st.info("No Twitch chat messages collected yet. Enable chat collection in Twitch page settings.")
        return

    df = pd.DataFrame(chat_data, columns=['id', 'message', 'username', 'timestamp', 'channel'])

    # Analyze sentiment and save to database
    analysis_method = 'claude' if CredentialManager.has_anthropic_credentials() else 'textblob'

    with st.spinner(f"Analyzing sentiment using {analysis_method.upper()}..."):
        sentiments = []
        for idx, row in df.iterrows():
            result = analyze_sentiment(row['message'])
            sentiments.append(result)

            # Save to database
            save_sentiment_result(db, 'sentiment_twitch_chat', row['id'], result, analysis_method)

        df['polarity'] = [s['polarity'] for s in sentiments]
        df['sentiment'] = [s['sentiment'] for s in sentiments]

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Messages", len(df))

    with col2:
        positive_pct = (df['sentiment'] == 'positive').sum() / len(df) * 100
        st.metric("Positive", f"{positive_pct:.1f}%")

    with col3:
        neutral_pct = (df['sentiment'] == 'neutral').sum() / len(df) * 100
        st.metric("Neutral", f"{neutral_pct:.1f}%")

    with col4:
        negative_pct = (df['sentiment'] == 'negative').sum() / len(df) * 100
        st.metric("Negative", f"{negative_pct:.1f}%")

    # Sentiment distribution pie chart
    sentiment_counts = df['sentiment'].value_counts()

    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title="Sentiment Distribution",
        color=sentiment_counts.index,
        color_discrete_map={'positive': '#00cc00', 'neutral': '#808080', 'negative': '#cc0000'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Most positive and negative messages
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Most Positive Messages:**")
        top_positive = df.nlargest(5, 'polarity')[['username', 'message', 'polarity']]
        for idx, row in top_positive.iterrows():
            st.success(f"**@{row['username']}**: {row['message'][:100]}... (Score: {row['polarity']:.2f})")

    with col2:
        st.write("**Most Negative Messages:**")
        top_negative = df.nsmallest(5, 'polarity')[['username', 'message', 'polarity']]
        for idx, row in top_negative.iterrows():
            st.error(f"**@{row['username']}**: {row['message'][:100]}... (Score: {row['polarity']:.2f})")


def analyze_twitter():
    """Analyze Twitter tweets."""
    st.subheader("Twitter Sentiment")

    db = get_session_db()
    from utils.credential_manager import CredentialManager

    # Get tweets with IDs
    tweets = db.execute_query("""
        SELECT t.id, t.text, t.created_at, tu.username, t.like_count, t.retweet_count
        FROM twitter_tweets t
        JOIN twitter_users tu ON t.user_id = tu.id
        ORDER BY t.created_at DESC
        LIMIT 500
    """)

    if not tweets:
        st.info("No Twitter data collected yet.")
        return

    df = pd.DataFrame(tweets, columns=['id', 'text', 'created_at', 'username', 'likes', 'retweets'])

    # Analyze sentiment and save to database
    analysis_method = 'claude' if CredentialManager.has_anthropic_credentials() else 'textblob'

    with st.spinner(f"Analyzing sentiment using {analysis_method.upper()}..."):
        sentiments = []
        for idx, row in df.iterrows():
            result = analyze_sentiment(row['text'])
            sentiments.append(result)

            # Save to database
            save_sentiment_result(db, 'sentiment_twitter', row['id'], result, analysis_method)

        df['polarity'] = [s['polarity'] for s in sentiments]
        df['sentiment'] = [s['sentiment'] for s in sentiments]

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tweets", len(df))

    with col2:
        positive_pct = (df['sentiment'] == 'positive').sum() / len(df) * 100
        st.metric("Positive", f"{positive_pct:.1f}%")

    with col3:
        neutral_pct = (df['sentiment'] == 'neutral').sum() / len(df) * 100
        st.metric("Neutral", f"{neutral_pct:.1f}%")

    with col4:
        negative_pct = (df['sentiment'] == 'negative').sum() / len(df) * 100
        st.metric("Negative", f"{negative_pct:.1f}%")

    # Sentiment over time
    df['created_at'] = pd.to_datetime(df['created_at'])
    df_time = df.groupby([pd.Grouper(key='created_at', freq='1H'), 'sentiment']).size().reset_index(name='count')

    fig = px.line(
        df_time,
        x='created_at',
        y='count',
        color='sentiment',
        title="Sentiment Over Time",
        color_discrete_map={'positive': '#00cc00', 'neutral': '#808080', 'negative': '#cc0000'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Most engaging tweets by sentiment
    st.write("**Most Engaging Tweets by Sentiment:**")

    for sentiment_type in ['positive', 'negative']:
        sentiment_df = df[df['sentiment'] == sentiment_type].nlargest(3, 'likes')

        if len(sentiment_df) > 0:
            st.write(f"\n**{sentiment_type.title()} Tweets:**")
            for idx, row in sentiment_df.iterrows():
                engagement = row['likes'] + row['retweets']
                if sentiment_type == 'positive':
                    st.success(f"**@{row['username']}**: {row['text'][:150]}... \n(Likes: {row['likes']}, RT: {row['retweets']}, Score: {row['polarity']:.2f})")
                else:
                    st.error(f"**@{row['username']}**: {row['text'][:150]}... \n(Likes: {row['likes']}, RT: {row['retweets']}, Score: {row['polarity']:.2f})")


def analyze_reddit():
    """Analyze Reddit posts."""
    st.subheader("Reddit Sentiment")

    db = get_session_db()
    from utils.credential_manager import CredentialManager

    # Get Reddit posts with IDs
    posts = db.execute_query("""
        SELECT rp.id, rp.title, rp.selftext, rp.score, rp.num_comments, rp.created_utc, rs.subreddit_name
        FROM reddit_posts rp
        JOIN reddit_subreddits rs ON rp.subreddit_id = rs.id
        ORDER BY rp.created_utc DESC
        LIMIT 500
    """)

    if not posts:
        st.info("No Reddit data collected yet.")
        return

    df = pd.DataFrame(posts, columns=['id', 'title', 'selftext', 'score', 'num_comments', 'created_utc', 'subreddit'])

    # Combine title and text for sentiment analysis
    df['full_text'] = df['title'] + ' ' + df['selftext'].fillna('')

    # Analyze sentiment and save to database
    analysis_method = 'claude' if CredentialManager.has_anthropic_credentials() else 'textblob'

    with st.spinner(f"Analyzing sentiment using {analysis_method.upper()}..."):
        sentiments = []
        for idx, row in df.iterrows():
            result = analyze_sentiment(row['full_text'])
            sentiments.append(result)

            # Save to database
            save_sentiment_result(db, 'sentiment_reddit', row['id'], result, analysis_method)

        df['polarity'] = [s['polarity'] for s in sentiments]
        df['sentiment'] = [s['sentiment'] for s in sentiments]

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Posts", len(df))

    with col2:
        positive_pct = (df['sentiment'] == 'positive').sum() / len(df) * 100
        st.metric("Positive", f"{positive_pct:.1f}%")

    with col3:
        neutral_pct = (df['sentiment'] == 'neutral').sum() / len(df) * 100
        st.metric("Neutral", f"{neutral_pct:.1f}%")

    with col4:
        negative_pct = (df['sentiment'] == 'negative').sum() / len(df) * 100
        st.metric("Negative", f"{negative_pct:.1f}%")

    # Sentiment by subreddit
    sentiment_by_sub = df.groupby(['subreddit', 'sentiment']).size().reset_index(name='count')

    fig = px.bar(
        sentiment_by_sub,
        x='subreddit',
        y='count',
        color='sentiment',
        title="Sentiment by Subreddit",
        color_discrete_map={'positive': '#00cc00', 'neutral': '#808080', 'negative': '#cc0000'},
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top posts by sentiment
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Most Positive Posts:**")
        top_positive = df.nlargest(5, 'polarity')[['title', 'subreddit', 'score', 'polarity']]
        for idx, row in top_positive.iterrows():
            st.success(f"**r/{row['subreddit']}**: {row['title'][:100]}... \n(Score: {row['score']}, Sentiment: {row['polarity']:.2f})")

    with col2:
        st.write("**Most Negative Posts:**")
        top_negative = df.nsmallest(5, 'polarity')[['title', 'subreddit', 'score', 'polarity']]
        for idx, row in top_negative.iterrows():
            st.error(f"**r/{row['subreddit']}**: {row['title'][:100]}... \n(Score: {row['score']}, Sentiment: {row['polarity']:.2f})")


def main():
    st.title("Sentiment Analysis")

    st.write("""
    Analyze the sentiment of collected data across all platforms.
    Sentiment is classified as Positive, Neutral, or Negative based on the content.
    """)

    # Platform selector
    st.divider()

    platform = st.selectbox(
        "Select Platform",
        ["All Platforms", "Twitch Chat", "Twitter", "Reddit"],
        help="Choose which platform's data to analyze"
    )

    st.divider()

    if platform == "All Platforms":
        # Show all platforms
        analyze_twitch_chat()
        st.divider()
        analyze_twitter()
        st.divider()
        analyze_reddit()
    elif platform == "Twitch Chat":
        analyze_twitch_chat()
    elif platform == "Twitter":
        analyze_twitter()
    elif platform == "Reddit":
        analyze_reddit()

    st.divider()

    # Info section
    from utils.credential_manager import CredentialManager

    if CredentialManager.has_anthropic_credentials():
        st.info("""
        **About Sentiment Analysis:**

        - **Polarity**: Ranges from -1 (negative) to +1 (positive)
        - **Positive**: Polarity > 0.1
        - **Neutral**: Polarity between -0.1 and 0.1
        - **Negative**: Polarity < -0.1

        Sentiment analysis uses **Claude API** for advanced, context-aware sentiment detection.
        Claude provides more nuanced analysis than traditional methods.
        """)
    else:
        st.info("""
        **About Sentiment Analysis:**

        - **Polarity**: Ranges from -1 (negative) to +1 (positive)
        - **Positive**: Polarity > 0.1
        - **Neutral**: Polarity between -0.1 and 0.1
        - **Negative**: Polarity < -0.1

        Sentiment analysis uses TextBlob for natural language processing.

        **Tip:** Configure Anthropic API credentials in Setup to use Claude for more accurate sentiment analysis.
        """)


if __name__ == "__main__":
    main()
