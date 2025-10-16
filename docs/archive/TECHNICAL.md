# Technical Documentation

## Architecture Overview

### Design Patterns Used

1. **Service Layer Pattern**: Business logic separated in services
   - `AceProxyService`: AceStream proxy management
   - `ChannelScraperService`: Channel scraping logic
   - `EPGService`: EPG data management

2. **Repository Pattern**: Data access abstraction (ready for expansion)
   - Future: separate data access from business logic

3. **Dependency Injection**: FastAPI's dependency system
   - Database sessions via `get_db()`
   - Configuration via `get_config()`

4. **Factory Pattern**: Model creation and configuration

### Technology Stack

#### Backend
- **FastAPI**: Modern async web framework
- **SQLAlchemy 2.0**: ORM with typed mappings
- **Alembic**: Database migrations (ready to implement)
- **aiohttp**: Async HTTP client/server
- **Pydantic**: Data validation and settings

#### Security
- **passlib + bcrypt**: Password hashing
- **python-jose**: JWT tokens
- **python-multipart**: Form data handling

#### Data Processing
- **BeautifulSoup4**: HTML parsing
- **lxml**: XML/HTML processing
- **xmltodict**: XML parsing
- **defusedxml**: Secure XML parsing

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0,
    is_trial BOOLEAN DEFAULT 0,
    max_connections INTEGER DEFAULT 1,
    created_at DATETIME,
    expiry_date DATETIME
);

