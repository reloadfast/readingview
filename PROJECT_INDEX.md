# Shelf - Complete Project Index

This document provides a complete overview of all files in the Shelf project and their purposes.

## Project Structure

```
shelf/
├── 📄 Core Application Files
│   ├── app.py                      # Main Streamlit application entry point
│   ├── config.py                   # Configuration management (env vars)
│   └── requirements.txt            # Python dependencies
│
├── 📁 API Layer
│   └── api/
│       └── audiobookshelf.py      # Audiobookshelf API client
│
├── 📁 UI Components
│   └── components/
│       ├── library.py             # Library grid view component
│       └── statistics.py          # Statistics dashboard component
│
├── 📁 Utilities
│   └── utils/
│       └── helpers.py             # Helper functions and utilities
│
├── 🐳 Docker & Deployment
│   ├── Dockerfile                 # Container definition
│   ├── docker-compose.yml         # Compose configuration
│   ├── .dockerignore             # Docker build exclusions
│   ├── unraid-template.xml        # Unraid Community Apps template
│   ├── build.sh                   # Docker build script
│   └── verify.sh                  # Build verification script
│
├── ⚙️ Configuration
│   ├── .env.example               # Environment variables template
│   └── .gitignore                # Git exclusions
│
├── 📚 Documentation
│   ├── README.md                  # Project overview and quick start
│   ├── GETTING_STARTED.md         # Detailed setup guide
│   ├── DEPLOYMENT.md              # Deployment instructions
│   ├── API.md                     # API documentation
│   ├── ARCHITECTURE.md            # Architecture overview
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   ├── CHANGELOG.md               # Version history
│   ├── PROJECT_SUMMARY.md         # Project summary
│   └── PROJECT_INDEX.md           # This file
│
└── 📜 Legal
    └── LICENSE                    # MIT License
```

## File Purposes

### Core Application Files

#### `app.py`
**Purpose**: Main application entry point
**Contains**:
- Streamlit page configuration
- Custom CSS theming
- Navigation between views
- Configuration validation
- Error handling
- API client initialization

**Key Functions**:
- `main()`: Application entry point
- `apply_custom_theme()`: Applies distinctive dark theme
- `show_configuration_guide()`: Displays setup instructions

#### `config.py`
**Purpose**: Centralized configuration management
**Contains**:
- Environment variable loading
- Configuration validation
- Default values
- Type-safe configuration access

**Key Class**:
- `Config`: Singleton configuration object

**Environment Variables Managed**:
- `ABS_URL`: Audiobookshelf server URL
- `ABS_TOKEN`: API authentication token
- `APP_TITLE`: Dashboard title
- `CACHE_TTL`: Cache duration
- `ITEMS_PER_ROW`: Grid layout
- `THEME`: UI theme

#### `requirements.txt`
**Purpose**: Python package dependencies
**Contains**:
- `streamlit`: Web framework
- `requests`: HTTP client
- `pandas`: Data manipulation

### API Layer

#### `api/audiobookshelf.py`
**Purpose**: Audiobookshelf API integration
**Contains**:
- `AudiobookshelfAPI`: Main API client class
- `AudiobookData`: Data helper class

**Key Methods**:
- `test_connection()`: Verify API connectivity
- `get_libraries()`: Fetch library list
- `get_library_items()`: Fetch items in library
- `get_user_items_in_progress()`: In-progress audiobooks
- `get_user_listening_sessions()`: Historical sessions
- `get_user_listening_stats()`: Aggregate statistics
- `get_cover_url()`: Generate cover image URL

**Data Helpers**:
- `extract_metadata()`: Parse audiobook metadata
- `calculate_progress()`: Compute progress metrics
- `format_duration()`: Format time durations

### UI Components

#### `components/library.py`
**Purpose**: Library grid view
**Contains**:
- `render_library_view()`: Main rendering function

**Features**:
- Bookshelf-style grid layout
- Cover image display
- Progress bars
- Start date tracking
- Time remaining calculation
- Sorting options
- Custom CSS styling

#### `components/statistics.py`
**Purpose**: Statistics dashboard
**Contains**:
- `render_statistics_view()`: Main rendering function

**Features**:
- Overall metrics (books completed, hours listened)
- Yearly completion bar chart
- Monthly completion line chart
- Average calculations
- Detailed data tables
- Custom CSS styling

### Utilities

#### `utils/helpers.py`
**Purpose**: Shared utility functions
**Contains**:
- Date formatting functions
- Statistics calculations
- Session grouping
- Caching decorators
- Error display helpers

**Key Functions**:
- `format_date()`: Full date formatting
- `format_date_short()`: Short date formatting
- `calculate_completion_stats()`: Aggregate statistics
- `get_monthly_completion_counts()`: Monthly breakdowns
- `get_yearly_completion_counts()`: Yearly breakdowns
- `cached_api_call()`: Caching decorator
- `display_error()`: Error message display

### Docker & Deployment

#### `Dockerfile`
**Purpose**: Container definition
**Strategy**: Multi-stage build for optimization
**Contains**:
- Python 3.11 base image
- Dependency installation
- Application code
- Streamlit configuration
- Health check definition

#### `docker-compose.yml`
**Purpose**: Docker Compose configuration
**Contains**:
- Service definition
- Port mapping
- Environment variables
- Restart policy
- Health checks

#### `.dockerignore`
**Purpose**: Exclude files from Docker build
**Excludes**:
- Python cache files
- Virtual environments
- Git files
- Development files
- Documentation

#### `unraid-template.xml`
**Purpose**: Unraid Community Applications template
**Contains**:
- Container configuration
- Port mappings
- Environment variables
- WebUI link
- Support links
- Category assignment

