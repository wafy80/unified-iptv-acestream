# Guida Rapida - Unified IPTV AceStream Platform

## 🚀 Setup Rapido (5 minuti)

### Opzione 1: Docker Compose (Raccomandato)

```bash
# 1. Clona/copia il progetto
cd unified-iptv-acestream

# 2. Copia e configura il file .env
cp .env.example .env
nano .env  # Modifica le configurazioni

# 3. Avvia con Docker Compose
docker-compose up -d

# 4. Verifica i logs
docker-compose logs -f
```

### Opzione 2: Installazione Manuale

```bash
# 1. Crea virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Configura
cp .env.example .env
nano .env  # Modifica le configurazioni

# 4. Crea le directory necessarie
mkdir -p data logs config

# 5. Avvia l'applicazione
python main.py
```

## ⚙️ Configurazione Iniziale

### 1. Admin User

Modifica `.env`:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=TuaPasswordSicura123!
```

### 2. Aggiungi Fonti Scraping

Aggiungi URL da cui scaricare canali. Puoi farlo in due modi:

**A. Via Environment Variables:**
```
SCRAPER_URLS=https://example.com/channels.json,https://another.com/acestream.m3u
```

**B. Via Database (dopo il primo avvio):**
```sql
INSERT INTO scraper_urls (url, is_enabled, scraper_type) 
VALUES ('https://example.com/channels.json', 1, 'auto');
```

### 3. Configura EPG

Aggiungi fonti EPG in `.env`:
```
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz
```

### 4. Configura AceStream Engine

Se hai un AceStream Engine esterno:
```
ACESTREAM_ENGINE_HOST=192.168.1.100
ACESTREAM_ENGINE_PORT=6878
```

## 📱 Utilizzo con Player IPTV

### IPTV Smarters Pro

1. Apri IPTV Smarters
2. Seleziona "Login with Xtream Codes API"
3. Inserisci:
   - **Server**: `http://TUO-SERVER-IP:58055`
   - **Username**: `admin` (o quello configurato)
   - **Password**: la tua password
4. Clicca "Add User"

### Perfect Player

1. Apri Perfect Player
2. Settings → General → Playlist
3. Tipo: **XTREAM CODES**
4. Inserisci:
   - Server: `http://TUO-SERVER-IP:58055`
   - Username e Password

### VLC

1. Media → Open Network Stream
2. URL: `http://TUO-SERVER-IP:58055/get.php?username=admin&password=TUA_PASSWORD`

## 🔧 Operazioni Comuni

### Aggiungi Utente Manualmente

```python
# Via Python shell
from app.utils.auth import create_user, SessionLocal

db = SessionLocal()
create_user(
    db,
    username="utente1",
    password="password123",
    is_trial=False,
    max_connections=2,
    expiry_date=None  # Nessuna scadenza
)
db.close()
```

### Forza Refresh Canali

```bash
# Via API
curl -X POST http://localhost:58055/api/scraper/refresh

# O riavvia il servizio
docker-compose restart
```

### Controlla Stato

```bash
# Health check
curl http://localhost:58055/health

# Lista canali (via Xtream API)
curl "http://localhost:58055/player_api.php?username=admin&password=TUA_PASSWORD&action=get_live_streams"
```

## 🐛 Troubleshooting

### Problema: Canali non appaiono

1. Verifica che le URL di scraping siano corrette
2. Controlla i logs: `docker-compose logs -f` o `tail -f logs/app.log`
3. Forza un refresh manuale

### Problema: Stream non parte

1. Verifica che AceStream Engine sia in esecuzione
2. Controlla la configurazione di ACESTREAM_ENGINE_HOST
3. Testa un canale manualmente: `curl http://localhost:8080/ace/getstream?id=ACESTREAM_ID`

### Problema: EPG non si carica

1. Verifica le URL EPG in `.env`
2. Controlla che le fonti EPG siano accessibili
3. Verifica il formato (gzipped o plain XML)

## 📊 Monitoraggio

### Logs in tempo reale
```bash
docker-compose logs -f unified-iptv
```

### Database SQLite
```bash
sqlite3 data/unified-iptv.db
.tables
SELECT * FROM channels LIMIT 10;
```

### API Health
```bash
curl http://localhost:58055/health | jq
```

## 🔐 Sicurezza in Produzione

1. **Cambia il SECRET_KEY** in `.env`
2. **Usa password forti** per admin
3. **Configura HTTPS** con reverse proxy (nginx/Traefik)
4. **Limita l'accesso** con firewall
5. **Backup regolare** del database

## 📝 Endpoints Principali

| Endpoint | Descrizione |
|----------|-------------|
| `/player_api.php` | Xtream Codes API principale |
| `/get.php` | Playlist M3U |
| `/xmltv.php` | EPG in formato XMLTV |
| `/{user}/{pass}/{id}` | Stream singolo canale |
| `/health` | Health check |
| `/docs` | Documentazione API |

## 🆘 Supporto

- Logs: `logs/app.log`
- Health: `http://localhost:58055/health`
- API Docs: `http://localhost:58055/docs`

## 📦 Struttura Progetto

```
unified-iptv-acestream/
├── app/
│   ├── api/          # API endpoints
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   ├── utils/        # Utilities
│   └── config.py     # Configuration
├── data/             # Database e cache
├── logs/             # Log files
├── config/           # Config files
├── main.py           # Entry point
├── requirements.txt  # Dipendenze Python
├── Dockerfile        # Docker image
└── docker-compose.yml # Docker orchestration
```
