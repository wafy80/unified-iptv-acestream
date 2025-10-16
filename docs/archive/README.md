# Unified IPTV AceStream Platform

Piattaforma IPTV unificata che combina il meglio di acestream-scraper, pyacexy e xtream_api in un'unica soluzione completa.

## 🚀 Caratteristiche

### Core Features
- **Scraping Automatico**: Raccolta automatica canali AceStream da multiple fonti
- **Xtream Codes API**: Compatibilità completa con IPTV Smarters, Perfect Player, TiviMate
- **Proxy AceStream Integrato**: Gestione intelligente stream con multiplexing
- **EPG Completo**: Electronic Program Guide con aggregazione da fonti multiple
- **Gestione Utenti**: Sistema completo autenticazione e autorizzazione
- **Dashboard Web**: Interfaccia amministrazione moderna e intuitiva

### Advanced Features
- Acestream Engine integrato con Acexy proxy
- Supporto ZeroNet per fonti decentralizzate
- Cloudflare WARP per geo-unblocking
- Channel status monitoring in tempo reale
- Auto-rescraping configurabile
- Database SQLAlchemy con migrations
- Health checking e monitoring
- API REST documentata (OpenAPI/Swagger)

## 📋 Architettura

```
┌─────────────────────────────────────────────────────────┐
│              Client IPTV (Player)                       │
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

## 🛠️ Installazione

### Docker (Raccomandato)

```bash
docker-compose up -d
```

### Docker Compose Configurazione

```yaml
version: '3.8'

services:
  unified-iptv:
    image: unified-iptv-acestream:latest
    container_name: unified-iptv
    environment:
      - TZ=Europe/Rome
      - ENABLE_ACESTREAM=true
      - ENABLE_WARP=false
      - SERVER_PORT=8000
      - XTREAM_PORT=58055
    ports:
      - "8000:8000"      # Web Dashboard
      - "58055:58055"    # Xtream API
      - "8080:8080"      # AceProxy
      - "6878:6878"      # AceStream Engine
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
```

### Installazione Manuale

```bash
# Clone e setup
git clone <repository-url>
cd unified-iptv-acestream

# Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura
cp config/config.example.json config/config.json
# Edita config/config.json

# Avvia
python main.py
```

## ⚙️ Configurazione

### Setup Wizard Interattivo

Al primo avvio, il setup wizard ti guiderà nella configurazione:

1. **Credenziali Admin**: Username e password amministratore
2. **Xtream API**: Configurazione endpoint e porta
3. **Fonti Scraping**: URL da cui raccogliere canali
4. **AceStream Engine**: Configurazione engine locale o remoto
5. **EPG Sources**: Fonti Electronic Program Guide

### Configurazione Manuale

Edita `config/config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "dashboard_port": 8000,
    "xtream_port": 58055,
    "timezone": "Europe/Rome"
  },
  "acestream": {
    "enabled": true,
    "engine_host": "localhost",
    "engine_port": 6878,
    "proxy_port": 8080,
    "buffer_size": "5MiB"
  },
  "scraper": {
    "urls": [
      "https://example.com/acestream-channels"
    ],
    "rescrape_interval": 86400,
    "base_url": "http://localhost:8080/ace/getstream?id="
  },
  "epg": {
    "sources": [
      "https://iptvx.one/EPG_NOARCH",
      "https://epg.pw/xmltv/epg.xml.gz"
    ],
    "update_interval": 86400
  },
  "admin": {
    "username": "admin",
    "password": "changeme"
  }
}
```

## 🔌 API Endpoints

### Xtream Codes API (Compatibile con tutti i player IPTV)

```
# Autenticazione e info
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
GET    /api/channels              # Lista canali
POST   /api/channels              # Aggiungi canale
PUT    /api/channels/{id}         # Aggiorna canale
DELETE /api/channels/{id}         # Elimina canale
GET    /api/channels/{id}/status  # Status canale

# Scraping
GET    /api/scraper/urls          # Lista URL scraping
POST   /api/scraper/urls          # Aggiungi URL
POST   /api/scraper/refresh       # Forza refresh
GET    /api/scraper/status        # Status scraper

# Users
GET    /api/users                 # Lista utenti
POST   /api/users                 # Crea utente
PUT    /api/users/{id}            # Aggiorna utente
DELETE /api/users/{id}            # Elimina utente
```

### Playlist M3U

```
# Playlist completa
GET  /playlist.m3u

# Playlist con refresh forzato
GET  /playlist.m3u?refresh=true

# Playlist filtrata per categoria
GET  /playlist.m3u?category={name}

# Playlist con ricerca
GET  /playlist.m3u?search={query}
```

## 📺 Utilizzo con Player IPTV

### IPTV Smarters Pro

1. Seleziona "Login with Xtream Codes API"
2. Inserisci:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: tuo username
   - **Password**: tua password
3. Clicca "Add User"

### Perfect Player

1. Vai in Settings → General → Playlist
2. Seleziona "Playlist type: XTREAM CODES"
3. Inserisci:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: tuo username  
   - **Password**: tua password

### VLC / Kodi (M3U)

1. Aggiungi sorgente rete
2. URL: `http://your-server-ip:8000/playlist.m3u`

### TiviMate

1. Aggiungi Playlist
2. Seleziona "Xtream Codes API"
3. Inserisci credenziali server

## 🔧 Features Avanzate

### Cloudflare WARP (Geo-unblocking)

```bash
docker run -d \
  --cap-add NET_ADMIN \
  --cap-add SYS_ADMIN \
  -e ENABLE_WARP=true \
  unified-iptv-acestream
```

### ZeroNet Sources

```json
{
  "scraper": {
    "urls": [
      "http://127.0.0.1:43110/your-zeronet-site",
      "https://regular-site.com/channels"
    ],
    "enable_zeronet": true
  }
}
```

### Multiple User Management

```python
# Via API
POST /api/users
{
  "username": "user1",
  "password": "pass123",
  "max_connections": 2,
  "is_trial": false,
  "expiry_date": "2024-12-31"
}
```

## 📊 Monitoring e Logs

### Health Check

```bash
curl http://localhost:8000/health
```

### Dashboard Web

Accedi a `http://localhost:8000` per:
- Statistiche canali (totali, online, offline)
- Gestione utenti
- Configurazione scraper
- Monitoring stream in tempo reale
- Log viewer

### Logs

```bash
# Docker
docker logs unified-iptv -f

# Manuale
tail -f logs/app.log
```

## 🔒 Sicurezza

- Autenticazione richiesta per Xtream API
- Supporto HTTPS con certificati SSL
- Rate limiting per API
- Protezione CSRF per dashboard
- Password hashing con bcrypt
- Token session con scadenza

## 🚀 Performance

- Database connection pooling
- Async I/O con aiohttp
- Stream buffering intelligente
- Caching EPG e metadati
- Lazy loading canali
- Multi-client stream sharing

## 🤝 Contributi

Basato su:
- [acestream-scraper](https://github.com/Pipepito/acestream-scraper) - Scraping e playlist
- [pyacexy](https://github.com/Javinator9889/acexy) - Proxy AceStream
- [xtream_api](https://github.com/Divarion-D/xtream_api) - Xtream Codes API

## 📄 Licenza

MIT License - vedi LICENSE file

## 🆘 Supporto

- Documentation: `/docs`
- Issues: GitHub Issues
- API Docs: `http://localhost:8000/api/docs`
