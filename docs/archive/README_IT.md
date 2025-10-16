# 🎬 Unified IPTV AceStream Platform

## 🎯 Panoramica

Piattaforma IPTV completa che unifica **acestream-scraper**, **pyacexy** e **xtream_api** in un'unica soluzione moderna e scalabile.

## ✨ Caratteristiche Principali

### 📺 Gestione Canali
- ✅ Scraping automatico da fonti multiple (JSON, M3U, HTML)
- ✅ Database relazionale con SQLAlchemy
- ✅ Categorie e metadati completi
- ✅ Channel status monitoring
- ✅ Auto-rescraping configurabile

### 🔌 API Xtream Codes
- ✅ Compatibilità totale con IPTV Smarters, Perfect Player, TiviMate
- ✅ Gestione utenti e autenticazione
- ✅ Multi-connessione per utente
- ✅ Sistema trial/premium
- ✅ Playlist M3U dinamiche

### 🎥 AceStream Proxy
- ✅ Multiplexing intelligente degli stream
- ✅ Buffer condiviso tra client
- ✅ Gestione automatica PID
- ✅ Cleanup automatico risorse
- ✅ Statistiche in tempo reale

### 📅 EPG (Guida Programmi)
- ✅ Aggregazione da fonti multiple
- ✅ Formato XMLTV standard
- ✅ Aggiornamento automatico
- ✅ Matching intelligente canali
- ✅ API EPG completa

## 🚀 Quick Start

### Setup in 30 Secondi

```bash
cd unified-iptv-acestream
python3 setup.py  # Wizard interattivo
python main.py    # Avvia piattaforma
```

### Docker (Consigliato)

```bash
docker-compose up -d
```

Visita: `http://localhost:58055/health`

## 📱 Configurazione Player

### IPTV Smarters
```
Server: http://TUO-IP:58055
Username: admin
Password: (configurata)
```

### Perfect Player / TiviMate
```
Type: Xtream Codes
Server: http://TUO-IP:58055
Username: admin
Password: (configurata)
```

### VLC / Kodi
```
M3U: http://TUO-IP:58055/get.php?username=admin&password=PASSWORD
EPG: http://TUO-IP:58055/xmltv.php
```

## 📊 Statistiche Progetto

- **4,400+** righe di codice
- **14** file Python
- **8** modelli database
- **3** servizi core
- **20+** API endpoints
- **5** guide documentazione

## 🏗️ Architettura

```
┌─────────────────────────────────┐
│      Client IPTV (Player)       │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│    Xtream API + Auth           │
├─────────────────────────────────┤
│  Scraper │  AceProxy  │  EPG   │
├─────────────────────────────────┤
│    Database (SQLAlchemy)        │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│      AceStream Engine           │
└─────────────────────────────────┘
```

## 📁 Struttura Progetto

```
unified-iptv-acestream/
├── app/
│   ├── api/                    # API Endpoints
│   │   └── xtream.py          # Xtream Codes API
│   ├── models/                # Database Models
│   │   └── __init__.py        # User, Channel, EPG, etc.
│   ├── services/              # Business Logic
│   │   ├── aceproxy_service.py
│   │   ├── scraper_service.py
│   │   └── epg_service.py
│   ├── utils/                 # Utilities
│   │   └── auth.py           # Authentication
│   └── config.py             # Configuration
│
├── data/                      # Database & Cache
├── logs/                      # Application Logs
├── config/                    # Config Files
│
├── main.py                    # Entry Point
├── setup.py                   # Setup Wizard
├── requirements.txt           # Dependencies
├── Dockerfile                 # Docker Image
├── docker-compose.yml         # Docker Compose
│
└── docs/
    ├── README.md             # Overview
    ├── QUICK_START.md       # Quick Start (5 min)
    ├── MIGRATION.md         # Migration Guide
    ├── TECHNICAL.md         # Technical Docs
    └── EXAMPLES.md          # Practical Examples
```

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI** - Web framework moderno e veloce
- **SQLAlchemy 2.0** - ORM con type hints
- **aiohttp** - Async HTTP client/server
- **Pydantic** - Validazione dati

### Security
- **bcrypt** - Password hashing
- **python-jose** - JWT tokens
- **passlib** - Crypto utilities

### Data Processing
- **BeautifulSoup4** - HTML parsing
- **lxml** - XML processing
- **xmltodict** - EPG parsing

## 📖 Documentazione

| File | Descrizione |
|------|-------------|
| [README.md](README.md) | Documentazione completa |
| [QUICK_START.md](QUICK_START.md) | Guida rapida 5 minuti |
| [MIGRATION.md](MIGRATION.md) | Migrazione dai progetti originali |
| [TECHNICAL.md](TECHNICAL.md) | Documentazione tecnica |
| [EXAMPLES.md](EXAMPLES.md) | Esempi pratici |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Riepilogo progetto |

## 🎯 Casi d'Uso

### 1. IPTV Personale
```bash
# Setup base
python setup.py
python main.py

# Configura player con credenziali
# Guarda TV su qualsiasi dispositivo
```

