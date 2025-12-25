# Project Summary - Standalone Version

## Overview

This is a **standalone, single-session version** of the Social Media Analytics Platform that runs entirely within Streamlit without any external services.

## Key Differences from Web App Version

| Feature | Standalone | Web App |
|---------|-----------|---------|
| **Architecture** | Single Streamlit app | Streamlit frontend + FastAPI backend |
| **Database** | In-memory SQLite | PostgreSQL (AWS RDS) |
| **Authentication** | None (single-user) | JWT-based multi-user |
| **External Services** | None | AWS (ECS, S3, Secrets Manager), Redis |
| **Data Persistence** | Session only (deleted on close) | Permanent storage |
| **Background Jobs** | Session-based job manager | APScheduler with persistent storage |
| **API Credentials** | Entered each session | Encrypted in database |
| **Deployment** | Local only (`streamlit run`) | Cloud (Streamlit Cloud + AWS) |
| **Cost** | Free (local) | ~$50-85/month (cloud services) |
| **Use Case** | Personal use, testing, demos | Production, multi-user, teams |

## Architecture

```
┌─────────────────────────────────────────┐
│      Streamlit Web Interface            │
│  (Pages: Setup, Platforms, Analytics)   │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │  Session State    │
        │  - Credentials    │
        │  - Job Manager    │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │  SQLite Database  │
        │   (In-Memory)     │
        └───────────────────┘
```

All components run in a single Python process within the user's browser session.

## File Structure

```
social_media_analytics_standalone/
├── streamlit_app.py                    # Main application entry point
├── requirements.txt                    # Python dependencies
├── README.md                          # Full documentation
├── QUICKSTART.md                      # 5-minute setup guide
├── PROJECT_SUMMARY.md                 # This file
├── .gitignore                         # Git ignore patterns
│
├── pages/                             # Streamlit pages (sidebar navigation)
│   ├── 1_⚙️_Setup.py                 # API credential configuration
│   ├── 2_🎮_Twitch.py                # Twitch monitoring
│   ├── 3_🐦_Twitter.py               # Twitter monitoring
│   ├── 4_📺_YouTube.py               # YouTube monitoring
│   ├── 5_🔴_Reddit.py                # Reddit monitoring
│   ├── 6_📊_Analytics.py             # Cross-platform analytics
│   └── 7_💾_Export.py                # Data export tools
│
├── database/                          # Database management
│   ├── __init__.py
│   └── session_db.py                  # In-memory SQLite manager
│
├── utils/                             # Utility modules
│   ├── __init__.py
│   ├── credential_manager.py          # Session state credential storage
│   └── job_manager.py                 # Background job manager
│
└── src/                               # Source code
    ├── __init__.py
    └── platforms/                     # Platform integrations
        ├── __init__.py
        ├── twitch_integration.py      # Twitch API client & DB
        ├── twitter_integration.py     # Twitter API client & DB
        ├── youtube_integration.py     # YouTube API client & DB
        └── reddit_integration.py      # Reddit API client & DB
```

## Components

### 1. Main Application (`streamlit_app.py`)

- Entry point for the Streamlit app
- Initializes session state
- Displays home dashboard
- Shows sidebar with navigation and statistics

### 2. Pages

Each page is a separate Streamlit page accessible via sidebar:

- **Setup:** Configure API credentials for platforms
- **Platform Pages (4):** Monitor channels/users/subreddits, view data, manage jobs
- **Analytics:** Cross-platform insights, sentiment analysis, engagement metrics
- **Export:** Download database or CSV files

### 3. Database Layer (`database/session_db.py`)

- **SessionDatabase class:** Manages in-memory SQLite database
- Creates tables for all 4 platforms
- Provides CRUD operations
- Exports database as SQL dump

**Tables:**
- `twitch_channels`, `twitch_stream_records`
- `twitter_users`, `twitter_tweets`
- `youtube_channels`, `youtube_videos`
- `reddit_subreddits`, `reddit_posts`

### 4. Credential Manager (`utils/credential_manager.py`)

- Stores API credentials in `st.session_state`
- Provides credential classes for each platform
- Credentials automatically deleted when browser closes
- No disk storage (security by design)

### 5. Job Manager (`utils/job_manager.py`)

- Manages background monitoring jobs
- Stores jobs in `st.session_state`
- Tracks job status (active/paused)
- Schedules next run times
- Jobs trigger when navigating between pages

### 6. Platform Integrations (`src/platforms/`)

Each platform has two main components:

**API Client:**
- Authenticates with platform API
- Fetches data (streams, tweets, videos, posts)
- Handles rate limiting and errors

**Database Helper:**
- CRUD operations for platform-specific tables
- Stores and retrieves data
- Computes statistics

## Features

### Multi-Platform Monitoring

- ✅ **Twitch:** Stream status, viewer counts, game tracking
- ✅ **Twitter:** Tweet collection, engagement metrics
- ✅ **YouTube:** Video performance, channel analytics
- ✅ **Reddit:** Post monitoring, upvote tracking

### Analytics

- 📊 **Cross-Platform Dashboard:** Overview of all platforms
- 💭 **Sentiment Analysis:** Twitter sentiment using TextBlob
- 📈 **Engagement Metrics:** Likes, views, comments, scores
- 🎯 **Platform Comparison:** Side-by-side comparisons

### Data Management

- 💾 **Export Options:**
  - Complete SQL database dump
  - CSV exports per platform
  - Platform-specific detailed exports
- 🔄 **Manual Collection:** On-demand data fetching
- ⏰ **Automated Jobs:** Background monitoring at intervals

### User Experience

