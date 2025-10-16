# Importazione Gestione EPG da xtream_api

## Riepilogo

La gestione EPG (Electronic Program Guide) è stata importata con successo dal progetto `xtream_api` al progetto `unified-iptv-acestream`.

## File Importati

### 1. Libreria XMLTV
**Sorgente**: `xtream_api/helper/xmltv.py`  
**Destinazione**: `unified-iptv-acestream/app/utils/xmltv.py`

Libreria Python completa per la gestione del formato XMLTV:
- Lettura e scrittura file XMLTV
- Parser completo per canali e programmi
- Supporto completo DTD XMLTV
- Versione: 1.4.3

### 2. Metodi EPG Avanzati

Aggiunti al servizio EPG esistente in `app/services/epg_service.py`:

#### Metodi Principali

1. **`download_epg(files)`** - Scarica file EPG da URL
2. **`parse_channel(channel, channels_db)`** - Abbina canali XMLTV con database
3. **`parse_programme(programmes)`** - Filtra programmi per canali tracciati
4. **`write_epg(output_file)`** - Genera file XMLTV consolidato
5. **`parse_xml_files(files)`** - Parser asincrono file XMLTV
6. **`update_epg_with_xmltv()`** - Workflow completo aggiornamento EPG
7. **`get_short_epg(channel_id, limit)`** - EPG breve compatibile Xtream API
8. **`get_simple_data_table(channel_id)`** - Tabella EPG completa per canale
9. **`generate_epg_xml(channel_ids)`** - Migliorato con libreria XMLTV

## Funzionalità Chiave

✅ **Supporto Multi-Sorgente**: Scarica e unisce da più fonti XMLTV  
✅ **Decompressione Automatica**: Gestisce file XMLTV compressi gzip  
✅ **Estrazione Icone**: Aggiorna loghi canali dai dati EPG  
✅ **Supporto Cirillico**: Traslitterazione nomi canali cirillici  
✅ **Conformità XMLTV**: Supporto completo specifica DTD XMLTV  
✅ **Compatibilità Xtream API**: Metodi get_short_epg e get_simple_data_table  
✅ **Pretty Printing**: Output XML formattato e leggibile  
✅ **Processing Asincrono**: Aggiornamenti EPG non bloccanti  
✅ **Gestione Errori**: Gestione robusta errori di rete e parsing  

## Configurazione

Nel file `app/config.py`:

```python
# Sorgenti EPG (URL separati da virgola)
epg_sources: str = "https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz"

# Intervallo aggiornamento in secondi (default: 24 ore)
epg_update_interval: int = 86400

# File cache EPG
epg_cache_file: str = "data/epg.xml"

# I file EPG sono compressi gzip
epg_is_gzipped: bool = True
```

## Esempio d'Uso

```python
from app.services.epg_service import EPGService
from app.database import get_db

# Crea istanza servizio
db = next(get_db())
epg_service = EPGService(db)

# Avvia servizio
await epg_service.start()

# Aggiorna EPG usando metodo XMLTV
programs_count = await epg_service.update_epg_with_xmltv()
print(f"Aggiornati {programs_count} programmi")

# Ottieni EPG breve (prossimi 4 programmi)
short_epg = epg_service.get_short_epg(channel_id=123, limit=4)

# Ottieni tabella EPG completa (7 giorni)
full_epg = epg_service.get_simple_data_table(channel_id=123)

# Genera XMLTV per canali specifici
xml_content = epg_service.generate_epg_xml(channel_ids=[1, 2, 3])

# Ferma servizio
await epg_service.stop()
```

## Mappatura EPG ID

Per il funzionamento dell'EPG, i canali nel database devono avere il campo `epg_id` impostato per corrispondere all'ID canale nella sorgente XMLTV:

```python
channel = Channel(
    name="BBC One",
    epg_id="bbc-one.uk",  # Deve corrispondere all'id canale XMLTV
    logo_url="https://example.com/bbc-one.png"
)
```

## Flusso Dati EPG

```
1. Scarica file EPG da sorgenti configurate
   ↓
2. Decomprime file gzip se necessario
   ↓
3. Parser formato XMLTV usando libreria xmltv
   ↓
4. Abbina canali tramite epg_id
   ↓
5. Filtra programmi per canali tracciati
   ↓
6. Aggiorna icone canali se trovate
   ↓
7. Genera output XMLTV consolidato
   ↓
8. Salva in file cache (data/epg.xml)
```

## Struttura File

```
unified-iptv-acestream/
├── app/
│   ├── services/
│   │   └── epg_service.py          # Migliorato con metodi xtream_api
│   └── utils/
│       └── xmltv.py                # Libreria XMLTV (importata)
├── data/
│   ├── epg/                        # File EPG scaricati (temp)
│   └── epg.xml                     # Output EPG consolidato
├── EPG_IMPORT_README.md            # Documentazione completa (inglese)
└── IMPORTAZIONE_EPG.md             # Questo file
```

## Verifica Importazione

Test eseguiti con successo:

```bash
✓ Import libreria XMLTV OK (versione 1.4.3)
✓ Import servizio EPG migliorato OK
✓ Tutti i nuovi metodi disponibili
```

Metodi disponibili nel servizio EPG:
- auto_update_loop
- download_epg ⭐ NUOVO
- fetch_epg_xml
- generate_epg_xml ⭐ MIGLIORATO
- get_current_program
- get_programs
- get_short_epg ⭐ NUOVO
- get_simple_data_table ⭐ NUOVO
- parse_channel ⭐ NUOVO
- parse_epg_xml
- parse_programme ⭐ NUOVO
- parse_xml_files ⭐ NUOVO
- start
- stop
- update_all_epg
- update_epg_from_source
- update_epg_with_xmltv ⭐ NUOVO
- write_epg ⭐ NUOVO

## Dipendenze

Tutte le dipendenze necessarie sono già presenti in `requirements.txt`:
- `unidecode==1.3.7` - Per traslitterazione caratteri cirillici
- `aiohttp` - Per download HTTP asincroni
- `sqlalchemy` - Per operazioni database

## Vantaggi

1. **Conformità agli Standard**: Supporto completo formato XMLTV
2. **Metadati Ricchi**: Supporto per credits, ratings, episodi, ecc.
3. **Migliore Compatibilità Client**: Molti client IPTV richiedono formato XMLTV
4. **Supporto Xtream API**: Compatibile con client Xtream API
5. **Efficiente**: Processa solo i canali tracciati nel database
6. **Flessibile**: Più sorgenti EPG possono essere combinate

## Documentazione

Per documentazione completa e dettagliata, consultare:
- `EPG_IMPORT_README.md` - Documentazione completa in inglese
- Esempi d'uso e troubleshooting
- API reference completa

## Prossimi Passi

L'importazione è completa e pronta all'uso. Funzionalità potenziali future:

1. Sistema priorità/fallback sorgenti EPG
2. Aggiornamenti EPG incrementali
3. API ricerca e filtraggio EPG
4. Notifiche/promemoria programmi
5. Scheduler registrazioni basato su EPG
6. Supporto EPG multilingua

## Crediti

Funzionalità gestione EPG importata dal progetto [xtream_api](../xtream_api), che include:
- Libreria XMLTV basata su XMLTV.pm di James Oakley
- Utility parsing e generazione EPG
- Layer compatibilità Xtream API

---

**Data Importazione**: 12 Ottobre 2025  
**Stato**: ✅ Completato e Testato  
**Versione XMLTV**: 1.4.3