### 2. Servizio Multi-Utente
```python
# Crea utenti con scadenze
create_user(db, "user1", "pass1", expiry_date=...)
create_user(db, "user2", "pass2", max_connections=3)
```

### 3. Aggregatore Canali
```bash
# Configura multiple fonti scraping
SCRAPER_URLS=url1,url2,url3
# Scraping automatico ogni 24h
```

### 4. EPG Provider
```bash
# Aggrega EPG da fonti multiple
EPG_SOURCES=source1,source2,source3
# Serve EPG via XMLTV
curl http://server/xmltv.php
```

## 🔐 Sicurezza

- ✅ Password con bcrypt hashing
- ✅ JWT tokens per sessioni
- ✅ User authentication per tutte le API
- ✅ Connection limits per utente
- ✅ CORS configurabile
- ⚠️ **In produzione: usa HTTPS con reverse proxy!**

## 📈 Performance

- **Stream Multiplexing**: Stesso stream condiviso tra N client
- **Database Pooling**: Connection pool configurabile
- **Async I/O**: Non-blocking operations
- **Smart Caching**: EPG e metadati cached
- **Auto-Cleanup**: Risorse liberate automaticamente

## 🐳 Deployment

### Docker Compose (Produzione)
```yaml
version: '3.8'
services:
  unified-iptv:
    image: unified-iptv:latest
    ports:
      - "58055:58055"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

### Reverse Proxy (nginx)
```nginx
server {
    listen 80;
    server_name iptv.example.com;
    
    location / {
        proxy_pass http://localhost:58055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Configurazione Avanzata

### Multi-Server Setup
```bash
# Server 1: Scraper + Database
ACESTREAM_ENABLED=false

# Server 2: AceStream + Proxy
SCRAPER_URLS=""
DATABASE_URL=postgresql://server1/db
```

### High Availability
```yaml
# Load balancer
services:
  iptv-1:
    image: unified-iptv:latest
    ...
  iptv-2:
    image: unified-iptv:latest
    ...
  nginx:
    image: nginx
    depends_on: [iptv-1, iptv-2]
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:58055/health
```

### Logs
```bash
tail -f logs/app.log
docker-compose logs -f
```

### Metrics (Future)
- Prometheus integration
- Grafana dashboards
- Alert manager

## 🤝 Contribuire

Contributi benvenuti! Il progetto combina:
- [acestream-scraper](https://github.com/Pipepito/acestream-scraper) - MIT License
- [pyacexy](https://github.com/Javinator9889/acexy) - GPL v3
- [xtream_api](https://github.com/Divarion-D/xtream_api) - License TBD

## 🆘 Supporto

- **Issues**: Apri una issue su GitHub
- **Logs**: Controlla `logs/app.log`
- **Health**: `curl http://localhost:58055/health`
- **Docs**: Leggi la documentazione completa

## 🎓 Tutorial Video (Future)

- [ ] Setup e Configurazione
- [ ] Configurazione Player IPTV
- [ ] Gestione Utenti
- [ ] Migrazione da altri sistemi
- [ ] Deployment in Produzione

## 🗺️ Roadmap

### v1.0 (Current)
- ✅ Core IPTV platform
- ✅ Xtream API complete
- ✅ AceStream proxy
- ✅ EPG support
- ✅ User management

### v1.1 (Next)
- [ ] Web Dashboard admin
- [ ] VOD support
- [ ] Series support
- [ ] Enhanced statistics

### v2.0 (Future)
- [ ] Multi-server clustering
- [ ] CDN integration
- [ ] Mobile apps
- [ ] Advanced analytics

## 📝 Changelog

### v1.0.0 (2024-10-10)
- 🎉 Initial release
- ✨ Unified platform combining 3 projects
- ✨ Complete Xtream Codes API
- ✨ AceStream proxy with multiplexing
- ✨ Auto-scraping from multiple sources
- ✨ EPG aggregation and serving
- ✨ User management system
- ✨ Docker support
- 📚 Comprehensive documentation

## 📄 Licenza

Progetto derivato da:
- acestream-scraper (MIT License)
- pyacexy (GPL v3)
- xtream_api (License TBD)

Verificare le licenze originali per compliance.

## 🌟 Features Highlights

### Per Utenti Finali
- 📱 Funziona con tutti i player IPTV popolari
- 🎬 EPG completo per sapere cosa c'è in TV
- 📡 Stream stabili e veloci con multiplexing
- 🌍 Accesso da qualsiasi dispositivo

### Per Amministratori
- ⚙️ Setup wizard interattivo
- 🔄 Aggiornamento automatico canali
- 👥 Gestione multi-utente semplice
- 📊 Monitoring e logs dettagliati
- 🐳 Deployment Docker one-click

### Per Sviluppatori
- 🏗️ Architettura moderna e modulare
- 📝 Codice ben documentato
- 🧪 Pronto per testing
- 🔌 API REST documentata
- 🚀 Facilmente estendibile

---

**Made with ❤️ combining the best of acestream-scraper, pyacexy, and xtream_api**

**Buon streaming! 📺**
