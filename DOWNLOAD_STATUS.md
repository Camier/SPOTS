# 🗺️ IGN 50GB Download - ACTIVE

## ✅ Download Started Successfully

The background download process is now running and will continue building the 50GB IGN offline map collection.

## 📊 Current Status
- **Process:** Running in background (2 Python processes active)
- **Target:** 50GB of IGN tiles
- **Current:** Downloading Toulouse Metropolitan area
- **Log File:** `IGN_CONSOLIDATED/02_downloads/download.log`

## 🔧 Management Commands

### Monitor Progress
```bash
# Real-time monitoring dashboard
./monitor_downloads.sh

# Watch the log file
tail -f IGN_CONSOLIDATED/02_downloads/download.log

# Check current size
du -sh IGN_CONSOLIDATED/
```

### Control Downloads
```bash
# Stop downloads
pkill -f download_50gb

# Resume downloads
cd IGN_CONSOLIDATED && python3 scripts/download_50gb_collection.py &

# Check if running
ps aux | grep download_50gb
```

## 📈 Expected Timeline
- **Download Rate:** ~3-4 MB/min (varies with IGN server response)
- **Estimated Time:** ~200-250 hours for full 50GB
- **Session Size:** 1GB per run (auto-resumes)

## 🎯 Download Strategy
The script is downloading in this order:
1. **Toulouse Metropolitan** - High detail urban area
2. **Montpellier Metropolitan** - Second major city
3. **Pyrénées National Parks** - Mountain regions
4. **Occitanie West & East** - Complete regional coverage

## 💡 Tips
- Downloads can be safely interrupted and resumed
- The script handles rate limiting automatically
- Failed tiles are skipped and can be retried later
- Each MBTiles database is optimized after download

## 📁 File Locations
- **MBTiles:** `IGN_CONSOLIDATED/01_active_maps/`
- **Downloads:** `IGN_CONSOLIDATED/02_downloads/`
- **Scripts:** `IGN_CONSOLIDATED/scripts/`
- **Log:** `IGN_CONSOLIDATED/02_downloads/download.log`

---
*Background download is active and will continue automatically*