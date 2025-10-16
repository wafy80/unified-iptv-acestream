# Aggiornamento Sicurezza Dashboard

## Modifiche Implementate

### 1. Autenticazione HTTP Basic
- Tutti gli endpoint della dashboard ora richiedono autenticazione
- Credenziali: username e password configurate in ADMIN_USERNAME e ADMIN_PASSWORD
- Protezione con `secrets.compare_digest()` contro timing attacks

### 2. Binding Localhost per Dashboard
- La porta 8000 (dashboard) ora è accessibile solo da localhost
- Configurazione docker-compose: `127.0.0.1:8000:8000`
- L'accesso esterno alla dashboard richiede tunnel SSH o reverse proxy

### 3. Endpoint Protetti
Tutti questi endpoint ora richiedono autenticazione:
- `/` - Dashboard principale
- `/channels` - Gestione canali
- `/users` - Gestione utenti
- `/scraper` - Configurazione scraper
- `/epg` - Configurazione EPG
- `/settings` - Impostazioni sistema

### 4. Endpoint Pubblici (non modificati)
Questi rimangono accessibili pubblicamente:
- `/player_api.php` - Xtream API (porta 58055)
- `/get.php` - M3U playlist
- `/xmltv.php` - EPG
- `/ace/getstream` - AceProxy (porta 8080)
- `/health` - Health check

## Accesso alla Dashboard

### Locale
```bash
http://localhost:8000
```

### Remoto (via SSH tunnel)
```bash
ssh -L 8000:localhost:8000 user@server
# Poi aprire: http://localhost:8000
```

### Reverse Proxy con Autenticazione (nginx esempio)
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Credenziali Default
⚠️ **IMPORTANTE**: Cambiare le credenziali in produzione!

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```
