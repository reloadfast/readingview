# ReadingView - Quick Reference

## 🚀 Quick Start

```bash
cd readingview
pip install -r requirements.txt
streamlit run app.py
```

## 📋 Requirements

- Python 3.11+
- Audiobookshelf instance
- API token from Audiobookshelf

## 🔧 Configuration

Create `.env` file:
```env
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token
```

## 📚 Main Features

| Feature | Tab | Description |
|---------|-----|-------------|
| Library View | 📚 Library | See in-progress audiobooks |
| Statistics | 📊 Statistics | Charts and listening stats |
| Release Tracker | 📅 Release Tracker | Track upcoming releases |

## 🔍 Release Tracker - Quick Guide

### Add a Book (3 Ways)

1. **🔍 Search Open Library** ← Recommended!
   - Search by title/author/series
   - Auto-fills book details
   - Just add release date

2. **📚 From Your Audiobooks**
   - Import authors from library
   - Track what you're reading

3. **✍️ Manual Entry**
   - Full manual control
   - Helper links to Open Library

### Search Open Library

```
1. Type: "Book Title" or "Author Name"
2. Choose search type: General/Author/Title/Series
3. Click "🔍 Search"
4. Click "➕ Add to Tracker" on result
5. Fill in release date
6. Save!
```

## 🎯 Common Tasks

### Track Next Book in Series

```
Search Open Library → Series → "Series Name"
Find next book → Add to Tracker
```

### Track Favorite Author

```
From Your Audiobooks → Select author
Or: Search Open Library → Author → "Name"
```

### Update Release Date

```
Upcoming Releases → Expand book → Edit
Update date → Mark confirmed → Save
```

## 🐛 Troubleshooting

### Import Error

```bash
# Fix missing __init__.py files
python3 setup.py
```

### Connection Failed

```bash
# Test Audiobookshelf
curl $ABS_URL/api/ping

# Check .env file
cat .env
```

### Database Issues

```bash
# Backup
cp data/releases.db data/releases.backup

# Reset (if needed)
rm data/releases.db
```

## 📁 File Structure

```
readingview/
├── app.py              # Main app
├── .env                # Your config
├── requirements.txt    # Dependencies
├── config/            # Configuration
├── api/               # API clients
│   ├── audiobookshelf.py
│   └── openlibrary.py
├── components/        # UI components
├── database/          # SQLite database
├── utils/             # Helper functions
└── data/              # App data
    └── releases.db    # Release tracker DB
```

## 🔗 Important Links

- **Open Library**: https://openlibrary.org
- **Audiobookshelf**: https://www.audiobookshelf.org
- **Documentation**: See `*.md` files in project

## ⌨️ Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh page
- `Enter`: Submit search
- `Tab`: Next field

## 📊 Default Settings

| Setting | Default | Change in |
|---------|---------|-----------|
| Cache TTL | 300s | `.env` |
| Items per row | 5 | `.env` |
| Theme | Dark | `.env` |
| Release Tracker | Enabled | `.env` |

## 🆘 Get Help

1. Check `OPEN_LIBRARY_USER_GUIDE.md`
2. See `BUG_FIXES.md` for known issues
3. Read `LOCAL_DEVELOPMENT.md` for dev help
4. Open GitHub issue

## 📦 Update

```bash
git pull
pip install -r requirements.txt
streamlit run app.py
```

## 🎉 Pro Tips

- ✅ Use Open Library search for easy tracking
- ✅ Link Goodreads for reference
- ✅ Mark dates as confirmed/tentative
- ✅ Add notes with sources
- ✅ Check tracker monthly
- ✅ Backup database before updates

---

**Version**: 1.2.0  
**Last Updated**: 2026-02-05
