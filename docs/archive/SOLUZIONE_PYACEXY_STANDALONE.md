# 🔧 Soluzione Performance - Usare pyacexy Standalone

## 🎯 Problema Identificato

L'**AceProxyService** (reimplementazione) ha problemi di performance rispetto a **pyacexy originale**:

### Differenze Critiche

| Aspetto | pyacexy Originale | AceProxyService (Unificato) |
|---------|-------------------|----------------------------|
| **Distribuzione** | Scrive direttamente ai client | Usa Queue (asyncio.Queue) |
| **Buffer** | Nessuna Queue intermedia | Queue maxsize=100 causa ritardi |
| **Client handling** | web.StreamResponse diretta | Generator con Queue.get() |
| **Chunk distribution** | Sincrona ai client | Asincrona via Queue |
| **Stale client cleanup** | ✅ Automatico ogni 15s | ❌ Mancante |
| **first_chunk event** | ✅ Presente | ❌ Mancante |

## 🔴 Performance Issue

### AceProxyService (Attuale - LENTO)
```python
# Fetch task scrive in Queue
await ongoing.buffer.put(chunk)  # Può bloccarsi se piena

# Client legge da Queue
chunk = await ongoing.buffer.get()  # Ritardo se vuota
yield chunk
```

**Problema**: Queue intermedia aggiunge latenza e può causare blocchi.

### pyacexy Originale (VELOCE)
```python
# Scrive direttamente a tutti i client
async with ongoing.lock:
    for client_response in ongoing.clients:
        await client_response.write(chunk)  # Diretto!
```

**Vantaggio**: Nessuna Queue intermedia, distribuzione immediata.

## ✅ Soluzioni

### Opzione 1: Usare pyacexy Standalone (CONSIGLIATO)

1. **Avvia pyacexy** come servizio separato:
```bash
cd /home/wafy/src/acextream/pyacexy
python -m pyacexy.proxy --host 0.0.0.0 --port 8080
```

2. **Configura Xtream** per usarlo:
```python
# In app/api/xtream.py
if channel.acestream_id:
    # Chiama pyacexy standalone su porta 8080
    stream_url = f"http://localhost:8080/ace/getstream?id={channel.acestream_id}"
    return StreamingResponse(StreamHelper.receive_stream(stream_url))
```

3. **Disabilita AceProxyService** in .env:
```bash
ACESTREAM_ENABLED=false
```

**Vantaggi**:
- ✅ Performance ottimale (pyacexy testato e ottimizzato)
- ✅ Multiplexing funzionante
- ✅ Gestione client stale
- ✅ Nessuna Queue intermedia

### Opzione 2: Migliorare AceProxyService

Riscrivere `_fetch_acestream` per distribuire direttamente (come pyacexy):

```python
async def _fetch_acestream(self, ongoing: OngoingStream):
    # Connetti ad AceStream
    async with self.session.get(ongoing.acestream.playback_url) as response:
        ongoing.started.set()
        
        # Distribuisci direttamente (NO Queue)
        async for chunk in response.content.iter_chunked(8192):
            # Scrivi a tutti i client direttamente
            for client_generator in ongoing.clients:
                try:
                    # Invia chunk direttamente al generator
                    await client_generator.asend(chunk)
                except:
                    # Rimuovi client morto
                    ongoing.clients.remove(client_generator)
```

**Problema**: Richiede refactoring completo dell'architettura.

## 📝 Raccomandazione

**Usare pyacexy standalone** (Opzione 1) è la soluzione migliore perché:

1. ✅ **Zero modifiche** al codice complesso
2. ✅ **Performance garantite** (pyacexy testato)
3. ✅ **Manutenzione** separata (pyacexy aggiornabile)
4. ✅ **Scalabilità** (pyacexy può girare su server separato)

## 🚀 Setup pyacexy Standalone

### 1. Installa pyacexy
```bash
cd /home/wafy/src/acextream/pyacexy
pip install -e .
```

### 2. Crea servizio systemd
```bash
# /etc/systemd/system/pyacexy.service
[Unit]
Description=PyAcexy AceStream Proxy
After=network.target

[Service]
Type=simple
User=wafy
WorkingDirectory=/home/wafy/src/acextream/pyacexy
ExecStart=/usr/bin/python3 -m pyacexy.proxy --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Avvia servizio
```bash
sudo systemctl start pyacexy
sudo systemctl enable pyacexy
```

### 4. Configura Xtream
```python
# app/api/xtream.py - Cambia porta da 8000 a 8080
if channel.acestream_id:
    stream_url = f"http://localhost:8080/ace/getstream?id={channel.acestream_id}"
```

### 5. Disabilita AceProxyService
```bash
# .env
ACESTREAM_ENABLED=false
```

## ✅ Risultato

Con pyacexy standalone:
- ✅ Performance ottimali
- ✅ Multiplexing efficiente
- ✅ Nessun ritardo Queue
- ✅ Gestione client stale
- ✅ Codice testato e stabile

---

**Usa pyacexy standalone per risolvere i problemi di performance!**
