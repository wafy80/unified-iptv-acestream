# Unified IPTV AceStream Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

A unified IPTV platform that combines the best of acestream-scraper, pyacexy, and xtream_api into a complete solution for streaming AceStream content via IPTV clients.

## 🚀 Features

### Core Features
- **Automatic Scraping**: Automatic AceStream channel collection from multiple sources
- **Xtream Codes API**: Full compatibility with IPTV Smarters, Perfect Player, TiviMate, and other IPTV clients
- **Integrated AceStream Proxy**: Intelligent stream management with multiplexing
- **Complete EPG**: Electronic Program Guide with aggregation from multiple sources
- **User Management**: Complete authentication and authorization system
- **Web Dashboard**: Modern and intuitive administration interface

### Advanced Features
- Integrated AceStream Engine with Acexy proxy
- ZeroNet support for decentralized sources
- Cloudflare WARP for geo-unblocking
- Real-time channel status monitoring
- Configurable auto-rescraping
- SQLAlchemy database with migrations
- Health checking and monitoring
- Documented REST API (OpenAPI/Swagger)

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│              IPTV Client (Player)                       │
│  (IPTV Smarters, VLC, Kodi, Perfect Player)            │
└──────────────────────┬──────────────────────────────────┘
                       │ Xtream API
┌──────────────────────▼──────────────────────────────────┐
│           Unified IPTV Platform                         │
│                                                          │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Xtream API    │  │   Scraper    │  │  AceProxy   │ │
│  │   Server       │◄─┤   Service    │◄─┤   Service   │ │
│  └────────────────┘  └──────────────┘  └─────────────┘ │
│          │                   │                  │       │
│  ┌────────▼───────────────────▼──────────────────▼────┐ │
│  │         Database (SQLAlchemy + SQLite)            │ │
│  └───────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              AceStream Engine                           │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ Installation

### Method 1: Interactive Setup Wizard (Recommended)

The easiest way to get started:

```bash
# Clone repository
git clone https://github.com/wafy80/unified-iptv-acestream.git
cd unified-iptv-acestream

# Install dependencies
pip install -r requirements.txt

# Run interactive setup wizard
python3 setup_wizard.py
```

The wizard will guide you through:
1. **Server Configuration**: Host, port, timezone
2. **AceStream**: Engine host/port, timeout and streaming parameters
3. **Scraper**: M3U playlist URLs and update interval
4. **EPG**: Electronic Program Guide sources
5. **Database**: SQLite or other database configuration
6. **Admin**: Username and password (change the default!)
7. **Security**: Automatic secret key generation

### Method 2: Docker (Production)

```bash
# Clone repository
git clone https://github.com/wafy80/unified-iptv-acestream.git
cd unified-iptv-acestream

# Create configuration
cp .env.example .env
nano .env  # Edit configuration

# Start with Docker Compose
docker-compose up -d
```

### Method 3: Manual Installation

```bash
# Clone and setup
git clone https://github.com/wafy80/unified-iptv-acestream.git
cd unified-iptv-acestream

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure manually
cp .env.example .env
nano .env  # Edit configuration

# Initialize database
python3 setup.py

# Start
python main.py
```

## ⚙️ Configuration

### Environment Variables

The `.env` file contains all configurations (26 variables):

#### Server
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=58055
SERVER_TIMEZONE=Europe/Rome
SERVER_DEBUG=false
```

#### AceStream Engine
```env
ACESTREAM_ENABLED=true
ACESTREAM_ENGINE_HOST=localhost
ACESTREAM_ENGINE_PORT=6878
ACESTREAM_TIMEOUT=15
```

#### AceStream Streaming (Advanced)
```env
ACESTREAM_STREAMING_HOST=127.0.0.1
ACESTREAM_STREAMING_PORT=8001
ACESTREAM_CHUNK_SIZE=8192
ACESTREAM_EMPTY_TIMEOUT=60.0
ACESTREAM_NO_RESPONSE_TIMEOUT=10.0
```

#### Scraper
```env
SCRAPER_URLS=http://example.com/playlist.m3u
SCRAPER_UPDATE_INTERVAL=3600
```

#### EPG
```env
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz
EPG_UPDATE_INTERVAL=86400
EPG_CACHE_FILE=data/epg.xml
```

#### Database
```env
DATABASE_URL=sqlite:///data/unified-iptv.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

#### Admin & Security
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### Docker Configuration

For custom configuration, create a `.env` file:

```bash
cp .env.example .env
nano .env
```

Then modify `docker-compose.yml` to use the `.env` file:

```yaml
services:
  unified-iptv:
    env_file:
      - .env
```

**Important**: Never commit the `.env` file with real credentials!

## 🔒 Security

### Protected Dashboard
- Dashboard accessible only from localhost by default
- HTTP Basic authentication required
- Remote access via SSH tunnel or reverse proxy

### Remote Dashboard Access

