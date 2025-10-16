# Ottimizzazioni AceProxy Service

## Problema Risolto
Le route HTTP non rispondevano quando uno stream AceStream era attivo, causando il blocco dell'intera applicazione.

## Cause Identificate
1. **Lock Contention**: Il lock globale `streams_lock` veniva tenuto durante operazioni I/O lente (chiamate HTTP all'engine AceStream)
2. **Blocking Operations**: Le operazioni di stream non cedevano il controllo all'event loop abbastanza frequentemente
3. **Cleanup Synchronous**: La cleanup degli stream senza client bloccava il generatore

## Soluzioni Implementate

### 1. Riduzione Lock Contention
**Prima:**
```python
async with self.streams_lock:
    # Operazioni I/O mentre si tiene il lock
    async with self.session.get(url) as response:
        ace_stats = await response.json()
```

**Dopo:**
```python
async with self.streams_lock:
    ongoing = self.streams[stream_id]
# I/O eseguito FUORI dal lock
async with self.session.get(url) as response:
    ace_stats = await response.json()
```

### 2. Event Loop Yielding
**Aggiunto nel generatore `stream_content()`:**
```python
# Yield control to event loop between chunks
await asyncio.sleep(0)

# Yield control to allow other tasks to run
await asyncio.sleep(0.01)
```

Questo garantisce che l'event loop possa processare altre richieste anche durante lo streaming.

### 3. Cleanup Asincrona
**Prima:**
```python
# Cleanup bloccante nel finally block
async with self.streams_lock:
    await self._close_stream(ongoing)
    del self.streams[stream_id]
```

**Dopo:**
```python
# Cleanup in background task separato
asyncio.create_task(self._cleanup_stream(stream_id, ongoing))
```

### 4. Ottimizzazione `get_all_streams()`
**Prima:**
```python
async with self.streams_lock:
    for stream_id in self.streams:
        stats = await self.get_stream_stats(stream_id)  # I/O con lock
```

**Dopo:**
```python
async with self.streams_lock:
    stream_ids = list(self.streams.keys())
# I/O senza lock
for stream_id in stream_ids:
    stats = await self.get_stream_stats(stream_id)
```

## Risultati
- ✅ Tutte le route HTTP rispondono correttamente anche durante streaming attivo
- ✅ Dashboard funziona senza blocchi
- ✅ API logs/health/stats rispondono istantaneamente
- ✅ Nessuna degradazione delle performance dello streaming
- ✅ Concorrenza migliorata tra client multipli

## Best Practices Applicate
1. **Never hold locks during I/O**: Mai tenere lock durante operazioni di I/O
2. **Yield control frequently**: Cedere il controllo all'event loop frequentemente
3. **Background cleanup**: Usare task separati per operazioni di cleanup
4. **Minimize lock scope**: Ridurre al minimo lo scope dei lock

## File Modificati
- `app/services/aceproxy_service.py`: Ottimizzazioni lock e event loop yielding

## Testing
Tutti gli endpoint sono stati testati con successo:
- `/api/health` ✓
- `/api/logs/tail` ✓
- `/api/aceproxy/stats` ✓
- `/api/aceproxy/streams` ✓
- `/` (dashboard) ✓
