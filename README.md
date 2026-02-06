# ReadingView

A self-hosted dashboard for visualizing audiobook listening statistics from Audiobookshelf.

## Quick Start (Local Development)

```bash
# Clone and setup
git clone https://github.com/yourusername/readingview.git
cd readingview
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Audiobookshelf credentials

# Run
streamlit run app.py
```

Access at: http://localhost:8506

## Configuration

Required environment variables in `.env`:

```env
ABS_URL=https://your-audiobookshelf-url
ABS_TOKEN=your_api_token
```

Get your API token: Audiobookshelf → Settings → Users → Generate API Token

## Development Workflow

1. **Develop locally**: `streamlit run app.py`
2. **Push to GitHub**: Triggers automatic Docker build
3. **Update Unraid**: Force update container

See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for detailed guide.

## GitHub Actions + Unraid Deployment

1. Setup GitHub Actions - see [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
2. Install on Unraid using template:
   ```
   https://raw.githubusercontent.com/yourusername/readingview/main/unraid-template.xml
   ```

## Documentation

- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Local development guide
- **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** - CI/CD setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - All deployment options

## Features

- Library view with progress tracking
- Statistics dashboard with charts
- Direct Audiobookshelf API integration
- Automated Docker builds
- Unraid support

## License

MIT License
