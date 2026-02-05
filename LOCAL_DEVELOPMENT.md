# Local Development Guide for ReadingView

This guide focuses on local development and testing. Once deployed to Unraid, the workflow uses GitHub Actions → Docker Hub → Unraid.

## Quick Start

### Prerequisites

- **Python 3.11+** installed
- **pip** package manager
- **git** for version control
- **Audiobookshelf** instance accessible

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/readingview.git
cd readingview
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Add your Audiobookshelf details:
```env
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token
APP_TITLE=ReadingView
CACHE_TTL=300
```

5. **Run the application:**
```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

## Development Workflow

### Daily Development

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run the app
streamlit run app.py

# 3. Make changes - Streamlit auto-reloads!

# 4. Test changes in browser
# 5. Commit when ready
```

### File Structure

```
readingview/
├── app.py                    # Main entry point - start here
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
│
├── api/
│   ├── __init__.py          # Makes it a Python package
│   └── audiobookshelf.py    # ABS API client
│
├── components/
│   ├── __init__.py          # Makes it a Python package
│   ├── library.py           # Library grid view
│   └── statistics.py        # Statistics dashboard
│
└── utils/
    ├── __init__.py          # Makes it a Python package
    └── helpers.py           # Utility functions
```

### Making Changes

#### Modify UI Components

**Library View:** Edit `components/library.py`
```python
def render_library_view(api: AudiobookshelfAPI):
    # Your changes here
    pass
```

**Statistics:** Edit `components/statistics.py`
```python
def render_statistics_view(api: AudiobookshelfAPI):
    # Your changes here
    pass
```

#### Add New Features

1. **New API Method:**
   - Edit `api/audiobookshelf.py`
   - Add method to `AudiobookshelfAPI` class

2. **New Utility Function:**
   - Edit `utils/helpers.py`
   - Add helper function

3. **New Configuration:**
   - Edit `config.py`
   - Add environment variable

### Testing

#### Manual Testing

```bash
# Run app
streamlit run app.py

# Test in browser:
# - http://localhost:8501
# - Library tab
# - Statistics tab
# - Error handling
```

#### Common Test Scenarios

1. **Connection Test:**
   - Start app
   - Should connect to Audiobookshelf
   - Check for errors

2. **Library View:**
   - Should show in-progress books
   - Covers should load
   - Progress bars accurate

3. **Statistics:**
   - Charts should render
   - Metrics should calculate
   - Data should be recent

### Debugging

#### Enable Debug Mode

```bash
# Set debug env var
export STREAMLIT_DEBUG=1
streamlit run app.py
```

#### Check Logs

Streamlit outputs logs to console:
```bash
streamlit run app.py 2>&1 | tee app.log
```

#### Common Issues

**Import Error: No module named 'api'**
- Solution: Make sure `__init__.py` exists in `api/`, `components/`, `utils/`
- Run from project root directory

**Connection Failed**
- Check `ABS_URL` and `ABS_TOKEN` in `.env`
- Test Audiobookshelf accessibility: `curl $ABS_URL/api/ping`

**Port Already in Use**
- Change port: `streamlit run app.py --server.port=8502`

### Code Style

Follow these conventions:

```python
# Type hints
def my_function(param: str) -> dict:
    """Docstring describing function."""
    pass

# Imports at top
import streamlit as st
from typing import List, Dict

# Constants uppercase
CACHE_TTL = 300

# Classes PascalCase
class MyClass:
    pass

# Functions snake_case
def my_function():
    pass
```

## Deployment Pipeline

### GitHub → Docker Hub → Unraid

Once you're happy with local changes:

```bash
# 1. Commit changes
git add .
git commit -m "Description of changes"
git push origin main

# 2. GitHub Actions builds Docker image
# (configured in .github/workflows/docker-build.yml)

# 3. Image pushed to Docker Hub

# 4. Update in Unraid
# - Open ReadingView container
# - Click "Force Update"
# - Restart container
```

### GitHub Actions Setup

Create `.github/workflows/docker-build.yml`:

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: yourusername/readingview
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### Unraid Configuration

See `unraid-template.xml` for the complete template.

Key settings:
- **Repository:** `yourusername/readingview:latest`
- **Port:** `8501`
- **Environment Variables:**
  - `ABS_URL`
  - `ABS_TOKEN`
  - `APP_TITLE` (optional)
  - `CACHE_TTL` (optional)

## Quick Reference

### Start Development
```bash
source venv/bin/activate
streamlit run app.py
```

### Stop Application
Press `Ctrl+C` in terminal

### Update Dependencies
```bash
pip install -r requirements.txt
```

### Add New Dependency
```bash
pip install package-name
pip freeze > requirements.txt
```

### Clear Cache
In the Streamlit UI: Menu → Clear cache

### Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `ABS_URL` | Yes | `https://abs.example.com` | Audiobookshelf server URL |
| `ABS_TOKEN` | Yes | `abc123...` | API token |
| `APP_TITLE` | No | `ReadingView` | Dashboard title |
| `CACHE_TTL` | No | `300` | Cache duration (seconds) |
| `ITEMS_PER_ROW` | No | `5` | Books per row in grid |

### Useful Commands

```bash
# Run on different port
streamlit run app.py --server.port=8502

# Run without opening browser
streamlit run app.py --server.headless=true

# Check Python syntax
python3 -m py_compile app.py

# Find Python location
which python3

# Check installed packages
pip list

# Upgrade pip
pip install --upgrade pip
```

## Development Tips

### Streamlit Features

- **Auto-reload:** Save files to see changes instantly
- **Cache:** Use `@st.cache_data` for expensive operations
- **Session state:** Use `st.session_state` for state management
- **Widgets:** Streamlit has many built-in widgets

### Performance

- Keep cache TTL reasonable (300s default)
- Minimize API calls
- Use progress indicators for slow operations

### UI Customization

Custom CSS is in `app.py` in the `apply_custom_theme()` function:
```python
st.markdown("""
    <style>
    /* Your custom CSS here */
    </style>
""", unsafe_allow_html=True)
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Deactivate and recreate
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Module Not Found

```bash
# Ensure you're in project root
pwd  # Should show: .../readingview

# Check __init__.py files exist
ls api/__init__.py
ls components/__init__.py
ls utils/__init__.py
```

### Streamlit Won't Start

```bash
# Check Streamlit installation
streamlit --version

# Reinstall if needed
pip uninstall streamlit
pip install streamlit
```

## Getting Help

- **Documentation:** See `README.md`, `API.md`, `ARCHITECTURE.md`
- **Issues:** GitHub issue tracker
- **Logs:** Check console output from `streamlit run`

## Next Steps

1. Make your changes locally
2. Test thoroughly with `streamlit run app.py`
3. Commit and push to GitHub
4. GitHub Actions builds Docker image
5. Update container in Unraid
6. Test in production

Happy coding! 🚀
