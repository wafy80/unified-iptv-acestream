# 📋 Deployment Checklist

Checklist completa per il deployment della piattaforma IPTV unificata.

## ✅ Pre-Deployment

### Requisiti Sistema
- [ ] Python 3.11+ installato
- [ ] Docker e Docker Compose (se deployment Docker)
- [ ] 2GB RAM minimo (4GB raccomandato)
- [ ] 10GB spazio disco
- [ ] Porte disponibili: 58055, 8080, 6878

### Requisiti Rete
- [ ] IP statico o DDNS configurato
- [ ] Firewall configurato per porte necessarie
- [ ] AceStream Engine accessibile (locale o remoto)

### Prerequisiti Software
- [ ] Git (per clone repository)
- [ ] SQLite3 (incluso in Python)
- [ ] curl/wget per testing

## 🔧 Setup Iniziale

### 1. Clone e Preparazione
```bash
- [ ] git clone <repository>
- [ ] cd unified-iptv-acestream
- [ ] chmod +x setup.py
```

### 2. Configurazione Ambiente
```bash
- [ ] python3 setup.py  # Wizard setup
# OPPURE
- [ ] cp .env.example .env
- [ ] nano .env  # Edita configurazioni
```

### 3. Configurazioni Critiche
- [ ] ADMIN_USERNAME configurato
- [ ] ADMIN_PASSWORD impostata (forte!)
- [ ] SECRET_KEY generata (lunga e casuale)
- [ ] SERVER_XTREAM_PORT configurata
- [ ] ACESTREAM_ENGINE_HOST/PORT corretti

### 4. Fonti Dati
- [ ] SCRAPER_URLS configurate
- [ ] EPG_SOURCES configurate
- [ ] Test manuale delle URL (curl)

## 🐳 Deployment Docker

### Build e Run
```bash
- [ ] docker-compose build
- [ ] docker-compose up -d
- [ ] docker-compose logs -f  # Verifica avvio
```

### Verifica Container
```bash
- [ ] docker ps  # Container running?
- [ ] docker-compose exec unified-iptv ps aux
- [ ] curl http://localhost:58055/health
```

### Volumes
- [ ] Volume data/ montato correttamente
- [ ] Volume logs/ accessibile
- [ ] Volume config/ persistente
- [ ] Permissions corrette (chown se necessario)

## 🔌 Deployment Manuale

### Virtual Environment
```bash
- [ ] python3 -m venv venv
- [ ] source venv/bin/activate
- [ ] pip install -r requirements.txt
```

### Directory Structure
```bash
- [ ] mkdir -p data logs config
- [ ] chmod 755 data logs config
```

### Service Setup (systemd)
```bash
- [ ] Crea /etc/systemd/system/unified-iptv.service
- [ ] systemctl daemon-reload
- [ ] systemctl enable unified-iptv
- [ ] systemctl start unified-iptv
- [ ] systemctl status unified-iptv
```

