# Social Media Analytics - Standalone Version

A self-contained Streamlit web application for social media analytics that runs entirely in your browser. No external services, databases, or authentication required!

## ✨ Features

- **Multi-Platform Monitoring:** Twitch, Twitter, YouTube, and Reddit
- **Session-Based Storage:** All data stored in memory (deleted when browser closes)
- **No External Services:** No AWS, no PostgreSQL, no Redis - completely standalone
- **No Login Required:** Single-user, instant access
- **Real-Time Data Collection:** Manual or automated monitoring jobs
- **Analytics Dashboard:** Sentiment analysis, engagement metrics, trends
- **Data Export:** Download database or CSV before closing session

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this directory:**
   ```bash
   cd social_media_analytics_standalone
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open your browser:**
   The app will automatically open at `http://localhost:8501`

## 📖 How to Use

### 1. Setup API Credentials

**First time using the app:**

1. Click on **⚙️ Setup** in the sidebar
2. Configure credentials for the platforms you want to use:
   - **Twitch:** Client ID and Client Secret
   - **Twitter:** Bearer Token
   - **YouTube:** API Key
   - **Reddit:** Client ID, Client Secret, and User Agent

**⚠️ Important:** Your credentials are stored only in the browser session and will be deleted when you close the tab.

### 2. Add Entities to Monitor

**For each platform:**

1. Go to the platform page (🎮 Twitch, 🐦 Twitter, 📺 YouTube, or 🔴 Reddit)
2. Enter the channel/user/subreddit name
3. Choose options:
   - **Collect data immediately:** Fetches data right away
   - **Start monitoring job:** Automatically collects data at intervals

### 3. View Analytics

1. Go to **📊 Analytics** page
2. See cross-platform insights:
   - Platform breakdown
   - Twitter sentiment analysis
   - Engagement metrics

### 4. Export Data

**Before closing the browser:**

1. Go to **💾 Export** page
2. Download options:
   - **Complete Database (SQL):** Full database dump
   - **CSV Exports:** Individual CSV files per platform
   - **Platform-Specific:** Detailed exports from platform pages

## 🔧 Platform API Setup Guides

### Twitch

1. Go to https://dev.twitch.tv/console
2. Log in and click **"Register Your Application"**
3. Fill in:
   - Name: Your app name
   - OAuth Redirect URLs: `http://localhost`
   - Category: Analytics Tool
4. Copy **Client ID** and **Client Secret**

### Twitter

1. Go to https://developer.twitter.com/
2. Create a Developer Account (if needed)
3. Create a new project and app
4. Navigate to **"Keys and Tokens"**
5. Generate and copy the **Bearer Token**

### YouTube

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable **"YouTube Data API v3"**
4. Go to **"Credentials"** → Create **API Key**
5. Copy the **API Key**

### Reddit

1. Go to https://www.reddit.com/prefs/apps
2. Click **"Create App"**
3. Select **"script"** as app type
4. Fill in details and create
5. Copy **Client ID** and **Client Secret**
6. Create a User Agent: `web:app-name:v1.0 (by /u/your_username)`

## 📊 Monitoring Jobs

**How it works:**

- Jobs run in the background within your browser session
- They collect data at specified intervals (e.g., every 15 minutes)
- Jobs persist across page refreshes (within the same session)
- All jobs stop when you close the browser tab

**Managing Jobs:**

- **Start Job:** Begins automated data collection
- **Pause Job:** Temporarily stops collection (can resume later)
- **Resume Job:** Continues a paused job
- **Delete Entity:** Removes entity and stops its job

## ⚠️ Important Limitations

### Session-Based Storage

- **All data is stored in memory**
- **Data is deleted when you close the browser tab**
- **No persistence between sessions**
- **Export your data before closing!**

### Manual Credential Entry

- API credentials must be re-entered each session
- They are never saved to disk
- For security: credentials are only stored in browser memory

### API Rate Limits

Be aware of platform API limits:
- **Twitch:** 800 requests/minute
- **Twitter:** 300 requests/15 minutes
- **YouTube:** 10,000 quota units/day
- **Reddit:** 60 requests/minute

Adjust monitoring intervals accordingly.

## 🆚 Differences from Web App Version

| Feature | Standalone | Web App |
|---------|------------|---------|
| Authentication | ❌ None | ✅ Multi-user |
| Database | In-memory SQLite | PostgreSQL |
| External Services | ❌ None | AWS, Redis |
| Data Persistence | ❌ Session only | ✅ Permanent |
| Deployment | Local only | Cloud (Streamlit Cloud) |
| Background Jobs | Session-based | APScheduler (persistent) |
| Credential Storage | Session state | Encrypted database |
| Use Case | Personal/Testing | Production/Multi-user |

## 🛠️ Troubleshooting

### "Module not found" errors

Install all dependencies:
```bash
pip install -r requirements.txt
```

### API credential errors

- Double-check your credentials in the Setup page
- Ensure you have the correct permissions for each API
- Some APIs require approval (Twitter Developer Account)

### Data not persisting

**This is expected behavior!** Data is session-only. Export before closing.

### Jobs not running

- Jobs run on-demand when you navigate between pages
- Refresh the page to trigger pending jobs
- Check the sidebar for job status

## 📁 Project Structure

```
social_media_analytics_standalone/
├── streamlit_app.py              # Main application
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── pages/
│   ├── 1_⚙️_Setup.py           # API credential setup
│   ├── 2_🎮_Twitch.py          # Twitch monitoring
│   ├── 3_🐦_Twitter.py         # Twitter monitoring
│   ├── 4_📺_YouTube.py         # YouTube monitoring
│   ├── 5_🔴_Reddit.py          # Reddit monitoring
│   ├── 6_📊_Analytics.py       # Analytics dashboard
│   └── 7_💾_Export.py          # Data export
├── database/
│   └── session_db.py             # In-memory database manager
├── utils/
│   ├── credential_manager.py     # Session credential storage
│   └── job_manager.py            # Background job manager
└── src/
    └── platforms/
        ├── twitch_integration.py
        ├── twitter_integration.py
        ├── youtube_integration.py
        └── reddit_integration.py
```

## 💡 Tips & Best Practices

1. **Export regularly:** Download your data periodically during long sessions
2. **Monitor responsibly:** Set reasonable intervals to avoid hitting API rate limits
3. **Test with one platform:** Start with one platform before adding all four
4. **Use Setup checks:** The sidebar shows which platforms are configured
5. **Browser tabs:** Each browser tab is a separate session with separate data

## 🔒 Security & Privacy

- **No data leaves your computer** (except API calls to platforms)
- **Credentials never saved to disk**
- **No telemetry or tracking**
- **No external databases or services**
- **All processing happens locally**

## 🐛 Known Issues

1. **Large datasets may slow down the browser** - Export and clear data periodically
2. **Job execution depends on page navigation** - Jobs trigger when you use the app
3. **No mobile optimization** - Best used on desktop browsers

## 📝 License

This is a standalone version of the Social Media Analytics Platform.

## 🙋 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your API credentials are correct
3. Ensure all dependencies are installed

## 🎉 Getting Started Checklist

- [ ] Install Python 3.8+
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run the app (`streamlit run streamlit_app.py`)
- [ ] Configure at least one platform in Setup
- [ ] Add your first channel/user/subreddit
- [ ] Collect data and view analytics
- [ ] Export your data before closing!

---

**Version:** 2.0.0 (Standalone)
**Last Updated:** December 2025

**Enjoy your standalone social media analytics! 🚀**
