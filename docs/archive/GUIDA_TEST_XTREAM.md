# Guida Rapida: Test del Server Xtream Code Corretto

## Modifiche Apportate

Il server Xtream Code è stato corretto per funzionare come nel progetto originale `xtream_api`. Le modifiche principali includono:

1. ✅ Aggiunta classe `StreamHelper` per streaming asincrono con aiohttp
2. ✅ Aggiunta classe `ClientTracker` per tracking delle connessioni
3. ✅ Correzione endpoint `/live/` per proxy streaming invece di redirect
4. ✅ Aggiunta endpoint container per compatibilità
5. ✅ Aggiunta endpoint movie/series (stub)
6. ✅ Correzione URL nella playlist M3U con prefisso `/live/`

## File Modificati

- `app/api/xtream.py` - Tutte le correzioni applicate

## Come Testare

### 1. Avvia il Server

```bash
cd /home/wafy/src/acextream/unified-iptv-acestream
python main.py
```

### 2. Test Automatico

Esegui lo script di test automatico:

```bash
python test_xtream_api.py
```

Lo script testerà:
- ✓ Autenticazione (player_api.php)
- ✓ Elenco categorie (get_live_categories)
- ✓ Elenco canali (get_live_streams)
- ✓ Generazione playlist M3U
- ✓ Endpoint streaming
- ✓ EPG XMLTV

### 3. Test Manuale

#### Test Autenticazione
```bash
curl "http://localhost:8000/player_api.php?username=admin&password=admin"
```

Risposta attesa:
```json
{
  "user_info": {
    "username": "admin",
    "status": "Active",
    ...
  },
  "server_info": {
    "url": "http://localhost:8000",
    ...
  }
}
```

#### Test Categorie
```bash
curl "http://localhost:8000/player_api.php?username=admin&password=admin&action=get_live_categories"
```

#### Test Canali
```bash
curl "http://localhost:8000/player_api.php?username=admin&password=admin&action=get_live_streams"
```

#### Test Playlist M3U
```bash
curl "http://localhost:8000/get.php?username=admin&password=admin&type=m3u_plus" -o playlist.m3u
```

Verifica che le URL nella playlist inizino con `/live/`:
```bash
grep -o "http://[^/]*/live/" playlist.m3u | head -5
```

#### Test Streaming (se hai canali)
```bash
# Sostituisci {CHANNEL_ID} con un ID canale reale
curl "http://localhost:8000/live/admin/admin/{CHANNEL_ID}.ts" --output test_stream.ts
```

#### Test EPG
```bash
curl "http://localhost:8000/xmltv.php?username=admin&password=admin" -o epg.xml
```

### 4. Test con Player IPTV

Configura il tuo player IPTV (IPTV Smarters, Perfect Player, TiviMate, ecc.) con:

- **Server URL**: `http://localhost:8000`
- **Username**: `admin`
- **Password**: `admin`

Il player dovrebbe:
1. Autenticarsi correttamente
2. Caricare le categorie
3. Mostrare i canali
4. Riprodurre lo streaming senza errori

## Verifica delle Correzioni

### 1. StreamHelper attivo?
Quando accedi a un canale, dovresti vedere nei log:
```
INFO:app.api.xtream:Streaming from http://... started successfully
```

### 2. Client Tracking attivo?
I client dovrebbero essere tracciati nella sessione. Controlla i log quando accedi allo stesso canale due volte.

### 3. URL Playlist corrette?
Apri `playlist.m3u` e verifica che le URL abbiano il formato:
```
http://localhost:8000/live/admin/admin/1.ts
```

NON:
```
http://localhost:8000/admin/admin/1.ts
```

## Risoluzione Problemi

### Errore "Unauthorized" o "Invalid credentials"
- Verifica username e password
- Assicurati che l'utente admin sia creato nel database

### Errore "Channel not found"
- Aggiungi canali tramite scraper o manualmente
- Verifica che i canali siano attivi (`is_active=True`)

### Stream non parte
- Verifica che il canale abbia `stream_url` o `acestream_id`
- Se usa AceStream, verifica che il motore AceStream sia avviato
- Controlla i log per errori HTTP

### Errore "No stream URL available"
- Il canale deve avere almeno uno tra:
  - `stream_url` (URL diretto)
  - `acestream_id` (ID AceStream)

## Confronto con Progetto Originale

Il comportamento è ora identico al progetto originale `xtream_api`:

| Funzionalità | Originale | Unificato (Prima) | Unificato (Corretto) |
|--------------|-----------|------------------|---------------------|
| Stream proxy asincrono | ✓ | ✗ | ✓ |
| Client tracking | ✓ | ✗ | ✓ |
| Endpoint completi | ✓ | Parziali | ✓ |
| Compatibilità player | ✓ | ✗ | ✓ |

## Documentazione Completa

Per dettagli tecnici completi, consulta:
- `XTREAM_SERVER_FIX.md` - Spiegazione dettagliata delle correzioni
- `CONFRONTO_XTREAM.md` - Confronto codice originale vs unificato

## Prossimi Passi

1. Popola il database con canali (tramite scraper o manualmente)
2. Configura EPG sources
3. Testa con un player IPTV reale
4. Implementa VOD/Series quando necessario (attualmente stub)

## Note

- Gli endpoint `/movie/` e `/series/` ritornano 404 (non ancora implementati)
- Il server supporta sia stream diretti (HTTP/HLS) che AceStream
- Il client tracking rimuove automaticamente client inattivi dopo 15 secondi
