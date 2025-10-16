# Guida Migrazione dai Progetti Esistenti

Questa guida spiega come migrare i tuoi dati dai progetti originali (acestream-scraper, xtream_api, pyacexy) alla piattaforma unificata.

## 📦 Cosa è stato integrato

### Da acestream-scraper
- ✅ Sistema di scraping canali da URL multiple
- ✅ Supporto JSON, HTML, M3U parsing
- ✅ Database SQLAlchemy con modelli completi
- ✅ Gestione categorie e metadati
- ✅ Auto-rescraping configurabile
- ✅ Channel status checking
- ✅ EPG integration

### Da pyacexy
- ✅ Proxy AceStream con multiplexing
- ✅ Gestione stream multipli
- ✅ Buffer intelligente
- ✅ PID management per client
- ✅ Stream statistics

### Da xtream_api
- ✅ API Xtream Codes completa
- ✅ Gestione utenti e autenticazione
- ✅ Compatibilità IPTV Smarters
- ✅ EPG in formato XMLTV
- ✅ M3U playlist generation

## 🔄 Migrazione Step-by-Step

### 1. Migrazione Database acestream-scraper

Se hai già un database di acestream-scraper:

```python
# migrate_from_scraper.py
import sqlite3
from app.utils.auth import SessionLocal
from app.models import Channel, Category, ScraperURL

# Connetti al vecchio DB
old_db = sqlite3.connect('path/to/acestream-scraper/data.db')
old_cursor = old_db.cursor()

# Connetti al nuovo DB
new_db = SessionLocal()

# Migra categorie
old_cursor.execute("SELECT id, name, description FROM categories")
for old_id, name, desc in old_cursor.fetchall():
    category = Category(name=name, description=desc)
    new_db.add(category)

new_db.commit()

# Migra canali
old_cursor.execute("""
    SELECT acestream_id, name, logo_url, epg_id, category_id 
    FROM channels
""")

for ace_id, name, logo, epg_id, cat_id in old_cursor.fetchall():
    # Trova categoria corrispondente
    if cat_id:
        old_cursor.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
        cat_name = old_cursor.fetchone()
        if cat_name:
            category = new_db.query(Category).filter(Category.name == cat_name[0]).first()
            cat_id = category.id if category else None
    
    channel = Channel(
        acestream_id=ace_id,
        name=name,
        logo_url=logo,
        epg_id=epg_id,
        category_id=cat_id,
        is_active=True
    )
    new_db.add(channel)

new_db.commit()
print("Migrazione completata!")
```

### 2. Migrazione Config xtream_api

Se hai configurazioni da xtream_api:

```python
# migrate_from_xtream.py
import sys
sys.path.insert(0, 'path/to/xtream_api')
import config as old_config

from app.config import Config

# Crea nuovo .env basato sul vecchio config
env_content = f"""
SERVER_HOST={old_config.SERVER_IP}
SERVER_XTREAM_PORT={old_config.SERVER_PORT}
ADMIN_USERNAME={old_config.ADMIN_USERNAME}
ADMIN_PASSWORD={old_config.ADMIN_PASSWORD}

SCRAPER_URLS={old_config.IPTV_LIST_URL}
EPG_SOURCES={','.join(old_config.IPTV_EPG_LIST_IN)}
EPG_UPDATE_INTERVAL={old_config.IPTV_UPD_INTERVAL_EPG}

ACESTREAM_ENGINE_HOST={old_config.ENGINE_URL.split(':')[0]}
ACESTREAM_ENGINE_PORT={old_config.ENGINE_URL.split(':')[1]}
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("Config migrata!")
```

### 3. Migrazione Utenti xtream_api

```python
# migrate_users.py
import sqlite3
from app.utils.auth import SessionLocal, get_password_hash
from app.models import User
from datetime import datetime

# Connetti al vecchio DB
old_db = sqlite3.connect('path/to/xtream_api/data.db')
old_cursor = old_db.cursor()

# Connetti al nuovo DB
new_db = SessionLocal()

# Migra utenti
old_cursor.execute("""
    SELECT username, password, is_admin, max_connections, expiry_date
    FROM users
""")

for username, password, is_admin, max_conn, expiry in old_cursor.fetchall():
    # Nota: se il password era già hashata, usa quella
    # altrimenti re-hash
    user = User(
        username=username,
        password_hash=password,  # Assumo già hashata
        is_admin=bool(is_admin),
        max_connections=max_conn or 1,
        expiry_date=datetime.fromisoformat(expiry) if expiry else None,
        is_active=True
    )
    new_db.add(user)

new_db.commit()
print(f"Migrati {len(list(old_cursor))} utenti")
```

### 4. Import Playlist M3U Esistente

Se hai una playlist M3U da importare:

