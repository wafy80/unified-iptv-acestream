# Conversione Valori Hardcoded a Variabili d'Ambiente

## Nuove Variabili d'Ambiente Aggiunte

### Scraper (1 nuova)
- ✅ `SCRAPER_UPDATE_INTERVAL=3600` - Intervallo aggiornamento automatico in secondi (default 1 ora)

### AceStream Streaming Server (5 nuove)
- ✅ `ACESTREAM_STREAMING_HOST=127.0.0.1` - Host interno streaming server
- ✅ `ACESTREAM_STREAMING_PORT=8001` - Porta interna streaming server
- ✅ `ACESTREAM_CHUNK_SIZE=8192` - Dimensione chunk streaming in bytes (8KB)
- ✅ `ACESTREAM_EMPTY_TIMEOUT=60.0` - Timeout stream vuoto in secondi
- ✅ `ACESTREAM_NO_RESPONSE_TIMEOUT=10.0` - Timeout nessuna risposta in secondi

## Modifiche ai File

### 1. app/config.py
Aggiunte nuove variabili nella classe Config:
```python
# AceStream Streaming Server
acestream_streaming_host: str = Field(default="127.0.0.1")
acestream_streaming_port: int = Field(default=8001)
acestream_chunk_size: int = Field(default=8192)
acestream_empty_timeout: float = Field(default=60.0)
acestream_no_response_timeout: float = Field(default=10.0)

# Scraper
scraper_update_interval: int = Field(default=3600)
```

### 2. app/services/scraper_service.py
Modificato costruttore per accettare parametro:
```python
def __init__(self, update_interval: int = 3600):
    self.update_interval = update_interval
```

### 3. main.py
Utilizzo delle variabili di configurazione:
```python
# Streaming server con config
aiohttp_streaming_server = AiohttpStreamingServer(
    listen_host=config.acestream_streaming_host,
    listen_port=config.acestream_streaming_port,
    chunk_size=config.acestream_chunk_size,
    empty_timeout=config.acestream_empty_timeout,
    no_response_timeout=config.acestream_no_response_timeout,
)

# Scraper con config
scraper_service = ImprovedScraperService(
    update_interval=config.scraper_update_interval
)
```

### 4. docker-compose.yml
Aggiunte variabili d'ambiente nel servizio

### 5. .env.example
Aggiunte variabili con valori default

## Vantaggi
- ✅ Nessun valore hardcoded nel codice
- ✅ Tuning personalizzabile via environment variables
- ✅ Configurazione centralizzata in un unico posto
- ✅ Facile modifica senza ricompilazione
- ✅ Default sensati mantenuti

## Totale Variabili d'Ambiente
- **Prima**: 20 variabili
- **Dopo**: 26 variabili (+6)
- Tutte le variabili ora sono configurabili via environment
