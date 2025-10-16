# Esempi Pratici di Utilizzo

Questa guida contiene esempi pratici per utilizzare la piattaforma IPTV unificata.

## 📋 Indice

1. [Setup Iniziale](#setup-iniziale)
2. [Gestione Utenti](#gestione-utenti)
3. [Configurazione Canali](#configurazione-canali)
4. [EPG Management](#epg-management)
5. [Player IPTV](#player-iptv)
6. [API Usage](#api-usage)
7. [Troubleshooting](#troubleshooting)

## Setup Iniziale

### Quick Start con Wizard
```bash
cd unified-iptv-acestream
python3 setup.py
```

Il wizard chiederà:
- Credenziali admin
- Configurazione server
- URL scraping
- Fonti EPG

### Setup Manuale

```bash
# 1. Copia configurazione
cp .env.example .env

# 2. Edita .env
nano .env

# Configurazioni minime richieste:
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password_sicura_123
SERVER_XTREAM_PORT=58055
ACESTREAM_ENGINE_HOST=localhost
ACESTREAM_ENGINE_PORT=6878

# 3. Avvia
python main.py
```

## Gestione Utenti

### Creare Utente via Python

```python
# create_user.py
from app.utils.auth import create_user, SessionLocal
from datetime import datetime, timedelta

db = SessionLocal()

# Utente base
user = create_user(
    db,
    username="mario",
    password="rossi123",
    max_connections=1
)

# Utente premium con scadenza
premium_user = create_user(
    db,
    username="premium_user",
    password="secure_pass",
    max_connections=3,
    expiry_date=datetime.utcnow() + timedelta(days=365)
)

# Utente trial (7 giorni)
trial_user = create_user(
    db,
    username="trial_user",
    password="trial_pass",
    is_trial=True,
    max_connections=1,
    expiry_date=datetime.utcnow() + timedelta(days=7)
)

db.close()
print("Utenti creati con successo!")
```

### Gestione via SQL

```sql
-- Lista tutti gli utenti
SELECT id, username, is_admin, max_connections, expiry_date 
FROM users;

-- Crea nuovo utente (password già hashata)
INSERT INTO users (username, password_hash, is_admin, max_connections)
VALUES ('newuser', '$2b$12$...', 0, 2);

-- Aggiorna scadenza utente
UPDATE users 
SET expiry_date = datetime('now', '+30 days')
WHERE username = 'mario';

-- Disabilita utente
UPDATE users 
SET is_active = 0
WHERE username = 'mario';

-- Reset password (usa hash bcrypt)
UPDATE users 
SET password_hash = '$2b$12$...'
WHERE username = 'mario';
```

## Configurazione Canali

### Aggiungere URL Scraping

#### Via .env
```bash
SCRAPER_URLS=https://example.com/channels.json,https://site2.com/acestream.m3u
```

#### Via Database
```sql
INSERT INTO scraper_urls (url, is_enabled, scraper_type)
VALUES 
    ('https://example.com/channels.json', 1, 'json'),
    ('https://site2.com/channels.m3u', 1, 'm3u'),
    ('https://site3.com/channels.html', 1, 'html');
```

#### Via Python
```python
# add_scraper_url.py
from app.utils.auth import SessionLocal
from app.models import ScraperURL

db = SessionLocal()

urls = [
    "https://example.com/channels.json",
    "https://another-site.com/acestream.m3u",
    "https://third-site.com/index.html"
]

for url in urls:
    scraper_url = ScraperURL(
        url=url,
        is_enabled=True,
        scraper_type='auto'  # auto-detect format
    )
    db.add(scraper_url)

db.commit()
db.close()
print(f"Aggiunti {len(urls)} URL per scraping")
```

### Aggiungere Canali Manualmente

```python
# add_channel.py
from app.utils.auth import SessionLocal
from app.models import Channel, Category

db = SessionLocal()

# Crea categoria se non esiste
category = db.query(Category).filter(Category.name == "Sport").first()
if not category:
    category = Category(name="Sport", display_order=1)
    db.add(category)
    db.flush()

# Aggiungi canale
channel = Channel(
    name="Sky Sport 1",
    acestream_id="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
    logo_url="https://example.com/logo.png",
    epg_id="skysport1",
    category_id=category.id,
    is_active=True
)

db.add(channel)
db.commit()
db.close()

print(f"Canale '{channel.name}' aggiunto con successo!")
```

### Import Playlist M3U

```python
# import_m3u.py
import re
from app.utils.auth import SessionLocal
from app.models import Channel, Category

def import_m3u_file(filepath):
    db = SessionLocal()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current = {}
    imported = 0
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            # Parse metadata
            current = {}
            
            # Logo
            if 'tvg-logo=' in line:
                current['logo'] = re.search(r'tvg-logo="([^"]+)"', line).group(1)
            
            # EPG ID
            if 'tvg-id=' in line:
                current['epg_id'] = re.search(r'tvg-id="([^"]+)"', line).group(1)
            
            # Category
            if 'group-title=' in line:
                cat_name = re.search(r'group-title="([^"]+)"', line).group(1)
                cat = db.query(Category).filter(Category.name == cat_name).first()
                if not cat:
                    cat = Category(name=cat_name)
                    db.add(cat)
                    db.flush()
                current['category_id'] = cat.id
            
            # Name
            name_match = re.search(r',(.+)$', line)
            if name_match:
                current['name'] = name_match.group(1).strip()
        
        elif line and not line.startswith('#'):
            # Extract AceStream ID
            ace_match = re.search(r'([0-9a-fA-F]{40})', line)
            if ace_match and current.get('name'):
                ace_id = ace_match.group(1).lower()
                
                # Check if exists
                exists = db.query(Channel).filter(
                    Channel.acestream_id == ace_id
                ).first()
                
                if not exists:
                    channel = Channel(
                        acestream_id=ace_id,
                        name=current['name'],
                        logo_url=current.get('logo'),
                        epg_id=current.get('epg_id'),
                        category_id=current.get('category_id'),
                        is_active=True
                    )
                    db.add(channel)
                    imported += 1
            
            current = {}
    
    db.commit()
    db.close()
    
    return imported

# Uso
count = import_m3u_file('playlist.m3u')
print(f"Importati {count} canali!")
```

## EPG Management

### Configurare Fonti EPG

```bash
# .env
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz,http://custom-epg.com/epg.xml
EPG_UPDATE_INTERVAL=43200  # 12 ore in secondi
EPG_IS_GZIPPED=true
```

### Aggiungere Fonte EPG

```python
# add_epg_source.py
from app.utils.auth import SessionLocal
from app.models import EPGSource

db = SessionLocal()

sources = [
    ("https://iptvx.one/EPG_NOARCH", True),
    ("https://epg.pw/xmltv/epg.xml.gz", True),
    ("http://my-custom-epg.com/epg.xml", False)  # Non gzippato
]

for url, is_gzipped in sources:
    source = EPGSource(
        url=url,
        is_enabled=True,
        is_gzipped=is_gzipped
    )
    db.add(source)

db.commit()
db.close()
print("Fonti EPG aggiunte!")
```

### Match EPG con Canali

```python
# match_epg_ids.py
from app.utils.auth import SessionLocal
from app.models import Channel

db = SessionLocal()

# Auto-assign EPG IDs basati sul nome
channels = db.query(Channel).filter(Channel.epg_id == None).all()

for channel in channels:
    # Normalizza nome per EPG ID
    epg_id = channel.name.lower()
    epg_id = epg_id.replace(' ', '_')
    epg_id = epg_id.replace('sport', 'sports')
    
    channel.epg_id = epg_id
    print(f"{channel.name} -> {epg_id}")

db.commit()
db.close()
```

## Player IPTV

### IPTV Smarters Pro

**Configurazione:**
```
1. Apri IPTV Smarters
2. Tap su "Add User"
3. Seleziona "Login with Xtream Codes API"

Server URL: http://192.168.1.100:58055
Username: mario
Password: rossi123

4. Tap "Add User"
```

### Perfect Player (Android/Windows)

**Configurazione:**
```
1. Settings → General → Playlist
2. Playlist type: XTREAM CODES

Name: My IPTV
Server: http://192.168.1.100:58055
Username: mario
Password: rossi123

3. OK
```

### TiviMate (Android TV)

**Configurazione:**
```
1. Settings → Playlists
2. Add Playlist → Xtream Codes
3. Inserisci:
   - Name: My Server
   - Server: http://192.168.1.100:58055
   - Username: mario
   - Password: rossi123
4. Next → Done
```

### VLC Media Player

**M3U URL:**
```
http://192.168.1.100:58055/get.php?username=mario&password=rossi123&type=m3u_plus
```

**Uso:**
```
1. Media → Open Network Stream
2. Incolla URL
3. Play
```

### Kodi

**Configurazione PVR IPTV Simple Client:**
```
1. Add-ons → PVR IPTV Simple Client → Configure
2. General:
   - Location: Remote Path
   - M3U Play List URL: http://192.168.1.100:58055/get.php?username=mario&password=rossi123
3. EPG Settings:
   - XMLTV Location: Remote Path
   - XMLTV URL: http://192.168.1.100:58055/xmltv.php
4. OK → Enable
```

## API Usage

### Python Client Example

```python
# iptv_client.py
import requests

class IPTVClient:
    def __init__(self, server, username, password):
        self.base_url = f"{server}/player_api.php"
        self.username = username
        self.password = password
    
    def get_user_info(self):
        params = {
            'username': self.username,
            'password': self.password
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def get_live_streams(self, category_id=None):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_live_streams'
        }
        if category_id:
            params['category_id'] = category_id
        
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def get_categories(self):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_live_categories'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def get_epg(self, stream_id, limit=10):
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_short_epg',
            'stream_id': stream_id,
            'limit': limit
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def get_stream_url(self, stream_id, format='ts'):
        return f"{self.base_url.replace('/player_api.php', '')}/{self.username}/{self.password}/{stream_id}.{format}"

# Uso
client = IPTVClient('http://192.168.1.100:58055', 'mario', 'rossi123')

# Info utente
info = client.get_user_info()
print(f"User: {info['user_info']['username']}")
print(f"Status: {info['user_info']['status']}")

# Lista categorie
categories = client.get_categories()
for cat in categories:
    print(f"- {cat['category_name']} (ID: {cat['category_id']})")

# Lista canali
streams = client.get_live_streams()
for stream in streams[:5]:
    print(f"- {stream['name']} (ID: {stream['stream_id']})")

# EPG per un canale
epg = client.get_epg(stream_id=1)
print(f"EPG: {epg}")

# URL stream
stream_url = client.get_stream_url(1)
print(f"Stream URL: {stream_url}")
```

### cURL Examples

```bash
# User info
curl "http://192.168.1.100:58055/player_api.php?username=mario&password=rossi123"

# Categories
curl "http://192.168.1.100:58055/player_api.php?username=mario&password=rossi123&action=get_live_categories"

# Channels
curl "http://192.168.1.100:58055/player_api.php?username=mario&password=rossi123&action=get_live_streams"

# Channels by category
curl "http://192.168.1.100:58055/player_api.php?username=mario&password=rossi123&action=get_live_streams&category_id=1"

# EPG
curl "http://192.168.1.100:58055/player_api.php?username=mario&password=rossi123&action=get_short_epg&stream_id=1&limit=10"

# M3U Playlist
curl "http://192.168.1.100:58055/get.php?username=mario&password=rossi123" > playlist.m3u

# XMLTV EPG
curl "http://192.168.1.100:58055/xmltv.php?username=mario&password=rossi123" > epg.xml

# Stream (redirect to AceStream)
curl -L "http://192.168.1.100:58055/mario/rossi123/1.ts"
```

## Troubleshooting

### Verifica Servizio

```bash
# Health check
curl http://localhost:58055/health

# Risposta attesa:
{
  "status": "healthy",
  "services": {
    "aceproxy": true,
    "scraper": true,
    "epg": true
  }
}
```

### Test Connessione Database

```python
# test_db.py
from app.utils.auth import SessionLocal
from app.models import User, Channel

db = SessionLocal()

users = db.query(User).count()
channels = db.query(Channel).count()

print(f"Database OK: {users} users, {channels} channels")
db.close()
```

### Verifica AceStream Engine

```bash
# Test AceStream
curl "http://localhost:6878/webui/api/service?method=get_version"

# Test AceProxy
curl "http://localhost:8080/ace/status"
```

### Debug Logs

```bash
# Watch logs
tail -f logs/app.log

# Filter errors
grep ERROR logs/app.log

# Filter specific service
grep "scraper" logs/app.log
```

### Reset Database

```bash
# Backup
cp data/unified-iptv.db data/unified-iptv.db.backup

# Reset
rm data/unified-iptv.db

# Restart (recreates DB)
python main.py
```

## Script Utili

### Backup Database

```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 data/unified-iptv.db ".backup data/backup_${DATE}.db"
echo "Backup created: data/backup_${DATE}.db"
```

### Monitor Streams

```python
# monitor_streams.py
import asyncio
from app.services.aceproxy_service import AceProxyService

async def monitor():
    service = AceProxyService()
    await service.start()
    
    while True:
        streams = await service.get_all_streams()
        print(f"\n=== Active Streams: {len(streams)} ===")
        for stream in streams:
            print(f"- {stream['stream_id']}: {stream['clients']} clients")
        
        await asyncio.sleep(5)

asyncio.run(monitor())
```

### Cleanup Old EPG

```python
# cleanup_epg.py
from datetime import datetime, timedelta
from app.utils.auth import SessionLocal
from app.models import EPGProgram

db = SessionLocal()

# Remove programs older than 7 days
cutoff = datetime.utcnow() - timedelta(days=7)
deleted = db.query(EPGProgram).filter(
    EPGProgram.end_time < cutoff
).delete()

db.commit()
db.close()

print(f"Deleted {deleted} old EPG programs")
```
