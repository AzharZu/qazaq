# Docker Configuration Documentation

This directory contains Docker-specific configuration for the Qazaq platform.

## Files

### `nginx.conf`
Nginx reverse proxy configuration that:
- Routes `/api/*` requests to FastAPI backend
- Routes `/admin/*` requests to admin SPA
- Routes `/` requests to student SPA
- Serves uploaded files from `/uploads` volume
- Handles static assets with proper caching
- Manages CORS headers
- Gzip compression enabled

### `init-db.sql`
PostgreSQL initialization script that:
- Creates `qazaq_user` with secure password
- Creates `qazaq_db` database
- Grants proper privileges to user
- Sets UTF-8 encoding
- Runs on first container startup

### `docker-entrypoint.sh`
Backend startup script that:
- Waits for database to be ready
- Applies pending Alembic migrations
- Starts Uvicorn server
- Enables health check endpoint
- Handles graceful shutdown

## Architecture

```
┌─────────────────────────────────────────┐
│        Docker Compose Network           │
│       (qazaq_network: bridge)           │
├──────────┬──────────┬────────┬──────────┤
│          │          │        │          │
│  postgres│ backend  │ nginx  │ admin-spa
│  :5432   │ :8000    │ :80    │ :3001
│  +       │ +        │ +      │
│  volumes │ volumes  │ volumes│ volumes
│          │          │        │
└──────────┴──────────┴────────┴──────────┘

Persistent Volumes:
- postgres_data: /var/lib/postgresql/data
- uploads: /app/uploads (backend) & /uploads (nginx)
```

## Service Communication

### Internal Network Hostnames

Within Docker, services communicate using container names:

```
Backend  ←→  Database: postgres:5432
         ├─→ URL: postgresql://qazaq_user:pass@postgres:5432/qazaq_db

Nginx    ←→  Backend: backend:8000
         ├─→ Admin SPA: admin-spa:80
         └─→ Student SPA: student-spa:80

SPAs     ←→  Backend: /api (via Nginx proxy)
```

### External Access

From host machine:

```
Browser ←→ http://localhost:{port}
             ├─→ localhost:3001 → admin-spa
             ├─→ localhost:3000 → student-spa
             ├─→ localhost:8000 → backend (direct)
             └─→ localhost:80   → nginx (all routes)
```

## Volumes & Data Persistence

### PostgreSQL Data

```
Volume: qazaq_postgres_data
Location: /var/lib/postgresql/data
Backup:
  docker-compose exec postgres pg_dump -U qazaq_user qazaq_db > backup.sql
Restore:
  docker-compose exec postgres psql -U qazaq_user qazaq_db < backup.sql
```

### User Uploads

```
Volume: qazaq_uploads
Backend location: /app/uploads
Nginx location: /uploads
URL path: /uploads/*
Backup:
  docker run --rm -v qazaq_uploads:/data -v $(pwd):/backup \
    alpine cp -r /data /backup/uploads_backup
```

### Application Uploads

Both SPAs upload files via the backend API:

```
POST /api/upload → Backend receives & stores in /app/uploads
GET /uploads/file.ext → Nginx serves from uploads volume
```

## Health Checks

Each service has health checks configured in docker-compose.yml:

### Backend Health Check

```bash
curl http://backend:8000/docs
```

Checks if FastAPI is responding with documentation endpoint.

### Postgres Health Check

```bash
pg_isready -U qazaq_user -d qazaq_db
```

Waits up to 30 seconds for database to be ready.

### Nginx Health Check

Implicit (no health check needed for Nginx unless custom endpoint added).

### Application Health Check

```bash
curl http://localhost/health
```

Returns 200 if all upstream services are responding.

## Logging

### View All Logs

```bash
docker-compose logs -f
```

### View Specific Service Logs

```bash
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f nginx
docker-compose logs -f admin-spa
docker-compose logs -f student-spa
```

### Search Logs

```bash
docker-compose logs | grep ERROR
docker-compose logs backend | grep migration
```

### Real-time Tail

```bash
# Last 100 lines
docker-compose logs --tail=100

# Follow new logs only
docker-compose logs -f --tail=50
```

## Debugging Commands

### Execute Commands in Container

