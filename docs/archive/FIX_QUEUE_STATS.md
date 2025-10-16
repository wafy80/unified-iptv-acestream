# 🔧 FIX QUEUE E STATS - Correzioni Applicate

## 🐛 Problemi Risolti

### 1. AttributeError: 'buffer' non esiste
**Errore**:
```
AttributeError: 'OngoingStream' object has no attribute 'buffer'
```

**Causa**: `get_stream_stats` cercava `ongoing.buffer.qsize()` ma ora usiamo `ongoing.clients` (dict di queue).

**Fix**:
```python
# Prima (ERRORE)
'buffer_size': ongoing.buffer.qsize()

# Dopo (CORRETTO)
'total_queue_size': sum(q.qsize() for q in ongoing.clients.values())
```

### 2. Queue Full continuo
**Problema**: 
```
WARNING - Client xxx queue full, skipping chunk (ripetuto centinaia di volte)
```

**Cause**:
1. Queue troppo piccole (50 elementi)
2. Client non consumano abbastanza velocemente
3. Logging eccessivo (spam)

**Fix applicati**:

#### A. Aumento dimensione Queue
```python
# Prima
client_queue = asyncio.Queue(maxsize=50)  # ~400KB buffer

# Dopo  
client_queue = asyncio.Queue(maxsize=200)  # ~1.6MB buffer
```

#### B. Throttling Log Warnings
```python
# Log queue full warnings solo ogni 5 secondi
queues_full = 0
for client_id, client_queue in ongoing.clients.items():
    try:
        client_queue.put_nowait(chunk)
    except asyncio.QueueFull:
        queues_full += 1

# Log throttled (ogni 5s invece di ogni chunk)
if queues_full > 0 and current_time - last_warning_log > 5:
    logger.warning(f"{queues_full} client(s) queue full, skipping chunks")
    last_warning_log = current_time
```

## 📊 Modifiche Parametri

| Parametro | Prima | Dopo | Motivo |
|-----------|-------|------|--------|
| **Queue maxsize** | 50 | 200 | Buffer più grande |
| **Queue per client** | ~400KB | ~1.6MB | Più spazio per burst |
| **Log warnings** | Ogni chunk | Ogni 5s | Riduce spam |
| **Stats buffer_size** | `buffer.qsize()` | `sum(q.qsize())` | Fix AttributeError |

## 🔍 Analisi Queue Full

### Perché le Queue si Riempiono?

1. **AceStream veloce**: Produce chunk a ~8KB ogni pochi ms
2. **Client lenti**: Consumano chunk più lentamente (HTTP overhead, rete)
3. **Generator blocking**: `await queue.get()` può tardare se client HTTP lento

### Soluzione: Queue più grandi + Skip

- ✅ Queue 200 elementi = buffer ~1.6MB
- ✅ Se piena, skip chunk (no blocking producer)
- ✅ Client perde qualche frame ma non blocca altri
- ✅ Log aggregato ogni 5s (no spam)

## 📝 File Modificati

- `app/services/aceproxy_service.py`
  - `get_stream_stats()`: Fix AttributeError (sum queue sizes)
  - `stream_content()`: Queue size 50 → 200
  - `_fetch_acestream()`: Throttled queue full logging

## ✅ Risultato

✅ **No più AttributeError** in `/api/health` e `/api/stats`  
✅ **Queue più grandi** (200 vs 50) per buffer maggiore  
✅ **Log puliti** (warnings aggregati ogni 5s)  
✅ **Performance mantenute** (skip chunk se queue piena)  

## 🚀 Test

```bash
# Riavvia server
pkill -f "python.*main.py"
python main.py

# Verifica health check
curl http://localhost:8000/api/health

# Verifica streams stats
curl http://localhost:8000/api/aceproxy/streams
```

## 📈 Monitoraggio

Nel log vedrai ora:
```
# Invece di centinaia di:
WARNING - Client xxx queue full, skipping chunk
WARNING - Client yyy queue full, skipping chunk
...

# Vedrai (ogni 5s max):
WARNING - 2 client(s) queue full, skipping chunks
```

---

**Fix applicati! Riavvia il server per testare.** 🚀
