# 📚 Chiarimento Architettura AceStream

## 🔍 Struttura Progetti

### Progetto Originale `xtream_api`
```
xtream_api (porta 8000)
    ↓ fa proxy di TUTTO
StreamHelper.receive_stream("http://127.0.0.1:6878/ace/getstream?id=xxx")
    ↓
AceStream Engine (porta 6878) diretto
```

### Progetto Unificato
```
Unified IPTV (porta 8000)
    ├─ Xtream API → StreamHelper.receive_stream("http://127.0.0.1:8000/ace/getstream?id=xxx")
    │                                          ↓ proxy interno
    ├─ /ace/getstream endpoint → AceProxyService (reimplementazione pyacexy)
    │                           ↓
    └─ AceStream Engine (porta 6878)
```

## 💡 Chiarimento: pyacexy

### Cosa è pyacexy?
- **Progetto separato** in `/pyacexy/`
- Server standalone che gira su porta 8080
- Fa da **proxy avanzato** tra client e AceStream Engine
- Features: multiplexing, PID assignment, buffering

### Progetto Unificato
- **NON usa pyacexy come server separato**
- Ha `AceProxyService` = **reimplementazione** della logica pyacexy
- `AceProxyService` è integrato nel server unificato
- Espone endpoint `/ace/getstream` che fa lo stesso lavoro

## 🏗️ Architettura Corretta (Attuale)

### Client IPTV → Xtream → AceStream

```
1. Client richiede stream
   GET /live/username/password/123.ts

2. Xtream verifica autenticazione
   Se channel ha acestream_id:

3. Xtream fa proxy INTERNO
   StreamHelper.receive_stream("http://127.0.0.1:8000/ace/getstream?id=xxx")
   
4. Richiesta HTTP interna a /ace/getstream
   → AceProxyService.stream_content(stream_id)
   
5. AceProxyService fa richiesta ad AceStream Engine
   → http://127.0.0.1:6878/ace/getstream?id=xxx
   
6. Stream chunks tornano:
   AceStream Engine → AceProxyService → StreamHelper → Client
```

## ✅ Perché è Corretto

1. **StreamHelper** fa proxy di TUTTO (come originale)
2. **AceProxyService** è la logica pyacexy integrata
3. **Nessun redirect** al client (proxy interno)
4. **Multiplexing** gestito da AceProxyService
5. **Client non deve conoscere** pyacexy o AceStream

## 🔧 Differenze

| Aspetto | Originale | Unificato |
|---------|-----------|-----------|
| Proxy tutto | ✅ StreamHelper | ✅ StreamHelper |
| AceStream Engine | Chiamata diretta a :6878 | Via AceProxyService |
| Multiplexing | ❌ No | ✅ Sì (AceProxyService) |
| Endpoint /ace/getstream | ❌ Non esiste | ✅ Esiste (AceProxyService) |

## 📝 Conclusione

L'implementazione attuale è **CORRETTA**:

✅ Xtream fa proxy interno a `/ace/getstream`  
✅ `/ace/getstream` usa `AceProxyService` (logica pyacexy)  
✅ `AceProxyService` gestisce multiplexing e buffering  
✅ Tutto tramite `StreamHelper` (come originale)  
✅ Nessun redirect al client  

**La differenza principale**: 
- Originale chiama AceStream Engine direttamente
- Unificato usa AceProxyService che aggiunge multiplexing

Questo è un **miglioramento** rispetto all'originale! 🎉

## 🚀 Implementazione Finale

```python
# Xtream endpoint /live/
if channel.acestream_id:
    # Proxy INTERNO a /ace/getstream (usa AceProxyService)
    stream_url = f"http://127.0.0.1:{config.server_port}/ace/getstream?id={channel.acestream_id}"
    
    # StreamHelper fa la richiesta HTTP interna
    return StreamingResponse(
        StreamHelper.receive_stream(stream_url),
        media_type="video/mp2t"
    )
```

Questo è **esattamente quello che serve**! ✅
