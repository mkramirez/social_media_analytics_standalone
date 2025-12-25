# Twitch Enhanced Features Guide

## 🎉 New Features Overview

The enhanced Twitch monitoring page now includes:

1. ✅ **Automated Collection** - Jobs run automatically with auto-refresh
2. ✅ **Bulk User Addition** - Add multiple channels at once
3. ✅ **Chat Message Collection** - Collect chat logs and message counts
4. ✅ **Multi-Sheet Excel Export** - One sheet per channel
5. ✅ **Configurable Intervals** - Set custom collection intervals
6. ✅ **Form Clearing** - Auto-clear after verification

---

## 📖 How to Use

### 1. Automated Collection

**Enable Auto-Refresh:**

1. Go to **🎮 Twitch Enhanced** page
2. Check the box: **"🔄 Auto-refresh (runs jobs automatically)"**
3. Select refresh interval (30s, 60s, 120s, etc.)

**What happens:**
- Jobs that are due will run automatically
- Page refreshes at the set interval
- Data collection happens in the background

**How it works:**
- Jobs have a "next run" time based on their interval
- When auto-refresh is ON, the page checks for due jobs
- Due jobs are executed automatically
- Page refreshes to show updated data

---

### 2. Bulk User Addition

**Add Multiple Channels:**

1. Go to **📝 Add Channels (Bulk)** section
2. Enter channel usernames, **one per line**:
   ```
   ninja
   shroud
   xqc
   pokimane
   ```

3. Configure settings:
   - ✅ **Verify channels exist** - Check if channels are valid
   - ✅ **Collect data immediately** - Fetch data right away
   - ✅ **Start monitoring jobs** - Begin automated collection

4. Set monitoring settings:
   - **Collection Interval:** How often to collect data (5-240 minutes)
   - **Collect chat messages:** Enable/disable chat collection
   - **Chat Collection Duration:** How long to collect chat (30-300 seconds)

5. Click **Add Channels**

**Results:**
- ✅ Success: Channels added and verified
- ℹ️ Already Exists: Channels that were already added
- ⚠️ Not Found: Invalid channel names
- ❌ Errors: Any issues encountered

**Auto-clear:** The form clears after successful addition!

---

### 3. Chat Message Collection

**What's Collected:**

For each data collection interval, the app captures:
- **Chat message count** - Total messages sent during the interval
- **Individual chat messages** - Username, message text, timestamp
- **Chat logs** - Stored in database for later viewing

**Enable Chat Collection:**

1. When adding channels, check **"Collect chat messages"**
2. Set **Chat Collection Duration** (e.g., 60 seconds)
3. For existing channels, toggle **"Collect chat messages"** in the channel's expander

**How It Works:**
- Connects to Twitch IRC chat
- Listens for messages during the specified duration
- Stores all messages in the database
- Only collects when stream is **LIVE**

**View Chat Data:**
- Shown in channel statistics: "Chat Messages (last interval)"
- Total chat messages tracked
- Available in exports

---

### 4. Collection Intervals

**Set Custom Intervals:**

**For Bulk Add:**
- Choose from: 5, 10, 15, 30, 60, 120, 180, 240 minutes
- All channels added together will use the same interval

**For Individual Channels:**
- Each channel can have its own interval
- Edit in the monitoring job settings

**How Intervals Work:**
- Jobs run every X minutes
- "Next run" timer shows when the next collection will happen
- With auto-refresh ON, jobs run automatically at the right time
- Without auto-refresh, jobs run when you navigate pages

---

### 5. Multi-Sheet Excel Export

**Export Options:**

**Option 1: Single Channel Export**
1. Find a channel in the list
2. Click **💾 Export** button
3. Downloads Excel with 2 sheets:
   - **Sheet 1:** Stream Data (viewer count, title, game, etc.)
   - **Sheet 2:** Chat Messages (if collected)

**Option 2: All Channels Export**
1. Click **"📥 Download All Channels Data (Multi-Sheet Excel)"** at the top
2. Downloads Excel with **one sheet per channel**
3. Each sheet contains that channel's stream data

**File Format:**
- `.xlsx` (Excel format)
- Compatible with Excel, Google Sheets, LibreOffice
- File name includes timestamp: `twitch_channelname_20251224_153045.xlsx`

---

## 📊 Data Collected

### Stream Records

For each collection:
- **Timestamp** - When data was collected
- **Is Live** - Whether stream was live
- **Title** - Stream title
- **Game Name** - Game being played
- **Viewer Count** - Current viewers
- **Started At** - When stream went live
- **Chat Message Count** - Messages during interval

### Chat Messages (when enabled)

- **Username** - Who sent the message
- **Message** - Message content
- **Timestamp** - When message was sent
- **Record ID** - Links to stream record

---

## 🔧 Configuration Guide

### Recommended Settings

**For Active Streamers (stream often):**
- Collection Interval: **15 minutes**
- Chat Collection: **ON**
- Chat Duration: **60 seconds**
- Auto-refresh: **ON** (60s)

**For Occasional Streamers:**
- Collection Interval: **60 minutes**
- Chat Collection: **ON**
- Chat Duration: **30 seconds**
- Auto-refresh: **ON** (120s)

