# ReadingView

A self-hosted dashboard for visualizing audiobook listening statistics from Audiobookshelf.

## Features

- Library view with cover art, progress bars, and sorting
- Statistics dashboard with charts (monthly/yearly completions, listening hours)
- Author browser with Open Library bios and photos
- Release tracker for upcoming books
- Notification support for tracked releases
- Direct Audiobookshelf API integration
- Docker + Unraid support with automated builds

## Quick Start

```bash
git clone https://github.com/reloadfast/readingview.git
cd readingview
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # edit with your credentials
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

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Docker, Docker Compose, Unraid, reverse proxy, local dev
- **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** — CI/CD pipeline setup
- **[NOTIFICATIONS.md](NOTIFICATIONS.md)** — Apprise notification setup (Telegram, Discord, etc.)
- **[OPEN_LIBRARY_USER_GUIDE.md](OPEN_LIBRARY_USER_GUIDE.md)** — Release tracker search guide

## License

MIT License