```bash
# Backend Python shell
docker-compose exec backend python

# Backend bash shell
docker-compose exec backend bash

# PostgreSQL shell
docker-compose exec postgres psql -U qazaq_user -d qazaq_db

# View environment variables
docker-compose exec backend env | grep DATABASE
```

### Check Network Connectivity

```bash
# From backend to postgres
docker-compose exec backend python -c \
  "import socket; print(socket.gethostbyname('postgres'))"

# From backend to nginx
docker-compose exec backend curl http://nginx:80/health

# From nginx to backend
docker-compose exec nginx curl http://backend:8000/docs
```

### Inspect Volumes

```bash
# List volumes
docker volume ls | grep qazaq

# Inspect volume
docker volume inspect qazaq_postgres_data
docker volume inspect qazaq_uploads

# Mount volume temporarily
docker run --rm -v qazaq_uploads:/data alpine ls -la /data
```

### Check Image Sizes

```bash
docker images | grep qazaq
# Shows size of each built image
```

## Performance Tuning

### PostgreSQL Configuration

Edit `docker-compose.yml` to add PostgreSQL parameters:

```yaml
postgres:
  environment:
    # Memory
    POSTGRES_INITDB_ARGS: |
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=16MB
      -c maintenance_work_mem=128MB
    # Connection pooling
    - max_connections=100
```

### Nginx Configuration

Already optimized in `nginx.conf`:
- Gzip compression (level 6)
- Client body buffer size: 10M
- Worker connections: 1024
- Keepalive timeout: 65s
- Cache-Control headers for static assets

### Backend Configuration

Uvicorn workers configured in `docker-entrypoint.sh`:

```bash
# Single worker (default)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers (for production)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check port availability
docker port qazaq_postgres

# Test connection
docker-compose exec backend python -c \
  "from sqlalchemy import create_engine; \
   e = create_engine('postgresql+psycopg2://qazaq_user:qazaq_pass@postgres:5432/qazaq_db'); \
   print('Connected!' if e.connect() else 'Failed')"
```

### Port Conflicts

```bash
# Find process using port
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Backend
lsof -i :80    # Nginx
lsof -i :3000  # Student SPA
lsof -i :3001  # Admin SPA

# Kill process (if needed)
kill -9 <PID>
```

### Out of Memory

```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or use memory limits in docker-compose.yml:
services:
  postgres:
    mem_limit: 2g
  backend:
    mem_limit: 1g
```

### Migrations Not Running

```bash
# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Run migrations manually
docker-compose exec backend alembic upgrade head

# View migration SQL (without executing)
docker-compose exec backend alembic upgrade head --sql
```

## Security Best Practices

### Secrets Management

1. Never commit `.env` files
2. Use `.env.example` templates
3. Generate strong keys: `openssl rand -hex 32`
4. Rotate secrets periodically

### Network Security

1. Services communicate via internal bridge network
2. Only Nginx exposes ports to host
3. Database not directly accessible from host
4. Use environment variables for credentials

### Image Security

1. Use specific base image versions (not `latest`)
2. Scan images for vulnerabilities: `docker scan <image>`
3. Keep base images updated
4. Use minimal images (alpine, slim variants)

## Deployment Checklist

- [ ] Verify all `.env` files are created and configured
- [ ] Run `docker-compose build` without errors
- [ ] Run `docker-compose up -d` successfully
- [ ] Check `docker-compose ps` shows all services as healthy
- [ ] Test API endpoint: `curl http://localhost:8000/docs`
- [ ] Test admin panel: `curl http://localhost:3001`
- [ ] Test student app: `curl http://localhost:3000`
- [ ] Verify uploads work through `/uploads` path
- [ ] Test database: `docker-compose exec postgres psql -U qazaq_user -d qazaq_db -c "SELECT 1"`
- [ ] Check logs for errors: `docker-compose logs | grep ERROR`
- [ ] Backup current database before going to production

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/concepts/#containerization)
- [Docker Networking](https://docs.docker.com/network/)

---

**Note**: This configuration is optimized for development and staging. For production, add:
- SSL/TLS certificates
- Secrets management (HashiCorp Vault, etc.)
- Log aggregation (ELK, Splunk, etc.)
- Monitoring (Prometheus, Datadog, etc.)
- Database replication/backup strategy
