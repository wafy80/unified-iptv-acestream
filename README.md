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

### Metodo 1: Setup Wizard Interattivo (Raccomandato)

Il modo più semplice per iniziare:

```bash
# Clone repository
git clone <repository-url>
cd unified-iptv-acestream

# Installa dipendenze
pip install -r requirements.txt

# Avvia il setup wizard interattivo
python3 setup_wizard.py
```

Il wizard ti guiderà attraverso:
1. **Configurazione Server**: Host, porta, timezone
2. **AceStream**: Engine host/porta, timeout e parametri streaming
3. **Scraper**: URL playlist M3U e intervallo di aggiornamento
4. **EPG**: Fonti Electronic Program Guide
5. **Database**: Configurazione SQLite o altro
6. **Admin**: Username e password (cambia il default!)
7. **Security**: Generazione automatica chiave segreta

### Metodo 2: Docker (Produzione)

```bash
# Crea configurazione
cp .env.example .env
nano .env  # Modifica configurazione

# Avvia con Docker Compose
docker-compose up -d
```

### Metodo 3: Installazione Manuale

```bash
# Clone e setup
git clone <repository-url>
cd unified-iptv-acestream

# Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura manualmente
cp .env.example .env
nano .env  # Edita configurazione

# Inizializza database
python3 setup.py

# Avvia
python main.py
```

## ⚙️ Configurazione

### Variabili d'Ambiente

Il file `.env` contiene tutte le configurazioni (26 variabili):

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

#### AceStream Streaming (Avanzato)
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

### Configurazione Docker

Per configurazione personalizzata, crea un file `.env`:

```bash
cp .env.example .env
nano .env
```

Poi modifica `docker-compose.yml` per usare il file `.env`:

```yaml
services:
  unified-iptv:
    env_file:
      - .env
```

**Importante**: Non commitare mai il file `.env` con credenziali reali!

## 🔒 Sicurezza

### Dashboard Protetta
- Dashboard accessibile solo da localhost per default
- Autenticazione HTTP Basic richiesta
- Accesso remoto via SSH tunnel o reverse proxy

### Accesso Remoto alla Dashboard

#### Via SSH Tunnel
```bash
ssh -L 8000:localhost:58055 user@your-server
# Poi apri: http://localhost:8000
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

### Checklist Sicurezza Produzione

- [ ] Cambia `ADMIN_PASSWORD` (minimo 12 caratteri)
- [ ] Genera nuovo `SECRET_KEY` (64+ caratteri)
- [ ] Dashboard solo su localhost o dietro reverse proxy
- [ ] Abilita HTTPS per connessioni esterne
- [ ] Usa firewall per limitare accesso porte
- [ ] Backup regolari database
- [ ] Monitora logs per accessi sospetti

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
   - **Username**: admin (o quello configurato)
   - **Password**: (quella configurata)
3. Clicca "Add User"

### Perfect Player

1. Vai in Settings → General → Playlist
2. Seleziona "Playlist type: XTREAM CODES"
3. Inserisci:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: admin
   - **Password**: (quella configurata)

### TiviMate

1. Aggiungi Playlist
2. Seleziona "Xtream Codes API"
3. Inserisci:
   - **Server**: `http://your-server-ip:58055`
   - **Username**: admin
   - **Password**: (quella configurata)

### VLC / Kodi (M3U)

```bash
http://your-server-ip:58055/get.php?username=admin&password=yourpass&type=m3u_plus
```

## 🎯 Quick Start Esempi

### Esempio 1: Setup Veloce con Wizard

```bash
git clone <repository-url>
cd unified-iptv-acestream
pip3 install -r requirements.txt
python3 setup_wizard.py
# Segui il wizard (premi Enter per defaults)
python3 main.py
```

### Esempio 2: Docker Compose Rapido

```bash
git clone <repository-url>
cd unified-iptv-acestream

# Modifica solo password in docker-compose.yml
nano docker-compose.yml

docker-compose up -d

# Check logs
docker-compose logs -f
```

### Esempio 3: Configurazione Custom

```bash
cp .env.example .env
nano .env  # Modifica le tue impostazioni

python3 setup.py  # Inizializza DB
python3 main.py   # Avvia
```

## 🔧 Gestione e Manutenzione

### Docker Commands

```bash
# Avvia
docker-compose up -d

# Stop
docker-compose stop

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Logs specifici
docker-compose logs -f unified-iptv

# Update
git pull
docker-compose build
docker-compose up -d

# Cleanup
docker-compose down
docker system prune -a
```

### Backup e Restore

```bash
# Backup database
cp data/unified-iptv.db data/unified-iptv.db.backup

# Backup completo
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/ .env

# Restore
tar -xzf backup-20240116.tar.gz
```

### Monitoring

```bash
# Health check
curl http://localhost:58055/health

# Stats AceProxy
curl http://localhost:58055/api/aceproxy/stats

# Scraper status
curl http://localhost:58055/api/scraper/status

# EPG status
curl http://localhost:58055/api/epg/status
```
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
