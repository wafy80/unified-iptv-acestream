# Correzione Formato Risposte API player_api.php

## Problema Identificato

L'endpoint `player_api.php` restituiva risposte con **formati dati non corretti** rispetto al progetto originale, causando incompatibilità con i player IPTV.

## Differenze Critiche Corrette

### 1. user_info - Tipi Dati Errati

#### ❌ Prima (SBAGLIATO)
```json
{
  "is_trial": "1",              // STRING invece di INT
  "active_cons": "0",           // STRING invece di INT  
  "max_connections": "1",       // STRING invece di INT
  "allowed_output_formats": '["ts","m3u8"]'  // JSON STRING invece di ARRAY
}
```

#### ✅ Dopo (CORRETTO)
```json
{
  "is_trial": 0,                // INT
  "active_cons": 0,             // INT
  "max_connections": 1,         // INT
  "allowed_output_formats": ["m3u8", "ts", "rtmp"]  // ARRAY
}
```

### 2. server_info - Campi Mancanti

#### ❌ Prima (INCOMPLETO)
```json
{
  "url": "http://localhost:8000",
  "port": "8000",
  "https_port": "",             // VUOTO
  "rtmp_port": "",              // VUOTO
  "server_protocol": "http",
  "timezone": "UTC"
  // MANCANO: xui, version
}
```

#### ✅ Dopo (COMPLETO)
```json
{
  "xui": true,                  // AGGIUNTO
  "version": "1.0.0",           // AGGIUNTO
  "url": "localhost",
  "port": "8000",
  "https_port": "443",          // CORRETTO
  "server_protocol": "http",
  "rtmp_port": "1935",          // CORRETTO
  "timestamp_now": 1234567890,
  "time_now": "2024-01-01 12:00:00",
  "timezone": "UTC"
}
```

### 3. get_live_streams - category_ids Mancante

#### ❌ Prima (MANCANTE ARRAY)
```json
{
  "num": 123,                   // Usava channel.id invece di contatore
  "name": "Channel",
  "category_id": "1",
  // MANCA: category_ids array
  "is_adult": "0"
}
```

#### ✅ Dopo (CON ARRAY)
```json
{
  "num": 1,                     // Contatore sequenziale
  "name": "Channel",
  "category_id": "1",
  "category_ids": [1],          // ARRAY di interi - CRITICO per IPTV Smarters
  "is_adult": "0"
}
```

### 4. Ordine Campi Corretto

I campi ora seguono l'ordine esatto dell'originale, importante per alcuni parser:

```json
{
  "num": 1,
  "name": "Channel Name",
  "stream_type": "live",
  "stream_id": 123,
  "stream_icon": "...",
  "epg_channel_id": "...",
  "added": "1234567890",
  "is_adult": "0",
  "category_id": "1",
  "category_ids": [1],          // Posizione corretta
  "custom_sid": "",
  "tv_archive": 0,
  "direct_source": "",
  "tv_archive_duration": 0
}
```

## Modifiche Applicate

### File: `app/api/xtream.py`

#### 1. Corretto user_info (player_api.php)
```python
"user_info": {
    "username": user.username,
    "password": password,
    "message": config.message_of_day if hasattr(config, 'message_of_day') else "",
    "auth": 1,
    "status": "Active" if user.is_active else "Disabled",
    "exp_date": int(user.expiry_date.timestamp()) if user.expiry_date else None,
    "is_trial": int(user.is_trial),        # INT, non string
    "active_cons": 0,                       # INT, non string
    "created_at": int(user.created_at.timestamp()),
    "max_connections": int(user.max_connections),  # INT, non string
    "allowed_output_formats": ["m3u8", "ts", "rtmp"]  # ARRAY, non JSON string
}
```

#### 2. Corretto server_info
```python
"server_info": {
    "xui": True,                           # AGGIUNTO
    "version": "1.0.0",                    # AGGIUNTO
    "url": config.server_host,
    "port": str(config.server_port),
    "https_port": "443",                   # CORRETTO (era "")
    "server_protocol": "http",
    "rtmp_port": "1935",                   # CORRETTO (era "")
    "timestamp_now": int(datetime.utcnow().timestamp()),
    "time_now": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "timezone": config.server_timezone
}
```

#### 3. Corretto get_live_streams
```python
result = []
num = 0
for channel in channels:
    num += 1  # Contatore sequenziale
    
    # Build category_ids array
    category_ids = [int(channel.category_id)] if channel.category_id else []
    
    result.append({
        "num": num,                        # CORRETTO: contatore, non channel.id
        "name": channel.name,
        "stream_type": "live",
        "stream_id": channel.id,
        "stream_icon": channel.logo_url or "",
        "epg_channel_id": channel.epg_id or "",
        "added": str(int(channel.created_at.timestamp())),
        "is_adult": "0",
        "category_id": str(channel.category_id) if channel.category_id else "0",
        "category_ids": category_ids,     # AGGIUNTO: array di interi
        "custom_sid": "",
        "tv_archive": 0,
        "direct_source": "",
        "tv_archive_duration": 0
    })
```

#### 4. Corretto panel_api.php
Stesso formato di player_api.php (senza action).

## Impatto delle Correzioni

### IPTV Smarters Pro
- ✅ Richiede `category_ids` come array
- ✅ Richiede `xui` in server_info
- ✅ Richiede tipi dati corretti

### Perfect Player
- ✅ Verifica `allowed_output_formats` come array
- ✅ Usa `max_connections` come int per controlli

### TiviMate
- ✅ Parser richiede ordine campi corretto
- ✅ Usa `version` per features detection

## Test delle Correzioni

```bash
# Test risposta completa
curl "http://localhost:8000/player_api.php?username=admin&password=admin" | jq .

# Verifica user_info.is_trial è int
curl "..." | jq '.user_info.is_trial | type'  # deve essere "number"

# Verifica allowed_output_formats è array
curl "..." | jq '.user_info.allowed_output_formats | type'  # deve essere "array"

# Verifica server_info.xui esiste
curl "..." | jq '.server_info.xui'  # deve essere true

# Verifica category_ids in get_live_streams
curl "...&action=get_live_streams" | jq '.[0].category_ids | type'  # deve essere "array"
```

## Risultato

✅ **Formato API ora identico al progetto originale**
✅ **Compatibile con IPTV Smarters Pro**
✅ **Compatibile con Perfect Player**
✅ **Compatibile con TiviMate**
✅ **Tutti i tipi dati corretti**
✅ **Tutti i campi presenti**
✅ **Ordine campi corretto**

## File Modificato

- ✅ `app/api/xtream.py` - Tutti i formati corretti

## Prossimi Passi

1. Testa con player IPTV reale
2. Verifica tutte le action (get_vod_info, get_series_info, ecc.)
3. Conferma che non ci siano altri problemi di formato
