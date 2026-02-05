# Architecture Overview

This document provides a detailed overview of Shelf's architecture, design decisions, and extensibility patterns.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                      (Streamlit App)                         │
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Library View    │         │ Statistics View   │          │
│  │  Component       │         │   Component       │          │
│  └────────┬─────────┘         └────────┬──────────┘          │
└───────────┼──────────────────────────────┼───────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Application Logic Layer                    │
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   API Clients    │         │     Utilities     │          │
│  │                  │         │                   │          │
│  │ - Audiobookshelf │         │ - Date Formatting │          │
│  │ - Future: Calibre│         │ - Stats Calc      │          │
│  │ - Future: Manual │         │ - Caching         │          │
│  └────────┬─────────┘         └────────┬──────────┘          │
└───────────┼──────────────────────────────┼───────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Data Source Layer                       │
│                                                               │
│  ┌──────────────────┐    ┌──────────────┐   ┌────────────┐ │
│  │ Audiobookshelf   │    │ Future:      │   │  Future:   │ │
│  │     Server       │    │   Calibre    │   │   Manual   │ │
│  │                  │    │   Server     │   │  Database  │ │
│  └──────────────────┘    └──────────────┘   └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Application Entry Point

**File:** `app.py`

- Initializes Streamlit configuration
- Handles environment validation
- Manages routing between views
- Applies custom theming
- Implements error boundaries

### Configuration Management

**File:** `config.py`

- Centralizes all configuration
- Loads environment variables
- Validates required settings
- Provides type-safe access
- No hard-coded values

**Design Pattern:** Singleton configuration object

### API Layer

**Directory:** `api/`

#### Current Implementation
- `audiobookshelf.py`: Full-featured ABS client

#### Design Patterns
- **Client Pattern**: Each data source has its own client
- **Adapter Pattern**: Data adapters normalize different sources
- **Error Handling**: Graceful degradation on failures

#### Extensibility
New data sources follow this template:

```python
class DataSourceAPI:
    def __init__(self, config_params):
        """Initialize with source-specific config"""
        
    def test_connection(self) -> bool:
        """Verify connectivity"""
        
    def get_items(self) -> List[Dict]:
        """Fetch data in source format"""
        
class DataSourceAdapter:
    @staticmethod
    def to_standard_format(source_data):
        """Convert to Shelf's internal format"""
```

### Component Layer

**Directory:** `components/`

#### Library View (`library.py`)
- Displays audiobooks in grid layout
- Handles sorting and filtering
- Renders progress information
- Responsive design

**Responsibilities:**
- Data presentation
- User interaction
- Visual feedback
- Layout management

**Dependencies:**
- API clients for data
- Utilities for formatting
- Streamlit for rendering

#### Statistics View (`statistics.py`)
- Aggregates listening data
- Generates visualizations
- Displays metrics
- Provides insights

**Responsibilities:**
- Data aggregation
- Chart generation
- Metric calculation
- Insight presentation

### Utilities Layer

**Directory:** `utils/`

#### Helpers (`helpers.py`)
- Date formatting functions
- Statistics calculations
- Caching decorators
- Error display helpers

**Design Pattern:** Pure functions for testability

## Data Flow

### Library View Data Flow

```
User Opens App
       │
       ▼
   app.py validates config
       │
       ▼
   API client initialized
       │
       ▼
   render_library_view() called
       │
       ▼
   API: get_user_items_in_progress()
       │
       ▼
   Extract metadata with AudiobookData
       │
       ▼
   Sort and filter items
       │
       ▼
   Render grid with Streamlit
       │
       ▼
   Display to user
```

### Statistics View Data Flow

```
User Switches to Stats Tab
       │
       ▼
   render_statistics_view() called
       │
       ├─────────────────┬──────────────────┐
       ▼                 ▼                  ▼
   get_sessions()   get_stats()      get_items()
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                         ▼
          Calculate aggregate statistics
                         │
                         ▼
               Generate visualizations
                         │
                         ▼
                 Display to user
```

## Design Decisions

### Why Streamlit?

**Advantages:**
- Rapid development
- Easy local testing
- No frontend/backend split
- Built-in reactivity
- Widget library

**Trade-offs:**
- Limited customization vs full SPA
- Python-only (no JS needed)
- Single-page limitation (acceptable for MVP)

**Extensibility:** Can migrate to React/FastAPI later if needed

### Why No Database Initially?

**Rationale:**
- Audiobookshelf is source of truth
- Reduces deployment complexity
- Easier local development
- No data synchronization needed
- Simpler architecture

**When to Add:**
- Multi-user features needed
- Manual entry support
- Offline access required
- Complex analytics
- Performance optimization

### Caching Strategy

**Implementation:**
- Streamlit's `@st.cache_data` decorator
- Default 300 second TTL
- Per-user caching (session-based)

**Benefits:**
- Reduces API load
- Improves response times
- User-specific data

