# Shelf - Project Summary

## What is Shelf?

Shelf is a self-hosted dashboard application for visualizing audiobook listening statistics, primarily from Audiobookshelf. It provides an elegant, bookshelf-style interface to track your reading journey with progress tracking, completion statistics, and listening insights.

## Project Status: MVP Complete ✅

Version 1.0.0 is production-ready with:
- ✅ Library grid view with cover art and progress
- ✅ Statistics dashboard with charts
- ✅ Audiobookshelf integration
- ✅ Docker containerization
- ✅ Unraid support
- ✅ Public-ready (no secrets in code)
- ✅ Comprehensive documentation

## Quick Start

### Docker (Fastest)

```bash
docker run -d \
  --name shelf \
  -p 8501:8501 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  shelf:latest
```

Then open: http://localhost:8501

### Docker Compose

1. Copy `.env.example` to `.env`
2. Fill in your Audiobookshelf credentials
3. Run: `docker-compose up -d`

### Local Development

```bash
pip install -r requirements.txt
export ABS_URL=https://your-audiobookshelf-url
export ABS_TOKEN=your_api_token
streamlit run app.py
```

## Project Structure

```
shelf/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── api/
│   └── audiobookshelf.py    # ABS API client
├── components/
│   ├── library.py           # Library grid view
│   └── statistics.py        # Statistics dashboard
├── utils/
│   └── helpers.py           # Utility functions
├── Dockerfile               # Container definition
├── docker-compose.yml       # Compose configuration
├── unraid-template.xml      # Unraid template
└── docs/
    ├── README.md            # Project overview
    ├── DEPLOYMENT.md        # Deployment guide
    ├── API.md               # API documentation
    ├── ARCHITECTURE.md      # Architecture overview
    └── CONTRIBUTING.md      # Contribution guide
```

## Key Features

### Library View
- **Bookshelf Grid**: Visual display of audiobooks with cover art
- **Progress Tracking**: Real-time progress bars and percentages
- **Start Dates**: See when you started each book
- **Time Remaining**: Know how much listening time is left
- **Smart Sorting**: Sort by progress, date, or title

### Statistics View
- **Completion Metrics**: Total books completed, hours listened
- **Monthly Trends**: Line chart showing books completed per month
- **Yearly Overview**: Bar chart of annual completions
- **Average Calculations**: Books per month averages
- **Historical Data**: Full listening history from Audiobookshelf

### Technical Features
- **Environment-Based Config**: No hard-coded secrets
- **API Caching**: Reduces load on Audiobookshelf server
- **Responsive Design**: Works on desktop and mobile
- **Health Checks**: Docker health monitoring
- **Error Handling**: Graceful error messages and recovery

## Design Philosophy

### Minimalism First
- Start with essential features only
- Clean, intuitive interface
- No feature bloat

### Extensibility Built-In
- Modular architecture
- Plugin-ready for new data sources
- Database-optional design
- Multi-user ready (not implemented)

### Privacy-First
- Self-hosted
- No external analytics
- No telemetry
- No hard-coded credentials

### Developer-Friendly
- Clear code structure
- Comprehensive docs
- Type hints throughout
- Easy to extend

## Technology Stack

**Frontend/App**: Streamlit (Python)
- Rapid development
- Easy local testing
- Built-in widgets

**API Client**: Requests (Python)
- Robust HTTP handling
- Session management
- Error handling

**Deployment**: Docker
- Containerized
- Portable
- Easy updates

**Visualization**: Pandas + Streamlit Charts
- Built-in charting
- DataFrame manipulation
- No external chart libraries

## Configuration

All configuration via environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ABS_URL` | Yes | Audiobookshelf server URL | - |
| `ABS_TOKEN` | Yes | API authentication token | - |
| `APP_TITLE` | No | Dashboard title | Shelf |
| `CACHE_TTL` | No | Cache duration (seconds) | 300 |
| `ITEMS_PER_ROW` | No | Grid columns | 5 |
| `THEME` | No | UI theme (dark/light) | dark |

## Getting Your API Token

1. Log into Audiobookshelf
2. Go to Settings → Users
3. Click your user
4. Click "Generate API Token"
5. Copy the token

## Deployment Options

### Home Server
- Docker or Docker Compose
- Reverse proxy optional
- Local network access

### Unraid
- Use provided XML template
- Community Applications compatible
- One-click install

### Cloud VPS
- Docker deployment
- Nginx/Caddy reverse proxy
- Let's Encrypt SSL

## Architecture Highlights

### Stateless Design
- No database required (MVP)
- Direct API access
- Simpler deployment

### Layered Architecture
```
UI Layer (Streamlit Components)
    ↓
Logic Layer (API Clients, Utilities)
    ↓
Data Layer (Audiobookshelf Server)
```

### Caching Strategy
- Streamlit session-based caching
- 5-minute default TTL
- Per-user cache isolation

## Future Roadmap

### Near-Term (v1.1-1.5)
- [ ] Reading goals
- [ ] Book notes/ratings
- [ ] Genre analytics
- [ ] Author statistics
- [ ] Series tracking
- [ ] Export data (CSV/JSON)

### Mid-Term (v2.0)
- [ ] Multi-user support
- [ ] Calibre integration
- [ ] Manual entry system
- [ ] Advanced charts
- [ ] Mobile app
- [ ] Dark/light theme toggle

### Long-Term (v3.0+)
- [ ] Social features
- [ ] Book recommendations
- [ ] Reading challenges
- [ ] Community insights
- [ ] Plugin system
- [ ] API for third-party apps

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas needing help:
- Additional data sources
- UI improvements
- Performance optimization
- Documentation
- Testing

## Documentation

- **README.md**: Project overview and quick start
- **DEPLOYMENT.md**: Detailed deployment instructions
- **API.md**: API documentation for developers
- **ARCHITECTURE.md**: System architecture and design
- **CONTRIBUTING.md**: Contribution guidelines
- **CHANGELOG.md**: Version history

## Support

- **Issues**: GitHub issue tracker
- **Discussions**: GitHub discussions
- **Documentation**: Full docs in repository

## License

MIT License - See [LICENSE](LICENSE) file

Free to use, modify, and distribute.

## Acknowledgments

Built for the Audiobookshelf community.

Powered by:
- [Audiobookshelf](https://www.audiobookshelf.org/)
- [Streamlit](https://streamlit.io/)
- [Docker](https://www.docker.com/)

## Project Name Rationale

**"Shelf"** was chosen because:
- Short and memorable
- References bookshelf/library concept
- Source-agnostic (not locked to Audiobookshelf)
- Easily extensible (Shelf Analytics, Shelf Dashboard)
- Available as domain/package name
- Professional yet approachable

## Success Metrics

MVP Success Criteria (All Met ✅):
- ✅ Displays audiobook library with covers
- ✅ Shows progress for in-progress books
- ✅ Visualizes completion statistics
- ✅ Docker deployment ready
- ✅ No hard-coded credentials
- ✅ Comprehensive documentation
- ✅ Unraid support

## Next Steps

1. **Deploy**: Try it with your Audiobookshelf instance
2. **Feedback**: Open issues for bugs or features
3. **Contribute**: Add features or improve docs
4. **Share**: Tell other audiobook listeners!

## Getting Help

1. Check documentation first
2. Search existing issues
3. Open new issue with details
4. Include logs and config (remove secrets)

---

**Built with ❤️ for audiobook enthusiasts**

Start tracking your listening journey today!
