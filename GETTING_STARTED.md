# Getting Started with Shelf

Welcome! This guide will help you get Shelf up and running in under 5 minutes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Quick Start (Docker Compose)](#quick-start-docker-compose)
4. [Quick Start (Local Development)](#quick-start-local-development)
5. [Getting Your API Token](#getting-your-api-token)
6. [First Time Setup](#first-time-setup)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

## Prerequisites

### For Docker Deployment
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Audiobookshelf instance running and accessible
- Audiobookshelf API token

### For Local Development
- Python 3.11 or higher
- pip package manager
- Audiobookshelf instance running and accessible
- Audiobookshelf API token

### Verify Prerequisites

```bash
# Check Docker
docker --version
# Should show: Docker version 20.x.x or higher

# Check Python (if running locally)
python3 --version
# Should show: Python 3.11.x or higher

# Check Audiobookshelf accessibility
curl https://your-audiobookshelf-url/api/ping
# Should return: {"success":true}
```

## Quick Start (Docker)

This is the fastest way to get started.

### Step 1: Get Your API Token

See [Getting Your API Token](#getting-your-api-token) section below.

### Step 2: Run Shelf

```bash
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token_here \
  --restart unless-stopped \
  shelf:latest
```

**Important**: Replace `https://your-audiobookshelf-url` and `your_api_token_here` with your actual values.

### Step 3: Access Shelf

Open your browser to: **http://localhost:8501**

That's it! You should see your audiobook library.

### Step 4 (Optional): Customize

Add optional environment variables:

```bash
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token_here \
  -e APP_TITLE="My Audiobook Stats" \
  -e CACHE_TTL=600 \
  -e ITEMS_PER_ROW=6 \
  --restart unless-stopped \
  shelf:latest
```

## Quick Start (Docker Compose)

For easier configuration management.

### Step 1: Create Project Directory

```bash
mkdir shelf
cd shelf
```

### Step 2: Download Project Files

```bash
# Option A: From repository
git clone https://github.com/yourusername/shelf.git .

# Option B: Just docker-compose.yml
curl -O https://raw.githubusercontent.com/yourusername/shelf/main/docker-compose.yml
```

### Step 3: Create Environment File

```bash
# Copy example
cp .env.example .env

# Or create new
cat > .env << 'EOF'
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token_here
APP_TITLE=Shelf
CACHE_TTL=300
ITEMS_PER_ROW=5
EOF
```

**Edit `.env`** and add your real values:
```bash
nano .env  # or vim, code, etc.
```

### Step 4: Start Shelf

```bash
docker-compose up -d
```

### Step 5: Access Shelf

Open your browser to: **http://localhost:8501**

### Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop Shelf
docker-compose down

# Restart Shelf
docker-compose restart

# Update Shelf
docker-compose pull
docker-compose up -d
```

## Quick Start (Local Development)

For development or if you prefer not to use Docker.

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/shelf.git
cd shelf
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

Or export directly:
```bash
export ABS_URL=https://your-audiobookshelf-url
export ABS_TOKEN=your_api_token_here
```

### Step 5: Run Shelf

```bash
streamlit run app.py
```

Shelf will open automatically in your browser, or visit: **http://localhost:8501**

### Development Tips

- Streamlit auto-reloads on file changes
- Use `Ctrl+C` to stop the server
- Check `app.log` for debugging

## Getting Your API Token

### Step-by-Step Guide

1. **Open Audiobookshelf** in your browser
2. **Log in** with your account
3. **Click Settings** (gear icon) in the sidebar
4. **Click Users** in settings menu
5. **Click your username** in the user list
6. **Scroll down** to API Tokens section
7. **Click "Generate Token"**
8. **Copy the token** (it will only be shown once!)

### Screenshot Guide

```
Audiobookshelf → Settings → Users → Your User → API Tokens
                                                    ↓
                                            [Generate Token]
                                                    ↓
                                         [Token appears here]
                                                    ↓
                                             [Copy Token]
```

### Important Notes

- **Save your token** - it's only shown once
- **Keep it secure** - treat it like a password
- **Generate new** if lost - old token will be invalidated
- **One token** per user is recommended

## First Time Setup

### After Installation

1. **Verify Connection**
   - Shelf should automatically connect to Audiobookshelf
   - You'll see a green checkmark if connected
   - Any errors will be displayed clearly

2. **Check Library View**
   - Should display your in-progress audiobooks
   - Covers should load
   - Progress bars should show correctly

3. **Check Statistics View**
   - Click "Statistics" tab
   - Should show completion counts
   - Charts should render

### Initial Configuration

#### Adjust Cache Time

If you want more frequent updates:
```bash
# Docker
docker run -e CACHE_TTL=60 ...

# Local
export CACHE_TTL=60
```

#### Adjust Grid Layout

Change books per row:
```bash
# Docker
docker run -e ITEMS_PER_ROW=6 ...

# Local
export ITEMS_PER_ROW=6
```

#### Customize Title

```bash
# Docker
docker run -e APP_TITLE="My Reading Stats" ...

# Local
export APP_TITLE="My Reading Stats"
```

## Troubleshooting

### "Failed to connect to Audiobookshelf"

**Possible causes:**
1. Wrong URL - check `ABS_URL`
2. Network issue - verify Audiobookshelf is accessible
3. Invalid token - regenerate API token

**Solutions:**
```bash
# Test URL
curl https://your-audiobookshelf-url/api/ping

# Verify token in Audiobookshelf settings
# Regenerate if needed

# Check Docker logs
docker logs shelf
```

### "No audiobooks in progress"

**This is normal if:**
- You haven't started any audiobooks yet
- You've finished all audiobooks

**To test:**
- Start playing an audiobook in Audiobookshelf
- Wait a moment for sync
- Refresh Shelf

### Port Already in Use

**Error:** Port 8501 already in use

**Solution:** Use a different port
```bash
# Docker
docker run -p 8502:8501 ...

# Access at http://localhost:8502
```

### Docker Build Fails

**Solution:**
```bash
# Check Dockerfile syntax
docker build -t shelf .

# View detailed errors
docker build --no-cache -t shelf .
```

### Covers Not Loading

**Possible causes:**
1. CORS issue
2. Network restrictions
3. Missing covers in Audiobookshelf

**Solutions:**
- Check Audiobookshelf web interface shows covers
- Check browser console for errors (F12)
- Verify network connectivity

### Slow Performance

**Solutions:**
1. Increase cache time:
   ```bash
   -e CACHE_TTL=600
   ```

2. Reduce items per row:
   ```bash
   -e ITEMS_PER_ROW=4
   ```

3. Check Audiobookshelf server performance

## Next Steps

### Explore Features

1. **Library View**
   - Sort audiobooks
   - View progress details
   - Track start dates

2. **Statistics View**
   - Monthly completion trends
   - Yearly overview
   - Total hours listened

### Customize

1. **Environment Variables**
   - See full list in [README.md](README.md)
   - Adjust to your preferences

2. **Styling**
   - Current: Dark theme
   - Future: Light theme option

### Advanced Setup

1. **Reverse Proxy**
   - See [DEPLOYMENT.md](DEPLOYMENT.md)
   - Setup HTTPS
   - Custom domain

2. **Unraid**
   - See [DEPLOYMENT.md](DEPLOYMENT.md)
   - Install from template
   - Configure in UI

3. **Monitoring**
   - Check health: `http://localhost:8501/_stcore/health`
   - View logs: `docker logs shelf`

### Get Help

1. **Documentation**
   - [README.md](README.md) - Overview
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment
   - [API.md](API.md) - API docs
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture

2. **Community**
   - GitHub Issues
   - GitHub Discussions

3. **Contribute**
   - See [CONTRIBUTING.md](CONTRIBUTING.md)
   - Report bugs
   - Suggest features
   - Submit PRs

### Update Shelf

```bash
# Docker
docker pull shelf:latest
docker stop shelf
docker rm shelf
# Run again with same settings

# Docker Compose
docker-compose pull
docker-compose up -d

# Local
git pull
pip install -r requirements.txt
```

## Quick Reference

### Docker Run Command
```bash
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://abs.example.com \
  -e ABS_TOKEN=your_token \
  --restart unless-stopped \
  shelf:latest
```

### Docker Compose
```yaml
version: '3.8'
services:
  shelf:
    image: shelf:latest
    ports:
      - "8501:8501"
    environment:
      - ABS_URL=https://abs.example.com
      - ABS_TOKEN=your_token
    restart: unless-stopped
```

### Environment Variables
| Variable | Required | Example |
|----------|----------|---------|
| `ABS_URL` | Yes | `https://abs.example.com` |
| `ABS_TOKEN` | Yes | `abc123...` |
| `APP_TITLE` | No | `My Library` |
| `CACHE_TTL` | No | `300` |
| `ITEMS_PER_ROW` | No | `5` |

### Access URLs
- **Web Interface**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health

### Useful Commands
```bash
# Docker logs
docker logs shelf
docker logs -f shelf  # Follow

# Docker restart
docker restart shelf

# Docker Compose
docker-compose logs -f
docker-compose restart
docker-compose down
```

---

**Need help?** Open an issue on GitHub or check the documentation.

**Ready to track your audiobook journey!** 📚