**For Many Channels (10+):**
- Collection Interval: **30 minutes**
- Chat Collection: **OFF** (to save resources)
- Auto-refresh: **ON** (60s)

---

## 🎯 Usage Examples

### Example 1: Monitor 5 Top Streamers

```
1. Go to Bulk Add
2. Enter:
   ninja
   shroud
   pokimane
   xqc
   summit1g

3. Settings:
   - Interval: 15 minutes
   - Chat collection: ON (60 seconds)
   - Start monitoring: ON

4. Enable auto-refresh (60s)

Result: All 5 streamers monitored every 15 minutes with chat!
```

### Example 2: Track Stream Performance

```
1. Add your favorite streamer
2. Enable chat collection
3. Let it run for a few hours
4. Export to Excel
5. Analyze:
   - Viewer count trends
   - Peak viewer times
   - Chat activity correlation
```

### Example 3: Compare Multiple Streamers

```
1. Add all streamers in bulk
2. Same interval for fair comparison
3. Export all channels to multi-sheet Excel
4. Compare:
   - Average viewers
   - Chat engagement
   - Stream frequency
```

---

## ⚙️ Technical Details

### Chat Collection Process

1. **Connect to Twitch IRC:**
   - Uses IRC protocol (irc.chat.twitch.tv:6667)
   - Authenticates with OAuth token
   - Joins channel's chat room

2. **Collect Messages:**
   - Listens for PRIVMSG events
   - Parses username and message
   - Stores with timestamp

3. **Store Data:**
   - Messages linked to stream record
   - Queryable by record ID
   - Available in exports

### Auto-Refresh Mechanism

```python
if auto_refresh:
    # 1. Check for due jobs
    due_jobs = get_jobs_due_for_run()

    # 2. Execute each job
    for job in due_jobs:
        collect_data(job.entity_name)

    # 3. Wait for refresh interval
    time.sleep(refresh_interval)

    # 4. Refresh page
    st.rerun()
```

### Database Schema

**twitch_stream_records:**
- Added column: `chat_message_count INTEGER`

**twitch_chat_messages:** (new table)
- `id` - Primary key
- `record_id` - Foreign key to stream record
- `username` - Chatter username
- `message` - Message text
- `timestamp` - When message was sent

---

## 🐛 Troubleshooting

### Jobs Not Running Automatically

**Problem:** Jobs don't execute automatically
**Solution:**
- ✅ Enable **auto-refresh** checkbox
- ✅ Ensure jobs are **active** (not paused)
- ✅ Check "Next run" time - jobs only run when due

### Chat Messages Not Collecting

**Problem:** Chat message count is always 0
**Solution:**
- ✅ Stream must be **LIVE** for chat collection
- ✅ Enable "Collect chat messages" checkbox
- ✅ Check chat duration setting (minimum 30s)
- ✅ Verify Twitch API credentials are valid

### Bulk Add Fails

**Problem:** All channels show "not found"
**Solution:**
- ✅ Check channel names are correct (no @ symbol)
- ✅ Verify Twitch API credentials
- ✅ Try adding channels one at a time
- ✅ Some channels may be banned/deleted

### Excel Export Errors

**Problem:** Export button doesn't work
**Solution:**
- ✅ Install `openpyxl`: `pip install openpyxl`
- ✅ Check if data exists for the channel
- ✅ Try exporting with fewer records

---

## 💡 Tips & Best Practices

### Performance Tips

1. **Don't over-monitor:**
   - More frequent intervals = more API calls
   - Twitch has rate limits (800 req/min)
   - For 10 channels with 15min intervals = 40 req/hour

2. **Chat collection is resource-intensive:**
   - Only enable for channels you care about
   - Shorter durations (30-60s) are usually enough
   - Disable when stream is offline

3. **Use auto-refresh wisely:**
   - 60s refresh is good for most use cases
   - Longer intervals (120s) for many channels
   - Shorter intervals (30s) for real-time tracking

### Data Management

1. **Export regularly:**
   - Session data is deleted when browser closes
   - Export before closing tab
   - Download multi-sheet Excel for backup

2. **Clean up old channels:**
   - Delete channels you no longer monitor
   - Reduces clutter and improves performance

3. **Monitor chat selectively:**
   - Chat logs can take a lot of storage
   - Enable only for important channels

---

## 📈 What's Next?

Potential future improvements:
- [ ] Sentiment analysis on chat messages
- [ ] Word clouds from chat logs
- [ ] Emote tracking
- [ ] Viewer growth charts
- [ ] Best streaming time analysis
- [ ] Chat activity heatmaps

---

## 🔄 Features Overview

The Twitch page now includes all enhanced features:

**Current Features:**
- ✅ Chat collection with IRC integration
- ✅ Bulk channel addition
- ✅ Multi-sheet Excel export (one sheet per channel)
- ✅ Auto-refresh with automated job execution
- ✅ Configurable collection intervals
- ✅ Individual chat settings per channel

---

**Happy Monitoring! 🎮📊**

For questions or issues, check the main README.md or QUICKSTART.md.