- 🎨 **Clean UI:** Streamlit's modern interface
- 📱 **Responsive:** Works on desktop browsers
- 🔒 **Secure:** Credentials never leave your computer
- ⚡ **Fast:** In-memory database for speed
- 📊 **Visualizations:** Plotly charts and graphs

## Technologies Used

### Core Framework
- **Streamlit:** Web interface and navigation
- **Python 3.8+:** Programming language

### Database
- **SQLite:** In-memory relational database (built-in)

### Platform APIs
- **Twitch API:** OAuth 2.0, REST API
- **Tweepy:** Twitter API v2 wrapper
- **Google API Client:** YouTube Data API v3
- **PRAW:** Reddit API wrapper

### Data Processing
- **Pandas:** Data manipulation
- **NumPy:** Numerical operations

### Visualization
- **Plotly:** Interactive charts
- **Matplotlib/Seaborn:** Additional plotting

### Analytics
- **TextBlob:** Lightweight sentiment analysis

### Export
- **openpyxl:** Excel export support
- **reportlab:** PDF generation (optional)

## How It Works

### 1. Session Initialization

```python
# streamlit_app.py
def initialize_session():
    # Create in-memory database
    db = get_session_db()  # Creates SessionDatabase instance

    # Initialize session state
    st.session_state.initialized = True
```

### 2. Credential Storage

```python
# User enters credentials in Setup page
CredentialManager.set_twitch_credentials(client_id, client_secret)

# Stored in st.session_state:
st.session_state.twitch_credentials = TwitchCredentials(...)
```

### 3. Data Collection

```python
# User clicks "Collect Data" on platform page
def collect_twitch_data(channel_name, db):
    # Get credentials from session
    creds = CredentialManager.get_twitch_credentials()

    # Call API
    api = TwitchAPI(creds.client_id, creds.client_secret)
    stream_info = api.get_stream_info(channel_name)

    # Store in database
    twitch_db = TwitchDatabase(db)
    twitch_db.add_stream_record(...)
```

### 4. Background Jobs

```python
# User starts monitoring job
job_id = JobManager.add_job(
    platform="twitch",
    entity_id=channel_id,
    entity_name=channel_name,
    interval_minutes=15
)

# Job stored in session state
st.session_state.monitoring_jobs[job_id] = MonitoringJob(...)

# Jobs run when due (checked on page navigation)
due_jobs = JobManager.get_jobs_due_for_run()
for job in due_jobs:
    collect_platform_data(job.platform, job.entity_name)
```

### 5. Data Export

```python
# User exports database
sql_dump = db.export_to_file()  # Generates SQL dump

# Downloads as file
st.download_button(data=sql_dump, file_name="database.sql")
```

## Limitations

### By Design

1. **No Persistence:** Data deleted when browser closes
2. **Single User:** No multi-user support or authentication
3. **Local Only:** Cannot deploy to cloud as-is
4. **Manual Credentials:** Must re-enter each session

### Technical

1. **Memory Limits:** Large datasets may slow browser
2. **Job Execution:** Jobs run on page navigation (not true background)
3. **No Real-Time:** No WebSocket updates
4. **Desktop Only:** Not optimized for mobile

## Security

### Privacy

- ✅ No data sent to external servers (except platform APIs)
- ✅ Credentials never saved to disk
- ✅ No telemetry or tracking
- ✅ All processing happens locally

### Best Practices

- API credentials stored only in memory
- No logging of sensitive data
- HTTPS recommended (Streamlit supports it)

## Deployment Options

### Local Use (Recommended)

```bash
streamlit run streamlit_app.py
```

### Local Network Access

```bash
streamlit run streamlit_app.py --server.address=0.0.0.0
```

Access from other devices on your network at `http://YOUR_IP:8501`

### Cloud Deployment (Not Recommended)

While technically possible to deploy to Streamlit Cloud, it's **not recommended** because:
- Session data would be shared across users
- No authentication to protect data
- Credentials would be visible to all users

For cloud deployment, use the **Web App Version** instead.

## When to Use This Version

### ✅ Good For:

- Personal use on your local machine
- Testing and experimentation
- Demos and presentations
- Learning about social media APIs
- One-time data collection projects

### ❌ Not Good For:

- Multi-user production use
- Long-term data storage
- Large-scale monitoring (100+ entities)
- Automated 24/7 monitoring
- Team collaboration

For production use, see the **Web App Version** (multi-user, cloud-deployed).

## Performance

### Expected Performance:

- **Database:** Fast (in-memory SQLite)
- **UI:** Responsive for <1000 records per platform
- **Job Execution:** Depends on page navigation frequency
- **Memory Usage:** ~100-500MB for typical use

### Optimization Tips:

1. Export and clear data periodically
2. Limit monitoring jobs to <10 per platform
3. Use reasonable intervals (≥15 minutes)
4. Close unused browser tabs

## Future Enhancements (Potential)

Ideas for improvement:
- [ ] Persistent storage option (local SQLite file)
- [ ] Credential encryption for saved credentials
- [ ] True background job execution (threading)
- [ ] Mobile-responsive UI
- [ ] More analytics features
- [ ] Custom alerts and notifications

## Comparison with Desktop App

This standalone version is similar to the original desktop (Tkinter) app:

| Feature | Desktop App | Standalone Web |
|---------|-------------|----------------|
| Interface | Tkinter | Streamlit (Web) |
| Persistence | SQLite files | In-memory only |
| Credentials | JSON files | Session state |
| Access | Desktop only | Browser (local) |
| Deployment | Executable | Python script |

## License

Same license as the main Social Media Analytics Platform.

## Credits

Built as a simplified, standalone alternative to the full web app version.

---

**Version:** 2.0.0 (Standalone)
**Created:** December 2025
**Platform:** Streamlit + Python
