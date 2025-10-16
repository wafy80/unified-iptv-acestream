# Pulizia Variabili d'Ambiente

## Variabili Rimosse (11 totali)

### AceStream (4 rimosse)
- ❌ `ACESTREAM_PROXY_PORT` - hardcoded a 8080
- ❌ `ACESTREAM_BUFFER_SIZE` - non utilizzato
- ❌ `ACESTREAM_ALLOW_REMOTE` - non utilizzato

### Scraper (4 rimosse)
- ❌ `SCRAPER_RESCRAPE_INTERVAL` - hardcoded a 3600s nel servizio
- ❌ `SCRAPER_BASE_URL` - costruito dinamicamente
- ❌ `SCRAPER_ENABLE_ZERONET` - funzionalità non implementata
- ❌ `SCRAPER_ENABLE_TOR` - funzionalità non implementata

### EPG (1 rimossa)
- ❌ `EPG_IS_GZIPPED` - gestito automaticamente

### WARP (3 rimosse)
- ❌ `WARP_ENABLED` - funzionalità non implementata
- ❌ `WARP_LICENSE_KEY` - funzionalità non implementata
- ❌ `WARP_ENABLE_NAT` - funzionalità non implementata

### Server (note)
- ✅ `SERVER_DASHBOARD_PORT` e `SERVER_XTREAM_PORT` consolidate in `SERVER_PORT=58055`

## Variabili Mantenute (20 totali)

### Server (4)
- ✅ `SERVER_HOST`
- ✅ `SERVER_PORT` (porta unificata 58055)
- ✅ `SERVER_TIMEZONE`
- ✅ `SERVER_DEBUG`

### AceStream (4)
- ✅ `ACESTREAM_ENABLED`
- ✅ `ACESTREAM_ENGINE_HOST`
- ✅ `ACESTREAM_ENGINE_PORT`
- ✅ `ACESTREAM_TIMEOUT`

### Scraper (1)
- ✅ `SCRAPER_URLS` (comma-separated M3U URLs)

### EPG (3)
- ✅ `EPG_SOURCES`
- ✅ `EPG_UPDATE_INTERVAL`
- ✅ `EPG_CACHE_FILE`

### Database (4)
- ✅ `DATABASE_URL`
- ✅ `DATABASE_ECHO`
- ✅ `DATABASE_POOL_SIZE`
- ✅ `DATABASE_MAX_OVERFLOW`

### Admin (2)
- ✅ `ADMIN_USERNAME`
- ✅ `ADMIN_PASSWORD`

### Security (2)
- ✅ `SECRET_KEY`
- ✅ `ACCESS_TOKEN_EXPIRE_MINUTES`

## File Aggiornati
1. `app/config.py` - rimosse definizioni variabili non usate
2. `docker-compose.yml` - pulite variabili d'ambiente
3. `.env.example` - template aggiornato con solo variabili necessarie

## Risultato
- **Prima**: 31 variabili d'ambiente
- **Dopo**: 20 variabili d'ambiente
- **Riduzione**: 35% (-11 variabili)
