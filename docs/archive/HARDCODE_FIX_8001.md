# Fix Porta 8001 Hardcoded

## Problema
La porta 8001 del streaming server interno era hardcoded in `app/api/aceproxy.py` invece di usare la variabile `ACESTREAM_STREAMING_PORT`.

## Modifiche Effettuate

### File: app/api/aceproxy.py

#### 1. Aggiunto Import
```python
from app.config import get_config
```

#### 2. Endpoint `/ace/getstream`
**Prima:**
```python
aiohttp_url = f"http://127.0.0.1:8001/ace/getstream?..."
```

**Dopo:**
```python
config = get_config()
aiohttp_url = f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/getstream?..."
```

#### 3. Endpoint `/ace/status`
**Prima:**
```python
aiohttp_url = "http://127.0.0.1:8001/ace/status"
```

**Dopo:**
```python
config = get_config()
aiohttp_url = f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status"
```

#### 4. Endpoint `/api/aceproxy/streams/{stream_id}`
**Prima:**
```python
async with session.get(f"http://127.0.0.1:8001/ace/status?id={stream_id}") as response:
```

**Dopo:**
```python
config = get_config()
async with session.get(f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status?id={stream_id}") as response:
```

#### 5. Endpoint `/api/aceproxy/stats`
**Prima:**
```python
async with session.get("http://127.0.0.1:8001/ace/status") as response:
    ...
    "streaming_port": 8001
```

**Dopo:**
```python
config = get_config()
async with session.get(f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status") as response:
    ...
    "streaming_port": config.acestream_streaming_port
```

## Endpoint Modificati

Tutti questi endpoint ora usano le variabili d'ambiente:
- ✅ `GET /ace/getstream` - Streaming proxy
- ✅ `GET /ace/status` - Status generale
- ✅ `GET /api/aceproxy/streams/{stream_id}` - Info stream specifico
- ✅ `GET /api/aceproxy/stats` - Statistiche complessive

## Valori Non Modificati

### app/services/aiohttp_streaming_server.py
```python
listen_host: str = "127.0.0.1",  # Default parameter
listen_port: int = 8001,         # Default parameter
```
Questi sono **default del costruttore**, non hardcoded. Il valore effettivo viene passato da `main.py` usando la config:
```python
aiohttp_streaming_server = AiohttpStreamingServer(
    listen_host=config.acestream_streaming_host,
    listen_port=config.acestream_streaming_port,
    ...
)
```

### app/api/xtream.py
```python
f"http://127.0.0.1:{config.server_port}/ace/getstream"
```
Questo è **corretto**: usa `server_port` (58055) che è la porta unificata pubblica, non la porta streaming interna.

## Test

```bash
# Compilazione
python3 -m py_compile app/api/aceproxy.py
✓ OK

# Verifica hardcode rimossi
grep -n "8001" app/api/aceproxy.py
✓ Nessun risultato (rimossi tutti)
```

## Benefici

1. **Configurabilità**: Porta streaming modificabile via `.env`
2. **Flessibilità**: Possibile usare porte diverse per evitare conflitti
3. **Consistenza**: Tutte le porte configurabili, nessun hardcode
4. **Multi-instance**: Possibile far girare istanze multiple con porte diverse

## Configurazione

### .env
```env
ACESTREAM_STREAMING_HOST=127.0.0.1
ACESTREAM_STREAMING_PORT=8001
```

### docker-compose.yml
```yaml
environment:
  - ACESTREAM_STREAMING_HOST=127.0.0.1
  - ACESTREAM_STREAMING_PORT=8001
```

## Esempio Uso Porta Diversa

Se la porta 8001 è occupata:
```env
ACESTREAM_STREAMING_PORT=8002
```

Nessun'altra modifica necessaria - tutto usa automaticamente la nuova porta.