```python
# import_m3u.py
import re
from app.utils.auth import SessionLocal
from app.models import Channel, Category

def import_m3u(file_path):
    db = SessionLocal()
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            current_channel = {}
            
            # Extract metadata
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            if logo_match:
                current_channel['logo_url'] = logo_match.group(1)
            
            category_match = re.search(r'group-title="([^"]+)"', line)
            if category_match:
                cat_name = category_match.group(1)
                category = db.query(Category).filter(Category.name == cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.add(category)
                    db.flush()
                current_channel['category_id'] = category.id
            
            name_match = re.search(r',(.+)$', line)
            if name_match:
                current_channel['name'] = name_match.group(1).strip()
        
        elif line and not line.startswith('#'):
            # Extract acestream ID
            ace_match = re.search(r'([0-9a-fA-F]{40})', line)
            if ace_match and current_channel.get('name'):
                acestream_id = ace_match.group(1).lower()
                
                # Check if exists
                existing = db.query(Channel).filter(
                    Channel.acestream_id == acestream_id
                ).first()
                
                if not existing:
                    channel = Channel(
                        acestream_id=acestream_id,
                        name=current_channel['name'],
                        logo_url=current_channel.get('logo_url'),
                        category_id=current_channel.get('category_id'),
                        is_active=True
                    )
                    db.add(channel)
            
            current_channel = {}
    
    db.commit()
    print("Import M3U completato!")

# Uso
import_m3u('path/to/playlist.m3u')
```

## 🔧 Configurazione Compatibilità

### Mantenere URL esistenti

Se vuoi mantenere compatibilità con URL esistenti del vecchio xtream_api:

```python
# In app/api/xtream.py, aggiungi route legacy:

@router.get("/live/{username}/{password}/{stream_id}.{ext}")
async def legacy_stream(username: str, password: str, stream_id: int, ext: str):
    """Legacy URL format support"""
    return await stream_channel(request, username, password, stream_id, ext)
```

### Redirect da vecchi endpoint

```nginx
# nginx config per redirect
location /old-api/ {
    rewrite ^/old-api/(.*)$ /player_api.php?$1 permanent;
}
```

## ✅ Checklist Post-Migrazione

- [ ] Database migrato correttamente
- [ ] Utenti importati e funzionanti
- [ ] Canali visibili nell'API Xtream
- [ ] EPG configurato e aggiornato
- [ ] AceStream Engine connesso
- [ ] Test con player IPTV (Smarters, Perfect Player)
- [ ] Backup del vecchio database creato
- [ ] Vecchi servizi fermati
- [ ] Monitoraggio logs attivo

## 🆘 Troubleshooting Migrazione

### Problema: Canali duplicati

```sql
-- Trova duplicati
SELECT acestream_id, COUNT(*) 
FROM channels 
GROUP BY acestream_id 
HAVING COUNT(*) > 1;

-- Rimuovi duplicati (mantieni il più recente)
DELETE FROM channels 
WHERE id NOT IN (
    SELECT MAX(id) 
    FROM channels 
    GROUP BY acestream_id
);
```

### Problema: Password utenti non funzionano

```python
# Re-hash password se necessario
from app.utils.auth import get_password_hash, SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()

for user in users:
    # Se password era in chiaro nel vecchio sistema
    user.password_hash = get_password_hash(user.password_hash)

db.commit()
```

### Problema: EPG non corrisponde ai canali

```python
# Match EPG IDs
from app.utils.auth import SessionLocal
from app.models import Channel

db = SessionLocal()

# Imposta EPG ID basato sul nome canale
channels = db.query(Channel).all()
for channel in channels:
    if not channel.epg_id:
        # Normalizza nome per EPG ID
        epg_id = channel.name.lower().replace(' ', '_')
        channel.epg_id = epg_id

db.commit()
```

## 📊 Verifica Migrazione

Script di verifica completo:

```python
# verify_migration.py
from app.utils.auth import SessionLocal
from app.models import User, Channel, Category

db = SessionLocal()

print("=== Verifica Migrazione ===\n")

users_count = db.query(User).count()
print(f"✓ Utenti: {users_count}")

channels_count = db.query(Channel).count()
active_channels = db.query(Channel).filter(Channel.is_active == True).count()
print(f"✓ Canali: {channels_count} (attivi: {active_channels})")

categories_count = db.query(Category).count()
print(f"✓ Categorie: {categories_count}")

channels_with_ace = db.query(Channel).filter(Channel.acestream_id != None).count()
print(f"✓ Canali con AceStream ID: {channels_with_ace}")

channels_with_epg = db.query(Channel).filter(Channel.epg_id != None).count()
print(f"✓ Canali con EPG ID: {channels_with_epg}")

print("\n=== Test API ===")
print("Test con:")
print(f"  curl http://localhost:58055/player_api.php?username=admin&password=PASSWORD")
```

## 🎯 Prossimi Passi

1. **Testa completamente** la piattaforma con i tuoi player
2. **Monitora i logs** per eventuali errori
3. **Backup regolare** del nuovo database
4. **Disabilita** i vecchi servizi dopo conferma
5. **Documenta** eventuali personalizzazioni

## 📝 Note Importanti

- Fai **sempre backup** prima di migrare
- Testa in ambiente di sviluppo prima di produzione
- La migrazione password dipende dal metodo di hash usato in origine
- Alcuni metadati potrebbero richiedere mapping manuale
- EPG IDs devono corrispondere tra fonti EPG e canali
