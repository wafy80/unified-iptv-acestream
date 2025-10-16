# EPG API Endpoints - Documentazione

## Overview

Il sistema EPG è stato integrato con il metodo XMLTV di xtream_api e include nuovi endpoint API per la gestione completa dell'EPG.

## Aggiornamento Automatico EPG

Il loop di aggiornamento automatico (`auto_update_loop`) è stato migliorato per supportare due modalità:

### Modalità XMLTV (Preferita)
Se sono configurate sorgenti XMLTV in `epg_sources`, il sistema usa il metodo `update_epg_with_xmltv()`:
- Scarica file EPG da URL configurati
- Decomprime automaticamente file gzip
- Parser formato XMLTV
- Abbina canali tramite `epg_id`
- Genera file consolidato `data/epg.xml`

### Modalità Database Sources (Fallback)
Se non ci sono sorgenti XMLTV configurate, usa il metodo `update_all_epg()`:
- Usa sorgenti EPG nel database (tabella `epg_sources`)
- Parser programmi e aggiornamento database

### Configurazione Intervallo

```python
# In .env o config
EPG_UPDATE_INTERVAL=86400  # Secondi (default: 24 ore)
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz
```

## Endpoint API

### 1. GET /xmltv.php (Xtream API)

Endpoint compatibile Xtream Codes per ottenere EPG in formato XMLTV.

**URL**: `/xmltv.php?username={USERNAME}&password={PASSWORD}`

**Metodo**: GET

**Parametri Query**:
- `username` (opzionale): Nome utente per autenticazione
- `password` (opzionale): Password per autenticazione

**Risposta**: XML in formato XMLTV

**Esempio**:
```bash
curl "http://localhost:8000/xmltv.php?username=admin&password=changeme"
```

**Esempio Risposta**:
```xml
<?xml version='1.0' encoding='utf-8'?>
<tv date="20251012210000 +0000" generator_info_name="unified-iptv-acestream">
  <channel id="bbc-one.uk">
    <display-name>BBC One</display-name>
    <icon src="https://example.com/bbc-one.png"/>
  </channel>
  <programme channel="bbc-one.uk" start="20251012200000 +0000" stop="20251012210000 +0000">
    <title>News at Six</title>
    <desc>Evening news programme</desc>
    <category>News</category>
  </programme>
</tv>
```

---

### 2. POST /epg/update

Trigger manuale aggiornamento EPG (richiede accesso admin).

**URL**: `/epg/update?username={USERNAME}&password={PASSWORD}`

**Metodo**: POST

**Parametri Query**:
- `username` (richiesto): Nome utente admin
- `password` (richiesto): Password admin
- `use_xmltv` (opzionale, default: true): Usa metodo XMLTV se disponibile

**Risposta**: JSON con risultato aggiornamento

**Esempio**:
```bash
# Aggiornamento con metodo XMLTV
curl -X POST "http://localhost:8000/epg/update?username=admin&password=changeme&use_xmltv=true"

# Aggiornamento con metodo database
curl -X POST "http://localhost:8000/epg/update?username=admin&password=changeme&use_xmltv=false"
```

**Esempio Risposta**:
```json
{
  "success": true,
  "method": "xmltv",
  "programmes_updated": 15420,
  "message": "EPG updated successfully using XMLTV method"
}
```

**Errori**:
- `401`: Autenticazione fallita
- `403`: Accesso negato (non admin)
- `500`: Errore durante aggiornamento

---

### 3. GET /epg/status

Ottieni statistiche e stato EPG.

**URL**: `/epg/status?username={USERNAME}&password={PASSWORD}`

**Metodo**: GET

**Parametri Query**:
- `username` (richiesto): Nome utente
- `password` (richiesto): Password

**Risposta**: JSON con statistiche EPG

**Esempio**:
```bash
curl "http://localhost:8000/epg/status?username=admin&password=changeme"
```

**Esempio Risposta**:
```json
{
  "total_channels": 150,
  "channels_with_epg_id": 120,
  "total_programs": 15420,
  "current_programs": 120,
  "future_programs": 15300,
  "xmltv_sources": [
    "https://iptvx.one/EPG_NOARCH",
    "https://epg.pw/xmltv/epg.xml.gz"
  ],
  "xmltv_sources_count": 2,
  "database_sources": [
    {
      "id": 1,
      "url": "https://example.com/epg.xml.gz",
      "enabled": true,
      "last_updated": "2025-10-12T20:00:00",
      "programs_found": 5000
    }
  ],
  "database_sources_count": 1,
  "update_interval": 86400,
  "cache_file": "data/epg.xml"
}
```