#### `build.sh`
**Purpose**: Docker build automation
**Features**:
- Version tagging
- Registry pushing
- Build verification
- Usage instructions

**Usage**:
```bash
./build.sh [version]
```

#### `verify.sh`
**Purpose**: Build verification
**Checks**:
- File structure
- Python syntax
- Docker build
- Dependencies

**Usage**:
```bash
./verify.sh
```

### Configuration

#### `.env.example`
**Purpose**: Environment variable template
**Contains**:
- All configuration options
- Example values
- Usage instructions

**Usage**: Copy to `.env` and fill in real values

#### `.gitignore`
**Purpose**: Git exclusions
**Excludes**:
- Python cache
- Virtual environments
- Environment files
- IDE files
- OS files
- Logs
- Databases

### Documentation

#### `README.md`
**Purpose**: Project overview
**Audience**: All users
**Contains**:
- Quick start guide
- Feature overview
- Configuration table
- Basic usage
- Links to other docs

#### `GETTING_STARTED.md`
**Purpose**: Detailed setup guide
**Audience**: New users
**Contains**:
- Step-by-step instructions
- Prerequisites
- Multiple deployment methods
- Troubleshooting
- First-time setup

#### `DEPLOYMENT.md`
**Purpose**: Deployment instructions
**Audience**: System administrators
**Contains**:
- Docker deployment
- Docker Compose setup
- Unraid installation
- Local development
- Production considerations
- Reverse proxy setup
- SSL configuration
- Monitoring
- Updates

#### `API.md`
**Purpose**: API documentation
**Audience**: Developers
**Contains**:
- Architecture overview
- API client usage
- Adding data sources
- Data models
- Best practices
- Testing strategies

#### `ARCHITECTURE.md`
**Purpose**: System architecture
**Audience**: Contributors, architects
**Contains**:
- High-level architecture
- Component design
- Data flow diagrams
- Design decisions
- Extensibility patterns
- Future roadmap

#### `CONTRIBUTING.md`
**Purpose**: Contribution guidelines
**Audience**: Contributors
**Contains**:
- Development setup
- Code standards
- PR guidelines
- Feature requests
- Bug reports
- Architecture principles

#### `CHANGELOG.md`
**Purpose**: Version history
**Audience**: All users
**Contains**:
- Version releases
- Feature additions
- Bug fixes
- Breaking changes

#### `PROJECT_SUMMARY.md`
**Purpose**: Quick project overview
**Audience**: Evaluators, new contributors
**Contains**:
- What is Shelf
- Key features
- Quick start
- Technology stack
- Future roadmap

#### `PROJECT_INDEX.md`
**Purpose**: Complete file reference (this file)
**Audience**: Developers, contributors
**Contains**:
- Complete file list
- File purposes
- Quick reference

### Legal

#### `LICENSE`
**Purpose**: Software license
**Type**: MIT License
**Permissions**:
- Commercial use
- Modification
- Distribution
- Private use

## Quick Reference by Task

### I want to...

**Run Shelf**
→ See `GETTING_STARTED.md`

**Deploy to production**
→ See `DEPLOYMENT.md`

**Understand the architecture**
→ See `ARCHITECTURE.md`

**Add a feature**
→ See `CONTRIBUTING.md` and `API.md`

**Fix a bug**
→ See `CONTRIBUTING.md`

**Integrate new data source**
→ See `API.md` - "Adding New Data Sources"

**Customize the UI**
→ Edit `components/library.py` or `components/statistics.py`

**Change configuration**
→ Edit `.env` or environment variables

**Build Docker image**
→ Run `./build.sh`

**Verify project**
→ Run `./verify.sh`

## Code Statistics

**Total Files**: 23
- Python: 6
- Markdown: 10
- Configuration: 4
- Scripts: 2
- License: 1

**Lines of Code** (approximate):
- Python: ~1,500 lines
- Documentation: ~3,000 lines
- Configuration: ~200 lines
- **Total**: ~4,700 lines

**Documentation Coverage**:
- Every major component documented
- API methods documented
- Configuration documented
- Examples provided throughout

## Development Workflow

1. **Setup**: `GETTING_STARTED.md`
2. **Code**: Edit files in `api/`, `components/`, `utils/`
3. **Test**: Run `streamlit run app.py`
4. **Verify**: Run `./verify.sh`
5. **Build**: Run `./build.sh`
6. **Deploy**: Use Docker or Docker Compose

## File Dependencies

```
app.py
  ├── config.py
  ├── api/audiobookshelf.py
  ├── components/library.py
  │   ├── api/audiobookshelf.py
  │   └── utils/helpers.py
  ├── components/statistics.py
  │   ├── api/audiobookshelf.py
  │   └── utils/helpers.py
  └── utils/helpers.py
```

## Maintenance

### Regular Updates
- **Dependencies**: Update `requirements.txt`
- **Documentation**: Keep in sync with code
- **Changelog**: Update on each release

### Testing Checklist
- [ ] Run `./verify.sh`
- [ ] Test Docker build
- [ ] Test local deployment
- [ ] Test Docker deployment
- [ ] Review documentation
- [ ] Update CHANGELOG

### Release Checklist
- [ ] Update version in CHANGELOG
- [ ] Update README if needed
- [ ] Tag release in Git
- [ ] Build and push Docker image
- [ ] Update Unraid template
- [ ] Announce release

## Contact & Support

**Issues**: GitHub issue tracker
**Docs**: This repository
**Discussions**: GitHub discussions

## Version

**Current Version**: 1.0.0
**Last Updated**: February 2, 2026
**Status**: Production Ready ✅

---

This index is maintained as part of the project documentation.
For the latest version, see the GitHub repository.
