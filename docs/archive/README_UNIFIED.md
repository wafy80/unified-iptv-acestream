# Unified IPTV AceStream Platform

Una piattaforma IPTV completa basata su AceStream, che integra il meglio di:
- **pyacexy**: Proxy HTTP per AceStream con multiplexing
- **xtream_api**: Parser M3U/EPG e API Xtream Codes
- **acestream-scraper**: Interfaccia web e gestione canali

## Caratteristiche

### 🚀 Servizi Integrati
- **AceProxy**: Proxy HTTP per stream AceStream con multiplexing client
- **Xtream API**: API compatibile con Xtream Codes per player IPTV
- **Scraper**: Scraping automatico di canali AceStream
- **EPG Service**: Gestione e aggregazione Guide Elettroniche Programmi
- **Web Dashboard**: Interfaccia web moderna per gestione completa

### 🎯 Endpoint Principali
- `/` - Informazioni API
- `/ace/getstream?id=ACESTREAM_ID` - Proxy AceStream (compatibile pyacexy)
- `/ace/status` - Stato stream attivi
- `/player_api.php` - API Xtream Codes
- `/get.php` - Playlist M3U
- `/xmltv.php` - EPG in formato XMLTV
- API Dashboard e gestione

### 🔧 Caratteristiche Tecniche
- **Una sola porta**: Tutti i servizi su porta singola (default: 8080)
- **Multiplexing**: Un stream AceStream serve multipli client
- **Database**: SQLite per gestione canali e utenti
- **Async**: Architettura asincrona con FastAPI
- **EPG**: Supporto multi-sorgente EPG con caching

## Installazione

### Requisiti
- Python 3.8+
- AceStream Engine (in esecuzione su localhost:6878 o remoto)

### Setup

1. Clona il repository:
```bash
cd /home/wafy/src/acextream/unified-iptv-acestream
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura l'ambiente:
```bash
cp .env.example .env
nano .env  # Modifica le impostazioni
```

4. Avvia l'applicazione:
```bash
python3 main.py
```

L'applicazione sarà disponibile su `http://localhost:8080`

## Configurazione

### Variabili d'Ambiente (.env)

```bash
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# AceStream  
ACESTREAM_ENGINE_HOST=localhost
ACESTREAM_ENGINE_PORT=6878

# Scraper
SCRAPER_URLS=http://example.com/acestream-list.json

# EPG
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

## Utilizzo

### Player IPTV (Xtream API)

Configura il tuo player IPTV con:
- **Server**: `http://your-server:8080`
- **Username**: `admin` (o utente creato)
- **Password**: `changeme` (o password impostata)
- **Port**: lascia vuoto (già incluso in server URL)

### Playlist M3U

Scarica la playlist M3U da:
```
http://your-server:8080/get.php?username=admin&password=changeme
```

### EPG

URL EPG per player:
```
http://your-server:8080/xmltv.php
```

### AceStream Diretto

Stream un contenuto AceStream:
```
http://your-server:8080/ace/getstream?id=ACESTREAM_CONTENT_ID
```

## Dashboard Web

Accedi alla dashboard su `http://your-server:8080/` per:
- Visualizzare statistiche
- Gestire canali
- Configurare scraper
- Gestire utenti
- Monitorare stream attivi

## API

### Documenti API Interattivi
```
http://your-server:8080/docs
```

### Endpoint Principali

#### Health Check
```bash
GET /health
GET /api/health
```

#### AceProxy
```bash
# Stream AceStream
GET /ace/getstream?id=CONTENT_ID

# Stato proxy
GET /ace/status

# Lista stream attivi
GET /streams

# Statistiche
GET /stats
```

#### Xtream API
```bash
# Player API
GET /player_api.php?username=USER&password=PASS

# Playlist M3U
GET /get.php?username=USER&password=PASS

# EPG
GET /xmltv.php
```

## Architettura

### Componenti

```
unified-iptv-acestream/
├── app/
│   ├── api/              # Endpoint FastAPI
│   │   ├── aceproxy.py   # Endpoint pyacexy-compatibili
│   │   ├── xtream.py     # API Xtream Codes
│   │   ├── dashboard.py  # Web dashboard
│   │   └── api_endpoints.py
│   ├── services/         # Servizi backend
│   │   ├── aceproxy_service.py
│   │   ├── scraper_service.py
│   │   └── epg_service.py
│   ├── models/           # Database models
│   ├── utils/            # Utility functions
│   ├── templates/        # Template HTML
│   └── static/           # File statici (CSS/JS)
├── data/                 # Database e cache
├── logs/                 # Log applicazione
├── main.py              # Entry point
└── requirements.txt     # Dipendenze Python
```

### Flusso Stream

```
Player IPTV
    ↓
Xtream API (/player_api.php)
    ↓
Database Canali
    ↓
AceProxy (/ace/getstream?id=XXX)
    ↓
AceStream Engine (localhost:6878)
    ↓
P2P Network
```

## Integrazione Progetti

### Da pyacexy
- ✅ Endpoint `/ace/getstream` compatibili
- ✅ Endpoint `/ace/status`
- ✅ Multiplexing stream con gestione client multipli
- ✅ Buffer management e timeout handling

### Da xtream_api
- ✅ Parser M3U corretto e testato
- ✅ API Xtream Codes completa
- ✅ Gestione EPG multi-sorgente
- ✅ Database structure

### Da acestream-scraper
- ✅ Web dashboard moderna
- ✅ Gestione canali via UI
- ✅ Scraping automatico URL
- ✅ Template HTML Bootstrap 5

## Problemi Risolti

1. ✅ **Porte Unificate**: Tutto su una porta invece di 2-3 diverse
2. ✅ **Endpoint AceProxy**: Ora compatibili con pyacexy (`/ace/getstream`)
3. ✅ **Parser M3U**: Sostituito con quello testato di xtream_api
4. ✅ **Directory mancanti**: `app/static` e `app/templates` create
5. ✅ **Template HTML**: Dashboard creata ispirata ad acestream-scraper

## Troubleshooting

### Porta già in uso
```bash
# Cambia porta in .env
SERVER_PORT=8081
```

### AceStream Engine non raggiungibile
```bash
# Verifica AceStream Engine
telnet localhost 6878

# Configura host/port in .env
ACESTREAM_ENGINE_HOST=192.168.1.100
ACESTREAM_ENGINE_PORT=6878
```

### Database errors
```bash
# Rimuovi e ricrea database
rm data/unified-iptv.db
python3 main.py  # Verrà ricreato automaticamente
```

## Sviluppo

### Esegui in modalità debug
```bash
SERVER_DEBUG=true python3 main.py
```

### Esegui test
```bash
pytest tests/
```

## Licenza

Questo progetto integra codice da:
- pyacexy (MIT License)
- xtream_api 
- acestream-scraper

## Credits

Creato integrando il meglio di:
- [pyacexy](https://github.com/romanouille/pyacexy) - AceStream HTTP Proxy
- xtream_api - Xtream Codes API implementation
- acestream-scraper - Web Dashboard e UI

## Supporto

Per problemi o domande, apri una issue su GitHub.