-- Channels table
CREATE TABLE channels (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    acestream_id VARCHAR(100) UNIQUE,
    category_id INTEGER,
    logo_url VARCHAR(500),
    epg_id VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    is_online BOOLEAN,
    created_at DATETIME,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Categories table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- EPG Programs table
CREATE TABLE epg_programs (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    category VARCHAR(100),
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

-- Scraper URLs table
CREATE TABLE scraper_urls (
    id INTEGER PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    is_enabled BOOLEAN DEFAULT 1,
    scraper_type VARCHAR(50) DEFAULT 'auto',
    last_scraped DATETIME,
    channels_found INTEGER DEFAULT 0
);
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_channels_acestream ON channels(acestream_id);
CREATE INDEX idx_channels_epg ON channels(epg_id);
CREATE INDEX idx_channels_active ON channels(is_active);
CREATE INDEX idx_epg_channel_time ON epg_programs(channel_id, start_time, end_time);
CREATE INDEX idx_users_username ON users(username);
```

## API Design

### Xtream Codes API Compliance

The implementation follows the official Xtream Codes API specification:

#### Authentication
- Username/password based
- Session management
- Connection limits per user

#### Endpoints Implemented
```python
# User info and server info
GET /player_api.php?username={user}&password={pass}

# Live streams
GET /player_api.php?action=get_live_categories
GET /player_api.php?action=get_live_streams
GET /player_api.php?action=get_live_streams&category_id={id}

# EPG
GET /player_api.php?action=get_short_epg&stream_id={id}
GET /player_api.php?action=get_simple_data_table&stream_id={id}

# Streaming
GET /{username}/{password}/{stream_id}.{ext}

# Playlist
GET /get.php?username={user}&password={pass}&type=m3u_plus

# EPG XML
GET /xmltv.php
```

### Response Formats

#### User Info Response
```json
{
    "user_info": {
        "username": "admin",
        "password": "pass",
        "message": "Welcome",
        "auth": 1,
        "status": "Active",
        "exp_date": null,
        "is_trial": "0",
        "active_cons": "0",
        "created_at": 1234567890,
        "max_connections": "2"
    },
    "server_info": {
        "url": "http://server.com",
        "port": "58055",
        "server_protocol": "http",
        "timezone": "Europe/Rome",
        "timestamp_now": 1234567890
    }
}
```

#### Live Streams Response
```json
[
    {
        "num": 1,
        "name": "Channel Name",
        "stream_type": "live",
        "stream_id": 1,
        "stream_icon": "http://...",
        "epg_channel_id": "channel_id",
        "category_id": "1"
    }
]
```

## AceStream Proxy Implementation

### Stream Multiplexing

The proxy implements efficient stream multiplexing:

```python
class OngoingStream:
    """
    Represents a single AceStream with multiple clients
    """
    - stream_id: Unique stream identifier
    - clients: Set of connected clients
    - buffer: Shared buffer queue
    - fetch_task: Background fetch task
```

### Flow
1. Client requests stream
2. Check if stream already exists
3. If exists: add client to existing stream
4. If not: create new stream and fetch from AceStream
5. Distribute chunks to all connected clients
6. When last client disconnects: cleanup stream

### Benefits
- Reduces load on AceStream engine
- Better bandwidth usage
- Faster start for subsequent clients
- Automatic cleanup

## Channel Scraper

### Supported Formats

1. **JSON**
```json
{
    "channels": [
        {
            "id": "acestream_id",
            "name": "Channel Name",
            "category": "Sports",
            "logo": "http://..."
        }
    ]
}
```

2. **M3U/M3U8**
```m3u
#EXTM3U
#EXTINF:-1 tvg-id="id" tvg-logo="http://..." group-title="Sports",Channel Name
acestream://acestream_id
```

3. **HTML**
```html
<a href="acestream://acestream_id">Channel Name</a>
```

### Auto-detection Logic
```python
def detect_format(content, content_type):
    if 'application/json' in content_type:
        return 'json'
    elif content.startswith('#EXTM3U'):
        return 'm3u'
    else:
        return 'html'
```

## EPG Service

### XML Processing

EPG XML format (XMLTV):
```xml
<tv>
    <channel id="channel_id">
        <display-name>Channel Name</display-name>
        <icon src="http://..."/>
    </channel>
    <programme start="20240101120000" stop="20240101130000" channel="channel_id">
        <title>Program Title</title>
        <desc>Description</desc>
        <category>Category</category>
    </programme>
</tv>
```

### Processing Steps
1. Fetch XML (with gzip support)
2. Parse with ElementTree
3. Extract channels and programs
4. Match with database channels via epg_id
5. Store in database
6. Serve via API

## Performance Optimization

### Database
- Connection pooling (configurable)
- Lazy loading relationships
- Indexed queries
- Batch operations for EPG

### Async Operations
- Non-blocking I/O with aiohttp
- Background tasks for scraping/EPG
- Async database sessions (future)

### Caching Strategy
- EPG cached in database
- Channel metadata cached
- Stream info cached during active session

### Resource Management
```python
# Automatic cleanup
- Streams cleanup when no clients
- EPG cleanup for old programs
- Session cleanup for expired users
```

## Configuration Management

### Environment Variables
All configuration via environment variables with defaults:

```python
class Config(BaseSettings):
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Validation
Pydantic validates all settings:
- Type checking
- Range validation
- Required fields
- Default values

## Security Best Practices

### Password Security
```python
# Never store plain passwords
password_hash = bcrypt.hash(password)

# Always verify with timing-safe comparison
bcrypt.verify(password, password_hash)
```

### JWT Tokens
```python
# Short expiry for security
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days default

# Strong secret key
SECRET_KEY = secrets.token_urlsafe(32)
```

### Input Validation
- All API inputs validated with Pydantic
- SQL injection prevention via ORM
- XSS prevention in responses
- CORS properly configured

## Error Handling

### Graceful Degradation
```python
try:
    # Fetch EPG
    epg_data = await fetch_epg(url)
except Exception as e:
    logger.error(f"EPG fetch failed: {e}")
    # Continue with cached data
    epg_data = get_cached_epg()
```

### Health Checks
- Service-level health checks
- Component status monitoring
- Automatic recovery for transient failures

## Deployment

### Docker Best Practices
```dockerfile
# Multi-stage build (future)
FROM python:3.11-slim as builder
# Install dependencies
FROM python:3.11-slim
# Copy only needed files
```

### Environment Variables
```yaml
# All secrets via environment
environment:
  - SECRET_KEY=${SECRET_KEY}
  - ADMIN_PASSWORD=${ADMIN_PASSWORD}
```

### Volumes
```yaml
volumes:
  - ./data:/app/data        # Database persistence
  - ./logs:/app/logs        # Log persistence
  - ./config:/app/config    # Config persistence
```

## Monitoring & Logging

### Structured Logging
```python
logger.info(
    "Stream started",
    extra={
        "stream_id": stream_id,
        "client_count": len(clients),
        "user": username
    }
)
```

### Metrics (Future)
- Stream count
- User count
- Channel availability
- API response times
- Error rates

## Testing Strategy

### Unit Tests
```python
# Test services in isolation
def test_scraper_service():
    service = ChannelScraperService(mock_db)
    channels = await service.scrape_url(test_url)
    assert len(channels) > 0
```

### Integration Tests
```python
# Test API endpoints
def test_xtream_api():
    response = client.get("/player_api.php?username=test&password=test")
    assert response.status_code == 200
```

### Load Testing
```bash
# Use tools like locust or k6
k6 run --vus 100 --duration 30s load_test.js
```

## Future Enhancements

### Phase 1 (Core)
- [ ] Complete admin dashboard
- [ ] Database migrations with Alembic
- [ ] Enhanced error handling
- [ ] Prometheus metrics

### Phase 2 (Features)
- [ ] VOD support
- [ ] Series support
- [ ] Catchup/Archive
- [ ] Multi-language support

### Phase 3 (Scale)
- [ ] PostgreSQL support
- [ ] Redis caching
- [ ] Multi-server clustering
- [ ] Load balancing

### Phase 4 (Advanced)
- [ ] CDN integration
- [ ] Transcoding support
- [ ] Mobile apps
- [ ] Web player

## Contributing

### Code Style
- Black for formatting
- Flake8 for linting
- Type hints encouraged
- Docstrings for public APIs

### Git Workflow
```bash
# Feature branch
git checkout -b feature/new-feature

# Commits
git commit -m "feat: add new feature"

# Pull request
# Include tests and documentation
```

### Review Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance acceptable