---

### 4. GET /epg/channel/{channel_id}

Ottieni EPG per un canale specifico.

**URL**: `/epg/channel/{channel_id}?username={USERNAME}&password={PASSWORD}&hours={HOURS}`

**Metodo**: GET

**Parametri Path**:
- `channel_id` (richiesto): ID del canale

**Parametri Query**:
- `username` (opzionale): Nome utente
- `password` (opzionale): Password
- `hours` (opzionale, default: 24): Ore di EPG da restituire

**Risposta**: JSON con programmi del canale

**Esempio**:
```bash
# EPG prossime 24 ore
curl "http://localhost:8000/epg/channel/1?username=admin&password=changeme"

# EPG prossime 48 ore
curl "http://localhost:8000/epg/channel/1?username=admin&password=changeme&hours=48"
```

**Esempio Risposta**:
```json
{
  "channel_id": 1,
  "channel_name": "BBC One",
  "epg_id": "bbc-one.uk",
  "programs": [
    {
      "id": 1001,
      "title": "News at Six",
      "description": "Evening news programme",
      "start_time": "2025-10-12T18:00:00",
      "end_time": "2025-10-12T18:30:00",
      "duration_minutes": 30,
      "category": "News",
      "icon_url": "https://example.com/news.png",
      "rating": null
    },
    {
      "id": 1002,
      "title": "EastEnders",
      "description": "Drama series",
      "start_time": "2025-10-12T19:30:00",
      "end_time": "2025-10-12T20:00:00",
      "duration_minutes": 30,
      "category": "Drama",
      "icon_url": null,
      "rating": "PG"
    }
  ],
  "total_programs": 2
}
```

**Errori**:
- `401`: Autenticazione fallita
- `404`: Canale non trovato

---

## Endpoint Xtream API Player (Esistenti Migliorati)

### GET /player_api.php

Gli endpoint EPG in `player_api.php` ora usano i nuovi metodi migliorati.

#### action=get_short_epg

Ottieni EPG breve per un canale (prossimi 4 programmi di default).

**URL**: `/player_api.php?username={USER}&password={PASS}&action=get_short_epg&stream_id={ID}&limit={N}`

**Parametri**:
- `stream_id` (richiesto): ID del canale
- `limit` (opzionale, default: 4): Numero programmi da restituire

**Esempio**:
```bash
curl "http://localhost:8000/player_api.php?username=admin&password=changeme&action=get_short_epg&stream_id=1&limit=4"
```

**Risposta**:
```json
{
  "epg_listings": [
    {
      "id": "1001",
      "epg_id": "1001",
      "title": "News at Six",
      "lang": "",
      "start": "2025-10-12 18:00:00",
      "end": "2025-10-12 18:30:00",
      "description": "Evening news programme",
      "channel_id": "1",
      "start_timestamp": 1728756000,
      "stop_timestamp": 1728757800,
      "has_archive": 0
    }
  ]
}
```

#### action=get_simple_data_table

Ottieni tabella EPG completa per un canale (7 giorni).

**URL**: `/player_api.php?username={USER}&password={PASS}&action=get_simple_data_table&stream_id={ID}`

**Parametri**:
- `stream_id` (richiesto): ID del canale

**Esempio**:
```bash
curl "http://localhost:8000/player_api.php?username=admin&password=changeme&action=get_simple_data_table&stream_id=1"
```

**Risposta**: Stessa struttura di `get_short_epg` ma con tutti i programmi disponibili (fino a 7 giorni).

---

## Configurazione Canali per EPG

Per funzionare correttamente, i canali devono avere l'`epg_id` impostato:

```python
# Esempio: impostare epg_id per un canale
from app.models import Channel
from app.database import SessionLocal

db = SessionLocal()
channel = db.query(Channel).filter(Channel.name == "BBC One").first()
if channel:
    channel.epg_id = "bbc-one.uk"  # Deve corrispondere all'ID nel file XMLTV
    db.commit()
```