**Configuration:**
- Adjustable via `CACHE_TTL` env var
- Can be disabled for testing

## Extensibility Points

### Adding Data Sources

1. **Create API Client** (`api/new_source.py`)
2. **Create Data Adapter** (normalize to standard format)
3. **Update Config** (add new env vars)
4. **Modify Components** (support multiple sources)
5. **Update Documentation**

### Adding Features

#### New Visualization
1. Add function to `components/statistics.py`
2. Use pandas/plotly/streamlit charts
3. Follow existing styling patterns

#### New View
1. Create new component file
2. Add to tab navigation in `app.py`
3. Import required utilities

#### Database Integration
1. Add database config to `config.py`
2. Create `database/` directory
3. Implement migration scripts
4. Add ORM models
5. Update components to use DB
6. Maintain fallback to direct API

### Multi-User Support

**Architecture Changes Needed:**

```
Current: Single user → Single API client
Future:  Multiple users → User management → Per-user API clients

┌──────────────┐
│   User Auth  │  (Add authentication layer)
└──────┬───────┘
       │
┌──────▼───────┐
│ User Manager │  (Manage user sessions)
└──────┬───────┘
       │
┌──────▼───────┐
│ API Clients  │  (Per-user instances)
└──────────────┘
```

**Implementation Steps:**
1. Add authentication (Streamlit auth, OAuth)
2. Store user credentials securely
3. Create per-user API clients
4. Add user management UI
5. Implement data isolation

## Security Considerations

### Current Implementation

**Secure:**
- No credentials in code
- Environment variable config
- Token masking in logs
- HTTPS for API calls

**Public-Ready:**
- No PII in codebase
- Configurable endpoints
- No hard-coded IPs

### Future Considerations

When adding multi-user:
- Implement proper authentication
- Encrypt stored credentials
- Use secrets management
- Add rate limiting
- Implement audit logging

## Performance Optimization

### Current Optimizations

1. **API Caching**: 5-minute default cache
2. **Image Loading**: Direct URLs from ABS
3. **Lazy Loading**: Only fetch displayed data
4. **Connection Pooling**: Reuse HTTP connections

### Future Optimizations

1. **Pagination**: Load items in batches
2. **Database**: Cache frequently accessed data
3. **CDN**: Serve static assets
4. **Compression**: Enable response compression
5. **Worker Threads**: Parallel API calls

## Deployment Architecture

### Docker Deployment

```
┌────────────────────────────────────────┐
│           Docker Container              │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      Streamlit Application       │  │
│  │         (Port 8501)              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  Environment Variables:                 │
│  - ABS_URL                             │
│  - ABS_TOKEN                           │
│  - APP_TITLE                           │
│  - CACHE_TTL                           │
└────────────────────────────────────────┘
              │
              ▼ (Network)
┌────────────────────────────────────────┐
│     Audiobookshelf Server              │
│        (External Service)               │
└────────────────────────────────────────┘
```

### Production Deployment

```
Internet
    │
    ▼
┌───────────────┐
│ Reverse Proxy │  (Nginx/Caddy)
│   + SSL/TLS   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│     Shelf     │  (Docker Container)
│   Container   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Audiobookshelf│  (External/Internal)
│     Server    │
└───────────────┘
```

## Testing Strategy

### Current Testing

Manual testing with real Audiobookshelf instance

### Future Testing

1. **Unit Tests**: Test utilities and data transformations
2. **Integration Tests**: Test API clients
3. **E2E Tests**: Test full user workflows
4. **Mock API**: Test without real server

## Code Organization Principles

### Modularity
- Each component has single responsibility
- Clear interfaces between layers
- Minimal coupling

### Maintainability
- Type hints for clarity
- Comprehensive docstrings
- Consistent naming conventions
- Clear error messages

### Extensibility
- Plugin architecture for data sources
- Component-based UI
- Configuration-driven behavior
- Version-safe APIs

## Migration Paths

### To Full-Stack Application

If outgrowing Streamlit:

1. **Backend**: FastAPI with SQLAlchemy
2. **Frontend**: React or Vue.js
3. **API**: RESTful or GraphQL
4. **Database**: PostgreSQL or SQLite
5. **Authentication**: OAuth2 / JWT

Shelf's modular design makes this transition straightforward:
- API clients remain unchanged
- Business logic easily ported
- Data models already defined
- Configuration system adapts

### To Multi-Tenancy

For SaaS deployment:

1. Add user authentication
2. Implement tenant isolation
3. Per-tenant database schemas
4. Subscription management
5. Admin interface

## Conclusion

Shelf's architecture prioritizes:

1. **Simplicity**: Easy to understand and deploy
2. **Extensibility**: Ready for future growth
3. **Maintainability**: Clean, well-documented code
4. **Privacy**: No hard-coded secrets, self-hosted
5. **Performance**: Cached, efficient data access

The design allows starting simple while supporting sophisticated features as the project evolves.
