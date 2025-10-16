# Quick Start con Setup Wizard

## Installazione Rapida

### 1. Prerequisiti
```bash
python3 --version  # Python 3.8+
pip3 --version
```

### 2. Installazione
```bash
# Clone repository
git clone <repository-url>
cd unified-iptv-acestream

# Installa dipendenze
pip3 install -r requirements.txt
```

### 3. Setup Interattivo
```bash
python3 setup_wizard.py
```

Il wizard è **interattivo** e ti guiderà passo-passo:

## Cosa ti Chiederà il Wizard

### 🖥️ Configurazione Server
- **Host**: Dove il server ascolta (default: 0.0.0.0 = tutte le interfacce)
- **Porta**: Porta unificata per tutti i servizi (default: 58055)
- **Timezone**: Fuso orario per EPG e log (default: Europe/Rome)
- **Debug Mode**: Abilita logging dettagliato (default: No)

### 📺 Configurazione AceStream
- **Abilitato**: Usa AceStream engine (default: Sì)
- **Engine Host**: Dove gira AceStream (default: localhost)
- **Engine Port**: Porta AceStream (default: 6878)
- **Timeout**: Timeout stream in secondi (default: 15)

**Impostazioni Avanzate** (puoi premere Enter per defaults):
- Streaming host/port interno
- Dimensione chunk (8KB default)
- Timeout vari

### 🔍 Configurazione Scraper
- **URL Playlist**: Lista di URL M3U separati da virgola
  - Esempio: `http://site1.com/list.m3u,http://site2.com/playlist.m3u`
  - Lascia vuoto se non hai playlist
- **Intervallo Aggiornamento**: Quanti secondi tra un update e l'altro (default: 3600 = 1 ora)

### 📅 Configurazione EPG
- **Fonti EPG**: URL separati da virgola (default già configurato)
- **Intervallo Aggiornamento**: Secondi tra update (default: 86400 = 1 giorno)
- **File Cache**: Dove salvare EPG (default: data/epg.xml)

### 💾 Configurazione Database
- **Database URL**: Default SQLite locale
- **Echo SQL**: Mostra query SQL (default: No)
- **Pool Settings**: Connessioni pool (defaults OK per SQLite)

### 👤 Configurazione Admin
- **Username**: Username amministratore (default: admin)
- **Password**: Password amministratore
  - ⚠️ **IMPORTANTE**: Cambia "changeme" in produzione!
  - Minimo 6 caratteri
  - Il wizard ti avviserà se usi password deboli

### 🔐 Configurazione Security
- **Secret Key**: Generata automaticamente (64 bytes sicuri)
- **Token Expiry**: Scadenza token in minuti (default: 43200 = 30 giorni)

## Esempio di Sessione Wizard

```
==============================================================
         Unified IPTV AceStream Setup Wizard
==============================================================

ℹ This wizard will guide you through the initial configuration

» Server Configuration
────────────────────────────────────────────────────────────
ℹ The server will listen on a single unified port
Server host [0.0.0.0]: <Enter>
Server port [58055]: <Enter>
Timezone [Europe/Rome]: <Enter>
Enable debug mode? [y/N]: n

» AceStream Configuration
────────────────────────────────────────────────────────────
Enable AceStream engine? [Y/n]: y
AceStream engine host [localhost]: <Enter>
AceStream engine port [6878]: <Enter>
Stream timeout (seconds) [15]: <Enter>

ℹ Advanced AceStream settings (press Enter to use defaults)
Streaming host [127.0.0.1]: <Enter>
Streaming port [8001]: <Enter>
...

» Scraper Configuration
────────────────────────────────────────────────────────────
ℹ Enter M3U playlist URLs (comma-separated) or leave empty
M3U playlist URLs []: http://myserver.com/channels.m3u
Update interval (seconds) [3600]: <Enter>

...

» Admin User Configuration
────────────────────────────────────────────────────────────
⚠ IMPORTANT: Change these credentials in production!
Admin username [admin]: admin
Admin password [changeme]: MySecurePass123
```

## Dopo il Wizard

### Verifica Configurazione
```bash
cat .env
```

### Avvia Applicazione
```bash
# Metodo 1: Direttamente
python3 main.py

# Metodo 2: Con Docker
docker-compose up -d
```

### Accedi alla Dashboard
```
http://localhost:58055
Username: admin (o quello scelto)
Password: (quella scelta)
```

### Testa Xtream API
```
http://localhost:58055/player_api.php?username=admin&password=XXX
```

## Tips

### 💡 Configurazione Veloce
Premi **Enter** su tutte le domande per usare i defaults sensati.

### 🔄 Ri-esegui Setup
Il wizard chiede conferma se `.env` esiste già. Puoi:
- Sovrascriverlo (ri-configurare tutto)
- Annullare e modificare `.env` manualmente

### ✏️ Modifica Configurazione
Dopo il wizard puoi sempre modificare `.env`:
```bash
nano .env
# Poi riavvia: docker-compose restart
```

### 🔒 Security Checklist
- ✅ Cambia `ADMIN_PASSWORD` da "changeme"
- ✅ `SECRET_KEY` è generata automaticamente (non cambiarla)
- ✅ Dashboard su localhost (127.0.0.1:8000) per sicurezza
- ✅ Usa password complesse (min 12 caratteri, mista)

### 🐛 Troubleshooting

**Wizard si blocca?**
```bash
Ctrl+C
rm .env
python3 setup_wizard.py
```

**Database error?**
```bash
rm data/unified-iptv.db
python3 setup.py
```

**Import errors?**
```bash
pip3 install -r requirements.txt --upgrade
```

## Setup Avanzato

### Configurazione Multi-Instance
Crea più file .env:
```bash
python3 setup_wizard.py  # Crea .env
mv .env .env.production
# Ripeti per altre configurazioni
```

### Environment Variables Override
Il wizard scrive `.env`, ma puoi override via shell:
```bash
export SERVER_PORT=9000
python3 main.py
```

### Backup Configurazione
```bash
# Backup
cp .env .env.backup

# Restore
cp .env.backup .env
```
