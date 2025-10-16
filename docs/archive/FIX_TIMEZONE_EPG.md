# Fix Timezone EPG - Documentazione

## Problema Risolto

L'EPG non teneva conto del timezone originale delle sorgenti XMLTV. Tutti i timestamp venivano impostati a `+0000` (UTC) anche quando la sorgente EPG originale aveva un timezone diverso (es. `+0300`), causando uno shift di N ore nei programmi visualizzati.

### Esempio del Problema

**Prima del fix**:
- Sorgente XMLTV: `20251013150000 +0300` (15:00 in timezone +03:00)
- Parsing: Ignorava `+0300`, creava datetime `2025-10-13 15:00:00` (assumendo UTC)
- Storage DB: `2025-10-13 15:00:00` (UTC errato, avrebbe dovuto essere 12:00 UTC)
- Output XMLTV: `20251013150000 +0000` (15:00 UTC, 3 ore in ritardo!)

**Dopo il fix**:
- Sorgente XMLTV: `20251013150000 +0300` (15:00 in timezone +03:00)
- Parsing: Riconosce `+0300`, converte a UTC
- Storage DB: `2025-10-13 12:00:00` (UTC corretto)
- Output XMLTV: `20251013140000 +0200` (14:00 in Europe/Rome, corretto!)

## Modifiche Implementate

### File Modificato: `app/services/epg_service.py`

#### 1. Aggiunto Import per Timezone
```python
from datetime import datetime, timedelta, timezone
import re
```

#### 2. Nuovo Metodo: `parse_xmltv_timestamp()`

Metodo per parsing corretto dei timestamp XMLTV con supporto timezone.

**Funzionalità**:
- Supporta formato XMLTV: `YYYYMMDDHHmmss +ZZZZ`
- Riconosce vari formati timezone: `+0300`, `+03:00`, `-0500`, etc.
- Converte automaticamente a UTC per storage database
- Gestisce timestamp senza timezone (assume UTC)

**Codice**:
```python
def parse_xmltv_timestamp(self, timestamp_str: str) -> Optional[datetime]:
    """
    Parse XMLTV timestamp with timezone support
    Format: YYYYMMDDHHmmss +ZZZZ or YYYYMMDDHHmmss
    
    Examples:
    - 20251013120000 +0300 -> 2025-10-13 12:00:00+03:00 -> converted to UTC
    - 20251013120000 -> 2025-10-13 12:00:00 UTC
    """
    try:
        # Extract date/time and timezone parts
        dt_part = timestamp_str[:14].strip()
        tz_part = timestamp_str[14:].strip()
        
        # Parse base datetime
        dt = datetime.strptime(dt_part, '%Y%m%d%H%M%S')
        
        if tz_part:
            # Parse timezone offset (+0300, -0500, etc.)
            tz_match = re.match(r'([+-])(\d{2}):?(\d{2})?', tz_part)
            if tz_match:
                sign = 1 if tz_match.group(1) == '+' else -1
                hours = int(tz_match.group(2))
                minutes = int(tz_match.group(3) or '0')
                
                # Create timezone-aware datetime
                offset = timedelta(hours=sign * hours, minutes=sign * minutes)
                tz = timezone(offset)
                dt = dt.replace(tzinfo=tz)
                
                # Convert to UTC
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        return dt
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None
```

#### 3. Modificato: `parse_epg_xml()`

Ora usa il nuovo metodo per parsing timestamp.

**Prima**:
```python
try:
    start_dt = datetime.strptime(start[:14], '%Y%m%d%H%M%S')  # Ignorava timezone!
    stop_dt = datetime.strptime(stop[:14], '%Y%m%d%H%M%S')
except Exception:
    continue
```

**Dopo**:
```python
# Parse datetime with timezone support
start_dt = self.parse_xmltv_timestamp(start)
stop_dt = self.parse_xmltv_timestamp(stop)

if not start_dt or not stop_dt:
    continue
```

