# Documentazione Principale

## Documentazione Essenziale (Root)
- **README.md** - Guida principale del progetto
- **SECURITY_UPDATE.md** - Aggiornamenti sicurezza dashboard
- **docker-compose.yml** - Configurazione deployment
- **Dockerfile** - Build container
- **.env.example** - Template configurazione

## Documentazione Archiviata
Tutta la documentazione di sviluppo, fix, changelog e test è stata spostata in:
- `docs/archive/` - Documentazione storica/di sviluppo
- `tests/` - Script di test e setup

## Guide Rapide

### Avvio Rapido
```bash
cp .env.example .env
# Modificare .env con le tue configurazioni
docker-compose up -d
```

### Accesso Dashboard
- URL: http://localhost:8000 (solo da localhost)
- Username: (vedi ADMIN_USERNAME in .env)
- Password: (vedi ADMIN_PASSWORD in .env)

### Xtream API
- Porta: 58055
- URL: http://your-server:58055/player_api.php

### AceProxy
- Porta: 8080
- URL: http://your-server:8080/ace/getstream?id={infohash}
