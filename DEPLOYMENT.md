# Deployment Guide

This guide covers various deployment options for Shelf.

## Table of Contents

- [Docker (Recommended)](#docker-recommended)
- [Docker Compose](#docker-compose)
- [Unraid](#unraid)
- [Local Development](#local-development)
- [Production Considerations](#production-considerations)

## Docker (Recommended)

### Prerequisites
- Docker installed and running
- Audiobookshelf instance accessible
- Audiobookshelf API token

### Quick Start

```bash
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  shelf:latest
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/shelf.git
cd shelf

# Build the image
docker build -t shelf:latest .

# Run the container
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  shelf:latest
```

### Configuration Options

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ABS_URL` | Audiobookshelf server URL | Yes | - |
| `ABS_TOKEN` | Audiobookshelf API token | Yes | - |
| `APP_TITLE` | Dashboard title | No | Shelf |
| `CACHE_TTL` | Cache duration (seconds) | No | 300 |
| `ITEMS_PER_ROW` | Books per row in grid | No | 5 |
| `THEME` | UI theme (dark/light) | No | dark |

### Accessing the Dashboard

After starting the container, access Shelf at:
```
http://localhost:8501
```

Or if running on a server:
```
http://your-server-ip:8501
```

## Docker Compose

Docker Compose provides easier configuration management and multi-container orchestration.

### Setup

1. **Create a `docker-compose.yml` file:**

```yaml
version: '3.8'

services:
  shelf:
    image: shelf:latest
    container_name: shelf
    ports:
      - "8501:8501"
    environment:
      - ABS_URL=https://your-audiobookshelf-url
      - ABS_TOKEN=your_api_token
      - APP_TITLE=My Audiobook Stats
      - CACHE_TTL=300
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

2. **Or use environment file:**

Create a `.env` file:
```env
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token
APP_TITLE=Shelf
```

Update `docker-compose.yml`:
```yaml
version: '3.8'

services:
  shelf:
    image: shelf:latest
    container_name: shelf
    ports:
      - "8501:8501"
    env_file:
      - .env
    restart: unless-stopped
```

3. **Start the service:**

```bash
docker-compose up -d
```

4. **View logs:**

```bash
docker-compose logs -f shelf
```

5. **Stop the service:**

```bash
docker-compose down
```

## Unraid

Shelf includes a Community Applications template for easy installation on Unraid.

### Installation

1. **Navigate to Docker tab** in Unraid web interface
2. **Click "Add Container"**
3. **Select "Shelf" from template list** (if available)
4. **Configure required fields:**
   - **Audiobookshelf URL**: Your Audiobookshelf server URL
   - **API Token**: Your Audiobookshelf API token
   - **Port**: Default 8501 (change if needed)

5. **Click "Apply"**

### Manual Template Installation

If the template isn't available:

1. Click "Add Container"
2. Switch to "Advanced View"
3. Fill in the following:

**Basic:**
- Name: `shelf`
- Repository: `shelf:latest`
- Network Type: `bridge`
- Port: `8501` → `8501`

**Environment Variables:**
- Key: `ABS_URL`, Value: `https://your-audiobookshelf-url`
- Key: `ABS_TOKEN`, Value: `your_api_token`

**Advanced:**
- Privileged: `No`
- Restart: `unless-stopped`

4. Click "Apply"

### Accessing on Unraid

Navigate to: `http://[unraid-ip]:8501`

Or add a custom icon link in your dashboard.

## Local Development

For development and testing without Docker.

### Prerequisites
- Python 3.11 or higher
- pip
- Audiobookshelf instance

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/shelf.git
cd shelf
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor
```

5. **Run the application:**
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

### Development Tips

- **Auto-reload**: Streamlit automatically reloads when you save changes
- **Debug mode**: Set `STREAMLIT_DEBUG=1` for more verbose logging
- **Cache clearing**: Click "Clear cache" in the Streamlit menu to force data refresh

## Production Considerations

### Reverse Proxy

Using a reverse proxy (Nginx, Caddy, Traefik) is recommended for production.

#### Nginx Example

```nginx
server {
    listen 80;
    server_name shelf.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

#### Caddy Example

```
shelf.yourdomain.com {
    reverse_proxy localhost:8501
}
```

### HTTPS/SSL

For secure connections:

1. **Using Let's Encrypt with Caddy** (automatic):
```
shelf.yourdomain.com {
    reverse_proxy localhost:8501
}
```

2. **Using Let's Encrypt with Nginx**:
```bash
certbot --nginx -d shelf.yourdomain.com
```

### Performance Tuning

1. **Adjust cache TTL** for your usage pattern:
   - High traffic: Increase `CACHE_TTL` (e.g., 600 seconds)
   - Real-time updates needed: Decrease `CACHE_TTL` (e.g., 60 seconds)

2. **Resource limits** (Docker):
```yaml
services:
  shelf:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Monitoring

Monitor container health:
```bash
# Docker
docker logs shelf

# Docker Compose
docker-compose logs -f shelf

# Health check
curl http://localhost:8501/_stcore/health
```

### Backup

No data is stored by Shelf itself. All data comes from Audiobookshelf. However, you may want to backup:
- Configuration files (docker-compose.yml, .env)
- Any customizations made to the code

### Updates

#### Docker
```bash
# Pull latest image
docker pull shelf:latest

# Recreate container
docker stop shelf
docker rm shelf
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  shelf:latest
```

#### Docker Compose
```bash
docker-compose pull
docker-compose up -d
```

### Troubleshooting

**Cannot connect to Audiobookshelf:**
- Verify `ABS_URL` is correct and accessible
- Check if API token is valid
- Ensure network connectivity between containers

**Port already in use:**
- Change the host port: `-p 8502:8501`

**High memory usage:**
- Reduce `CACHE_TTL` to clear cache more frequently
- Decrease `ITEMS_PER_ROW` for less data processing

**Slow loading:**
- Increase `CACHE_TTL` to cache data longer
- Check Audiobookshelf server response times
- Ensure adequate resources allocated

## Getting Help

- Check the [README](README.md) for general information
- Review [CONTRIBUTING](CONTRIBUTING.md) for development help
- Open an issue on GitHub for bugs or feature requests