#### 4. Modificato: `generate_epg_xml()`

Genera XMLTV con timezone corretto basato sulla configurazione server.

**Funzionalità**:
- Usa `server_timezone` dalla configurazione (default: `Europe/Rome`)
- Converte timestamp UTC dal database al timezone locale
- Genera XMLTV con offset timezone corretto (es. `+0200`)

**Prima**:
```python
programme_data = {
    "start": program.start_time.strftime('%Y%m%d%H%M%S +0000'),  # Sempre UTC!
    "stop": program.end_time.strftime('%Y%m%d%H%M%S +0000'),
    ...
}
```

**Dopo**:
```python
from zoneinfo import ZoneInfo

# Get server timezone
server_tz = ZoneInfo(self.config.server_timezone)

# Convert UTC times from database to server timezone
start_utc = program.start_time.replace(tzinfo=timezone.utc)
stop_utc = program.end_time.replace(tzinfo=timezone.utc)

start_local = start_utc.astimezone(server_tz)
stop_local = stop_utc.astimezone(server_tz)

# Format with timezone offset
start_str = start_local.strftime('%Y%m%d%H%M%S %z')
stop_str = stop_local.strftime('%Y%m%d%H%M%S %z')

programme_data = {
    "start": start_str,  # Es. 20251013140000 +0200
    "stop": stop_str,
    ...
}
```

## Configurazione

### Timezone Server

Il timezone per l'output XMLTV si configura in `.env`:

```bash
# Timezone del server (default: Europe/Rome)
SERVER_TIMEZONE=Europe/Rome
```

Timezone supportati (esempi):
- `Europe/Rome` - Italia (+01:00/+02:00 DST)
- `Europe/London` - UK (+00:00/+01:00 DST)
- `America/New_York` - EST/EDT (-05:00/-04:00)
- `UTC` - Coordinated Universal Time (+00:00)
- `Europe/Moscow` - Moscow (+03:00)