Oppure tramite API:
```bash
# Aggiornare canale con epg_id
curl -X PATCH "http://localhost:8000/api/channels/1" \
  -H "Content-Type: application/json" \
  -d '{"epg_id": "bbc-one.uk"}'
```

---

## Workflow Completo EPG

### 1. Configurazione Iniziale

```bash
# In .env
EPG_SOURCES=https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz
EPG_UPDATE_INTERVAL=86400
EPG_CACHE_FILE=data/epg.xml
EPG_IS_GZIPPED=true
```

### 2. Impostare epg_id sui Canali

Via database o API, assegnare `epg_id` ai canali che devono corrispondere agli ID nel file XMLTV.

### 3. Trigger Primo Aggiornamento

```bash
curl -X POST "http://localhost:8000/epg/update?username=admin&password=changeme"
```

### 4. Verifica Stato

```bash
curl "http://localhost:8000/epg/status?username=admin&password=changeme"
```

### 5. Test EPG Canale

```bash
curl "http://localhost:8000/epg/channel/1?username=admin&password=changeme"
```

### 6. Ottieni XMLTV

```bash
curl "http://localhost:8000/xmltv.php?username=admin&password=changeme" > epg.xml
```

---

## Integrazione Client IPTV

### IPTV Smarters / TiviMate

Configurare URL XMLTV:
```
http://YOUR_SERVER:8000/xmltv.php?username=USERNAME&password=PASSWORD
```

### Perfect Player

URL EPG:
```
http://YOUR_SERVER:8000/xmltv.php?username=USERNAME&password=PASSWORD
```

### VLC

Può usare direttamente il file generato:
```
http://YOUR_SERVER:8000/xmltv.php
```

---

## Monitoraggio e Debug

### Logs

I log EPG includono:
- Download sorgenti XMLTV
- Parsing canali e programmi
- Aggiornamenti database
- Errori durante processing

```bash
# Visualizza log EPG
tail -f logs/app.log | grep EPG
```

### Statistiche Real-time

```bash
# Script per monitorare EPG
watch -n 60 'curl -s "http://localhost:8000/epg/status?username=admin&password=changeme" | jq'
```

---

## Troubleshooting

### EPG Non Si Aggiorna

1. Verificare configurazione sorgenti:
```bash
curl "http://localhost:8000/epg/status?username=admin&password=changeme" | jq .xmltv_sources
```

2. Trigger manuale:
```bash
curl -X POST "http://localhost:8000/epg/update?username=admin&password=changeme"
```

3. Controllare logs per errori

### Canali Senza EPG

1. Verificare `epg_id` impostato:
```bash
curl "http://localhost:8000/epg/status?username=admin&password=changeme" | jq .channels_with_epg_id
```

2. Verificare che `epg_id` corrisponda al file XMLTV

3. Controllare che la sorgente XMLTV contenga il canale

### Programmi Non Visualizzati

1. Verificare timestamp programmi:
```bash
curl "http://localhost:8000/epg/channel/1?username=admin&password=changeme&hours=168" | jq .total_programs
```

2. Programmi passati vengono rimossi automaticamente

---

## Prestazioni

### Ottimizzazioni Implementate

- ✅ Parsing asincrono file XMLTV
- ✅ Decompressione automatica gzip
- ✅ Filtraggio programmi per canali tracciati
- ✅ Caching file XMLTV consolidato
- ✅ Pulizia automatica programmi passati

### Raccomandazioni

- Usare sorgenti XMLTV compresse (gzip)
- Impostare `epg_id` solo sui canali attivi
- Configurare intervallo aggiornamento appropriato (24-48 ore)
- Monitorare dimensione database EPG

---

## Sicurezza

### Autenticazione

- `/xmltv.php` - Autenticazione opzionale
- `/epg/update` - Richiede credenziali admin
- `/epg/status` - Richiede autenticazione
- `/epg/channel/{id}` - Autenticazione opzionale

### Rate Limiting

Considerare l'implementazione di rate limiting per endpoint pubblici:
```python
# Esempio con slowapi
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.get("/xmltv.php")
@limiter.limit("10/minute")
async def get_epg_xml(...):
    ...
```

---

## Credits

EPG API endpoints implementati usando la gestione EPG importata da [xtream_api](../xtream_api) con supporto completo XMLTV.