Esempio systemd service:
```ini
[Unit]
Description=Unified IPTV Platform
After=network.target

[Service]
Type=simple
User=iptv
WorkingDirectory=/opt/unified-iptv-acestream
Environment="PATH=/opt/unified-iptv-acestream/venv/bin"
ExecStart=/opt/unified-iptv-acestream/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🔐 Sicurezza

### Password e Keys
- [ ] Admin password cambiata dal default
- [ ] SECRET_KEY generata casualmente
- [ ] Password utenti forti (min 8 caratteri)
- [ ] Credenziali non in repository Git

### Firewall
```bash
- [ ] ufw allow 58055/tcp  # Xtream API
- [ ] ufw allow 8080/tcp   # AceProxy (solo se pubblico)
- [ ] ufw enable
```

### SSL/TLS (Reverse Proxy)
- [ ] Nginx/Apache configurato come reverse proxy
- [ ] Certificato SSL installato (Let's Encrypt)
- [ ] Redirect HTTP → HTTPS
- [ ] Headers di sicurezza configurati

Esempio nginx:
```nginx
server {
    listen 443 ssl http2;
    server_name iptv.example.com;
    
    ssl_certificate /etc/letsencrypt/live/iptv.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iptv.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:58055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Access Control
- [ ] Limitare accesso admin da IP specifici
- [ ] Rate limiting configurato
- [ ] Fail2ban per protezione brute-force (opzionale)

## 📊 Testing

### Health Checks
```bash
- [ ] curl http://localhost:58055/health
- [ ] curl http://localhost:58055/
- [ ] curl http://localhost:6878/webui/api/service?method=get_version
```

### API Testing
```bash
# User info
- [ ] curl "http://localhost:58055/player_api.php?username=admin&password=PASSWORD"

# Categories
- [ ] curl "http://localhost:58055/player_api.php?username=admin&password=PASSWORD&action=get_live_categories"

# Streams
- [ ] curl "http://localhost:58055/player_api.php?username=admin&password=PASSWORD&action=get_live_streams"

# M3U
- [ ] curl "http://localhost:58055/get.php?username=admin&password=PASSWORD" | head -20

# EPG
- [ ] curl "http://localhost:58055/xmltv.php" | head -20
```

### Database Verification
```bash
- [ ] sqlite3 data/unified-iptv.db ".tables"
- [ ] sqlite3 data/unified-iptv.db "SELECT COUNT(*) FROM users;"
- [ ] sqlite3 data/unified-iptv.db "SELECT COUNT(*) FROM channels;"
```

### Player Testing
- [ ] IPTV Smarters configurato e funzionante
- [ ] Perfect Player testato
- [ ] VLC playlist caricata
- [ ] Almeno 1 canale riproduce correttamente

## 🔄 Inizializzazione Dati

### Scraping Iniziale
```bash
- [ ] Verifica SCRAPER_URLS in .env
- [ ] Attendi primo scraping automatico (check logs)
# OPPURE forza manualmente:
- [ ] curl -X POST http://localhost:58055/api/scraper/refresh
```

### EPG Setup
```bash
- [ ] Verifica EPG_SOURCES in .env
- [ ] Attendi primo download EPG
- [ ] Verifica EPG in database:
      sqlite3 data/unified-iptv.db "SELECT COUNT(*) FROM epg_programs;"
```

### Utenti
```bash
# Admin già creato automaticamente
- [ ] Verifica admin: sqlite3 data/unified-iptv.db "SELECT * FROM users WHERE is_admin=1;"

# Crea utenti aggiuntivi (opzionale)
- [ ] python scripts/create_user.py
```

## 📈 Monitoring Setup

### Logs
```bash
- [ ] Verifica logs/app.log esiste
- [ ] Configura log rotation (logrotate)
- [ ] Setup monitoring logs (Grafana Loki, ELK, etc.)
```

Logrotate config (`/etc/logrotate.d/unified-iptv`):
```
/opt/unified-iptv-acestream/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 iptv iptv
    sharedscripts
    postrotate
        systemctl reload unified-iptv
    endscript
}
```

### Health Monitoring
- [ ] Prometheus metrics endpoint (future)
- [ ] Uptime monitoring (UptimeRobot, Pingdom)
- [ ] Alert setup per downtime

### Performance Monitoring
- [ ] Monitor CPU/RAM usage
- [ ] Monitor disk space
- [ ] Monitor network bandwidth
- [ ] Database size monitoring

## 💾 Backup Setup

### Database Backup
```bash
- [ ] Crea script backup automatico
- [ ] Configura cron per backup giornaliero
- [ ] Test restore da backup
- [ ] Backup remoto (S3, FTP, etc.)
```

Script backup (`/opt/scripts/backup-iptv.sh`):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/iptv"
DB_PATH="/opt/unified-iptv-acestream/data/unified-iptv.db"

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup $BACKUP_DIR/backup_${DATE}.db"
gzip $BACKUP_DIR/backup_${DATE}.db

# Mantieni solo ultimi 30 giorni
find $BACKUP_DIR -name "backup_*.db.gz" -mtime +30 -delete

echo "Backup completed: backup_${DATE}.db.gz"
```

Cron job:
```bash
- [ ] crontab -e
# Aggiungi: 0 2 * * * /opt/scripts/backup-iptv.sh
```

### Config Backup
```bash
- [ ] Backup .env file (senza committerlo!)
- [ ] Backup config/ directory
- [ ] Documenta configurazioni custom
```

## 🚀 Go Live

### Pre-Launch
- [ ] Tutti i test passati
- [ ] Backup configurato e testato
- [ ] Monitoring attivo
- [ ] Documentazione aggiornata
- [ ] Credenziali sicure

### Launch
- [ ] Riavvia servizio (fresh start)
- [ ] Monitor logs per primi 30 minuti
- [ ] Test con utenti reali
- [ ] Verifica performance sotto carico

### Post-Launch
- [ ] Monitor per prime 24 ore
- [ ] Raccogli feedback utenti
- [ ] Documenta problemi riscontrati
- [ ] Pianifica manutenzione

## 📱 Comunicazione Utenti

### Istruzioni Setup
- [ ] Crea guida per utenti finali
- [ ] Include screenshots
- [ ] Testa istruzioni con utente non tecnico
- [ ] Fornisci supporto durante onboarding

### Info da Fornire
- [ ] Server URL: `http://YOUR-SERVER:58055`
- [ ] Username personale
- [ ] Password temporanea
- [ ] Link guide setup player
- [ ] Contatti supporto

## 🔧 Manutenzione

### Giornaliera
- [ ] Check logs per errori
- [ ] Verifica disponibilità servizio
- [ ] Monitor utilizzo risorse

### Settimanale
- [ ] Review canali attivi/inattivi
- [ ] Pulizia canali non funzionanti
- [ ] Verifica EPG aggiornata
- [ ] Check backup funzionanti

### Mensile
- [ ] Aggiornamento dipendenze
- [ ] Review utenti e scadenze
- [ ] Ottimizzazione database (VACUUM)
- [ ] Test disaster recovery

### Comandi Manutenzione
```bash
# Cleanup EPG vecchia
- [ ] sqlite3 data/unified-iptv.db "DELETE FROM epg_programs WHERE end_time < datetime('now', '-7 days');"

# Vacuum database
- [ ] sqlite3 data/unified-iptv.db "VACUUM;"

# Update statistics
- [ ] sqlite3 data/unified-iptv.db "ANALYZE;"

# Check channel status
- [ ] python scripts/check_channels.py
```

## 🆘 Troubleshooting Checklist

### Servizio Non Si Avvia
- [ ] Check logs: `tail -f logs/app.log`
- [ ] Verifica porte disponibili: `netstat -tulpn | grep -E "58055|6878|8080"`
- [ ] Verifica dipendenze: `pip list`
- [ ] Test configurazione: `python -c "from app.config import get_config; print(get_config())"`

### API Non Risponde
- [ ] Check health: `curl http://localhost:58055/health`
- [ ] Verifica processo running: `ps aux | grep python`
- [ ] Check firewall: `ufw status`
- [ ] Review nginx logs (se reverse proxy)

### Canali Non Appaiono
- [ ] Verifica scraper URLs: `cat .env | grep SCRAPER`
- [ ] Check database: `sqlite3 data/unified-iptv.db "SELECT COUNT(*) FROM channels;"`
- [ ] Force refresh: restart service
- [ ] Check scraper logs

### Stream Non Parte
- [ ] Test AceStream Engine: `curl http://localhost:6878/webui/api/service?method=get_version`
- [ ] Verifica AceStream ID valido
- [ ] Check AceProxy: `curl http://localhost:8080/ace/status`
- [ ] Review stream logs

### EPG Mancante
- [ ] Verifica EPG sources: `cat .env | grep EPG`
- [ ] Check download: `ls -lh data/epg.xml`
- [ ] Test fonte EPG: `curl -I <EPG_URL>`
- [ ] Force update: restart service

## ✅ Final Checklist

### Production Ready
- [ ] Tutte le configurazioni verificate
- [ ] Sicurezza implementata (SSL, passwords, firewall)
- [ ] Backup automatici funzionanti
- [ ] Monitoring attivo
- [ ] Documentazione completa
- [ ] Team training completato
- [ ] Supporto utenti organizzato
- [ ] Disaster recovery plan documentato
- [ ] Performance testata sotto carico
- [ ] Tutti i test passati

### Sign-Off
- [ ] Technical Lead approval
- [ ] Security review passed
- [ ] Documentation complete
- [ ] Backup verified
- [ ] Monitoring confirmed
- [ ] Support ready

---

**🎉 Deployment Completato!**

Monitora il servizio per le prime 24-48 ore e raccogli feedback dagli utenti.

**Buona fortuna! 🚀**