#### Via SSH Tunnel
```bash
ssh -L 8000:localhost:58055 user@your-server
# Then open: http://localhost:8000
```

#### Via Reverse Proxy (nginx)
```nginx
server {
    listen 443 ssl;
    server_name dashboard.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:58055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # HTTP Basic Auth
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

### Production Security Checklist

- [ ] Change `ADMIN_PASSWORD` (minimum 12 characters)
- [ ] Generate new `SECRET_KEY` (64+ characters)
- [ ] Dashboard only on localhost or behind reverse proxy
- [ ] Enable HTTPS for external connections
- [ ] Use firewall to limit port access
- [ ] Regular database backups
- [ ] Monitor logs for suspicious access

## 🔌 API Endpoints

### Xtream Codes API (Compatible with all IPTV players)

```
# Authentication and info
GET  /player_api.php?username={user}&password={pass}

# Live Streams
GET  /player_api.php?username={user}&password={pass}&action=get_live_categories
GET  /player_api.php?username={user}&password={pass}&action=get_live_streams
GET  /player_api.php?username={user}&password={pass}&action=get_live_streams&category_id={id}

# EPG
GET  /player_api.php?username={user}&password={pass}&action=get_simple_data_table&stream_id={id}
GET  /player_api.php?username={user}&password={pass}&action=get_short_epg&stream_id={id}&limit={num}

# Stream URL format
http://server:port/{username}/{password}/{stream_id}
```

### Dashboard API

```
# Channels
GET    /api/channels              # List channels
POST   /api/channels              # Add channel
PUT    /api/channels/{id}         # Update channel
DELETE /api/channels/{id}         # Delete channel
GET    /api/channels/{id}/status  # Channel status

# Scraping
GET    /api/scraper/urls          # List scraping URLs
POST   /api/scraper/urls          # Add URL
POST   /api/scraper/refresh       # Force refresh
GET    /api/scraper/status        # Scraper status

# Users
GET    /api/users                 # List users
POST   /api/users                 # Create user
PUT    /api/users/{id}            # Update user
DELETE /api/users/{id}            # Delete user
```

### M3U Playlist

```
# Complete playlist
GET  /playlist.m3u

# Playlist with forced refresh
GET  /playlist.m3u?refresh=true

# Filtered playlist by category
GET  /playlist.m3u?category={name}

# Playlist with search
GET  /playlist.m3u?search={query}
```

## 📺 Usage with IPTV Players

### IPTV Smarters Pro

1. Select "Login with Xtream Codes API"
2. Enter:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: admin (or configured)
   - **Password**: (configured password)
3. Click "Add User"

### Perfect Player

1. Go to Settings → General → Playlist
2. Select "Playlist type: XTREAM CODES"
3. Enter:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: admin
   - **Password**: (configured password)

### TiviMate

1. Add Playlist
2. Select "Xtream Codes API"
3. Enter:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: admin
   - **Password**: (configured password)

### VLC / Kodi (M3U)

```bash
http://your-server-ip:58055/get.php?username=admin&password=yourpass&type=m3u_plus
```

## 🎯 Quick Start Examples

### Example 1: Fast Setup with Wizard

```bash
git clone https://github.com/wafy80/unified-iptv-acestream.git
cd unified-iptv-acestream
pip3 install -r requirements.txt
python3 setup_wizard.py
# Follow the wizard (press Enter for defaults)
python3 main.py
```

### Example 2: Quick Docker Compose

```bash
git clone https://github.com/wafy80/unified-iptv-acestream.git
cd unified-iptv-acestream

# Only modify password in docker-compose.yml
nano docker-compose.yml

docker-compose up -d

# Check logs
docker-compose logs -f
```

### Example 3: Custom Configuration

```bash
cp .env.example .env
nano .env  # Modify your settings

python3 setup.py  # Initialize DB
python3 main.py   # Start
```

## 🔧 Management and Maintenance

### Docker Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose stop

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Specific logs
docker-compose logs -f unified-iptv

# Update
git pull
docker-compose build
docker-compose up -d

# Cleanup
docker-compose down
docker system prune -a
```

### Backup and Restore

```bash
# Backup database
cp data/unified-iptv.db data/unified-iptv.db.backup

# Complete backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/ .env

# Restore
tar -xzf backup-20240116.tar.gz
```

### Monitoring

```bash
# Health check
curl http://localhost:58055/health

# AceProxy stats
curl http://localhost:58055/api/aceproxy/stats

# Scraper status
curl http://localhost:58055/api/scraper/status

# EPG status
curl http://localhost:58055/api/epg/status
```

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines first.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

This project combines and extends:
- [acestream-scraper](https://github.com/acestream/acestream-scraper) - Channel scraping
- [pyacexy](https://github.com/pyacexy/pyacexy) - AceStream proxy
- [xtream-api](https://github.com/xtream-codes/xtream-api) - Xtream Codes API implementation

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This software is for educational purposes only. Ensure you have the right to stream content and comply with local laws.
