# Fix: Route Blocking During AceStream Streaming

## Problema
Quando un client si connetteva ad uno stream AceStream tramite `/ace/getstream`, tutte le altre route HTTP (dashboard, API, logs) non rispondevano fino alla disconnessione del client.

## Diagnosi
L'analisi ha rivelato tre problemi principali:

1. **Lock Contention**: Il lock globale `streams_lock` veniva tenuto durante operazioni I/O lente (chiamate HTTP all'engine AceStream), bloccando tutte le altre richieste che necessitavano dello stesso lock.

2. **Event Loop Starvation**: Il generatore di streaming non cedeva abbastanza frequentemente il controllo all'event loop di asyncio, impedendo ad altre coroutine di essere eseguite.

3. **Cleanup Bloccante**: La cleanup degli stream veniva eseguita in modo sincrono nel finally block del generatore, bloccando ulteriormente l'event loop.

## Soluzione Implementata

### 1. Minimizzazione Lock Scope
Tutte le operazioni I/O sono state spostate fuori dai contesti dei lock:

```python
# Prima: I/O con lock (MALE)
async with self.streams_lock:
    ongoing = self.streams[stream_id]
    async with self.session.get(url) as response:  # BLOCCA TUTTO
        stats = await response.json()

# Dopo: Lock solo per accesso memoria (BENE)
async with self.streams_lock:
    ongoing = self.streams[stream_id]
# I/O senza lock
async with self.session.get(url) as response:
    stats = await response.json()
```

### 2. Event Loop Yielding
Aggiunto yielding esplicito nel loop di streaming:

```python
while not ongoing.done.is_set():
    chunk = await asyncio.wait_for(ongoing.buffer.get(), timeout=2.0)
    yield chunk
    await asyncio.sleep(0)  # Cede controllo all'event loop
```

### 3. Cleanup Asincrona
La cleanup è stata spostata in un task separato:

```python
# Prima: Cleanup bloccante
async with self.streams_lock:
    await self._close_stream(ongoing)

# Dopo: Background task
asyncio.create_task(self._cleanup_stream(stream_id, ongoing))
```

## Risultati dei Test

### Test Stress (10 richieste concorrenti)
```
Request 1 (/api/logs/tail?lines=10): .279s
Request 2 (/api/aceproxy/stats): .047s
Request 3 (/api/aceproxy/streams): .065s
Request 4 (/api/health): .054s
...
```

### Test Durante Streaming
```
Health check #1: .037s
Health check #2: .046s
Health check #3: .025s
Health check #4: .010s
Health check #5: .010s
```

Tutte le richieste sono processate rapidamente anche durante streaming attivo.

## File Modificati
- `app/services/aceproxy_service.py`: Ottimizzazioni lock e yielding

## Commit
Vedere `OPTIMIZATION_SUMMARY.md` per dettagli tecnici completi.