Lista completa: [IANA Time Zone Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## Flusso Dati Completo

### 1. Import EPG (parse_epg_xml)

```
Sorgente XMLTV
    ↓
"20251013150000 +0300" (15:00 Moscow time)
    ↓
parse_xmltv_timestamp()
    ↓
Riconosce timezone +0300
    ↓
Crea datetime con timezone: 2025-10-13 15:00:00+03:00
    ↓
Converte a UTC: 2025-10-13 12:00:00
    ↓
Storage Database (UTC): 2025-10-13 12:00:00
```

### 2. Export EPG (generate_epg_xml)

```
Database (UTC): 2025-10-13 12:00:00
    ↓
Legge configurazione: SERVER_TIMEZONE=Europe/Rome
    ↓
Converte UTC → Local: 2025-10-13 12:00:00 UTC → 14:00:00 +02:00
    ↓
Formatta XMLTV: "20251013140000 +0200"
    ↓
Output XMLTV (Rome time)
```

## Test

### Test Parsing

```python
from app.services.epg_service import EPGService

# Test timezone parsing
service = EPGService(db)

# Moscow time (+0300)
result = service.parse_xmltv_timestamp("20251013150000 +0300")
print(result)  # 2025-10-13 12:00:00 (UTC)

# EST time (-0500)
result = service.parse_xmltv_timestamp("20251013120000 -0500")
print(result)  # 2025-10-13 17:00:00 (UTC)

# No timezone (assume UTC)
result = service.parse_xmltv_timestamp("20251013120000")
print(result)  # 2025-10-13 12:00:00 (UTC)
```

### Test Generazione

```bash
# Genera XMLTV con timezone corretto
curl "http://localhost:8000/xmltv.php?username=admin&password=changeme" > epg.xml

# Verifica timestamp
grep 'programme start=' epg.xml | head -5

# Output esempio:
# <programme start="20251013140000 +0200" stop="20251013150000 +0200">
```

### Verifica Conversione

```python
# Scenario: Programma in sorgente EPG a 15:00 +0300
# Server timezone: Europe/Rome (+0200)

# 1. Parsing: 15:00 +0300 → 12:00 UTC (corretto)
# 2. Storage: 12:00 UTC nel database
# 3. Output: 12:00 UTC → 14:00 +0200 (corretto per Roma)

# Il programma che iniziava alle 15:00 ora di Mosca
# viene mostrato alle 14:00 ora di Roma
# che è l'orario corretto!
```

## Benefici

✅ **Timestamp Corretti**: I programmi vengono mostrati all'orario corretto  
✅ **Supporto Multi-Timezone**: Gestisce sorgenti EPG da diversi fusi orari  
✅ **Conversione Automatica**: UTC nel database, timezone locale nell'output  
✅ **Configurabile**: Timezone output configurabile via environment  
✅ **Backward Compatible**: Gestisce anche timestamp senza timezone  
✅ **Standard Compliant**: Segue le specifiche XMLTV per timezone  

## Casi d'Uso

### Sorgente EPG Russa (+0300)

```xml
<!-- Sorgente originale -->
<programme start="20251013150000 +0300" ...>
  <title>Новости</title>
</programme>
```

**Storage DB**: `2025-10-13 12:00:00 UTC`

**Output per utenti italiani** (Europe/Rome +0200):
```xml
<programme start="20251013140000 +0200" ...>
  <title>Новости</title>
</programme>
```

**Risultato**: Il programma che va in onda alle 15:00 a Mosca viene mostrato alle 14:00 agli utenti in Italia ✅

### Sorgente EPG Americana (-0500)

```xml
<!-- Sorgente originale -->
<programme start="20251013200000 -0500" ...>
  <title>Evening News</title>
</programme>
```

**Storage DB**: `2025-10-14 01:00:00 UTC`

**Output per utenti italiani** (Europe/Rome +0200):
```xml
<programme start="20251014030000 +0200" ...>
  <title>Evening News</title>
</programme>
```

**Risultato**: Il programma delle 20:00 EST viene mostrato alle 03:00 del giorno dopo in Italia ✅

## Risoluzione Problemi

### EPG ancora spostato

1. Verifica timezone configurato:
```bash
curl "http://localhost:8000/epg/status?username=admin&password=changeme" | jq
```

2. Controlla log durante import:
```bash
tail -f logs/app.log | grep "parse_xmltv_timestamp"
```

3. Trigger nuovo aggiornamento EPG:
```bash
curl -X POST "http://localhost:8000/epg/update?username=admin&password=changeme"
```

### Timezone non valido

Se il timezone configurato non è valido:
```
WARNING: Invalid timezone 'Invalid/Timezone', using UTC
```

Usa un timezone valido dalla [lista IANA](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

### Client IPTV ignora timezone

Alcuni client potrebbero ignorare il timezone XMLTV. Verifica la documentazione del client o configura il timezone manualmente nel client.

## Dipendenze

Nessuna nuova dipendenza richiesta. Usa moduli Python standard:
- `datetime.timezone` - Gestione timezone
- `zoneinfo.ZoneInfo` - Database timezone IANA (Python 3.9+)
- `re` - Regex per parsing timezone

## Conclusione

Il fix risolve completamente il problema del timezone EPG:

✅ **Import**: Riconosce e converte correttamente i timezone XMLTV  
✅ **Storage**: Memorizza tutto in UTC nel database  
✅ **Export**: Genera XMLTV con timezone configurato per il server  
✅ **Risultato**: Gli utenti vedono i programmi all'orario corretto locale  

---

**Data Fix**: 13 Ottobre 2025  
**Versione**: unified-iptv-acestream v1.1  
**Issue**: Timezone EPG non gestito correttamente  
**Status**: ✅ RISOLTO
