# Guida Docker - Unified IPTV AceStream

## 🐳 Quick Start

### 1. Clone e Setup
```bash
git clone <repository-url>
cd unified-iptv-acestream
```

### 2. Configurazione Base
```bash
# Copia esempio
cp .env.example .env

# Modifica almeno queste variabili
nano .env
```

Cambia almeno:
- `ADMIN_PASSWORD` (minimo 8 caratteri)
- `SECRET_KEY` (usa output di: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`)

### 3. Avvia con Docker Compose
```bash
docker-compose up -d
```

### 4. Verifica
```bash
# Controlla logs
docker-compose logs -f

# Health check
curl http://localhost:58055/health
```

## 📦 Docker Compose Configurazione

### Struttura File

```yaml
version: '3.8'

services:
  unified-iptv:
    build: .
    image: unified-iptv-acestream:latest
    container_name: unified-iptv-acestream
    restart: unless-stopped
    
    environment:
      # Tutte le variabili d'ambiente qui
      - SERVER_PORT=58055
      - ADMIN_PASSWORD=changeme123
      # ...
    
    ports:
      - "127.0.0.1:8000:58055"  # Dashboard localhost only
      - "58055:58055"            # Xtream API
      - "8080:8080"              # AceProxy
      - "6878:6878"              # AceStream Engine
    
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

### Porte Esposte

| Porta | Servizio | Accesso | Note |
|-------|----------|---------|------|
| 8000 | Dashboard | Localhost only | Protetta, HTTP Basic Auth |
| 58055 | Xtream API | Pubblico | Per player IPTV |
| 8080 | AceProxy | Pubblico | Stream AceStream |
| 6878 | AceStream Engine | Interno | Non modificare |

### Volumi

```yaml
volumes:
  - ./data:/app/data      # Database, cache
  - ./logs:/app/logs      # Log applicazione
  - ./config:/app/config  # Config files (opzionale)
```

## 🔧 Gestione Container

### Comandi Base

```bash
# Start
docker-compose up -d

# Stop (mantiene container)
docker-compose stop

# Restart
docker-compose restart

# Stop e rimuovi container
docker-compose down

# Stop, rimuovi e cleanup volumi (⚠️ PERDE DATI!)
docker-compose down -v
```

### Logs

```bash
# Tutti i logs (follow)
docker-compose logs -f

# Solo app logs
docker-compose logs -f unified-iptv

# Ultimi 100 righe
docker-compose logs --tail=100

# Logs da timestamp
docker-compose logs --since 2024-01-01T00:00:00
```

### Shell nel Container

```bash
# Bash interattivo
docker-compose exec unified-iptv bash

# Esegui comando singolo
docker-compose exec unified-iptv python3 -c "from app.config import get_config; print(get_config().SERVER_PORT)"

# Python REPL
docker-compose exec unified-iptv python3
```

## 🔄 Update e Rebuild

### Update Codice

```bash
# Pull latest
git pull origin main

# Rebuild immagine
docker-compose build

# Restart con nuova immagine
docker-compose up -d
```

### Force Rebuild

```bash
# Rebuild senza cache
docker-compose build --no-cache

# Ricrea container
docker-compose up -d --force-recreate
```

## 💾 Backup e Restore

### Backup Completo

```bash
#!/bin/bash
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Stop container
docker-compose stop

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Backup config
cp .env $BACKUP_DIR/.env_$DATE
cp docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.yml

# Restart
docker-compose start

echo "Backup completato in $BACKUP_DIR/"
```

### Restore

```bash
# Stop container
docker-compose down

# Restore data
tar -xzf backups/data_20240116_120000.tar.gz

# Restore config
cp backups/.env_20240116_120000 .env

# Restart
docker-compose up -d
```

### Backup Automatico (cron)

```bash
# Aggiungi a crontab
crontab -e

# Backup giornaliero alle 3 AM
0 3 * * * cd /path/to/unified-iptv-acestream && ./backup.sh
```

## 🔍 Troubleshooting

### Container non parte

```bash
# Check status
docker-compose ps

# Logs dettagliati
docker-compose logs

# Verifica configurazione
docker-compose config

# Test sintassi docker-compose.yml
docker-compose config --quiet && echo "OK" || echo "ERRORE"
```

### Problemi di Rete

```bash
# Ispeziona network
docker network inspect unified-iptv-network

# Ricrea network
docker-compose down
docker network prune
docker-compose up -d
```

### Performance Issues

```bash
# Stats in tempo reale
docker stats unified-iptv-acestream

# Limita risorse (docker-compose.yml)
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

### Database Corrotto

```bash
# Backup DB corrotto
cp data/unified-iptv.db data/unified-iptv.db.broken

# Rimuovi DB
rm data/unified-iptv.db

# Ricrea DB
docker-compose exec unified-iptv python3 setup.py
```

## 🚀 Configurazioni Avanzate

### Multi-Instance

```yaml
# docker-compose-instance2.yml
services:
  unified-iptv-2:
    build: .
    container_name: unified-iptv-2
    environment:
      - SERVER_PORT=58056
      - ACESTREAM_STREAMING_PORT=8002
    ports:
      - "58056:58056"
      - "8081:8081"
    volumes:
      - ./data2:/app/data
```

Avvio:
```bash
docker-compose -f docker-compose-instance2.yml up -d
```

### Production Stack con Reverse Proxy

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - unified-iptv
  
  unified-iptv:
    build: .
    expose:
      - "58055"
    environment:
      - SERVER_HOST=0.0.0.0
```

### Resource Limits

```yaml
services:
  unified-iptv:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # Ulimits
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

## 📊 Monitoring

### Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:58055/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Prometheus Metrics (futuro)

```yaml
services:
  unified-iptv:
    environment:
      - ENABLE_METRICS=true
      - METRICS_PORT=9090
    ports:
      - "9090:9090"
```

## 🔐 Security Best Practices

### 1. Non esporre Dashboard pubblicamente

```yaml
ports:
  - "127.0.0.1:8000:58055"  # Solo localhost
```

### 2. Usa secrets per credentials

```yaml
secrets:
  admin_password:
    file: ./secrets/admin_password.txt

services:
  unified-iptv:
    secrets:
      - admin_password
    environment:
      - ADMIN_PASSWORD_FILE=/run/secrets/admin_password
```

### 3. Network Isolation

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  unified-iptv:
    networks:
      - backend
  
  nginx:
    networks:
      - frontend
      - backend
```

### 4. Read-only Filesystem

```yaml
services:
  unified-iptv:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

## 📝 Variabili d'Ambiente File

Invece di inserire tutte le variabili in `docker-compose.yml`, usa `.env`:

```yaml
services:
  unified-iptv:
    env_file:
      - .env
```

`.env`:
```env
SERVER_PORT=58055
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme123
SECRET_KEY=your-secret-key-here
```

**⚠️ Importante**: Aggiungi `.env` a `.gitignore`!
