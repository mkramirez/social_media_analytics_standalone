# Quick Start Guide

Get up and running with Social Media Analytics in 5 minutes!

## Installation (2 minutes)

```bash
# Navigate to the directory
cd social_media_analytics_standalone

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## First-Time Setup (3 minutes)

### 1. Configure API Credentials

Click **⚙️ Setup** in the sidebar and add credentials for at least one platform:

#### Twitch (Easiest)
- Go to: https://dev.twitch.tv/console
- Create app → Copy Client ID & Secret

#### Twitter
- Go to: https://developer.twitter.com/
- Create app → Generate Bearer Token

#### YouTube
- Go to: https://console.cloud.google.com/
- Enable YouTube Data API → Create API Key

#### Reddit
- Go to: https://www.reddit.com/prefs/apps
- Create "script" app → Copy ID & Secret

### 2. Add Your First Entity

1. Click on a platform page (e.g., **🎮 Twitch**)
2. Enter a channel name (e.g., "ninja" or "shroud")
3. Check "Collect data immediately"
4. Click **Add Channel**

### 3. View Your Data

- Check the platform page to see collected data
- Go to **📊 Analytics** for insights
- Use **💾 Export** to download before closing

## That's it! 🎉

You're now monitoring social media!

## Next Steps

- Add more channels/users/subreddits
- Enable **monitoring jobs** for automatic data collection
- Explore the **Analytics** dashboard
- Remember to **export your data** before closing!

## Need Help?

See [README.md](README.md) for full documentation.

---

**⚠️ Remember:** All data is deleted when you close the browser. Export regularly!
