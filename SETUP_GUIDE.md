# 🚀 Qazaq Production Deployment - Complete Setup Guide

Complete, production-ready Docker deployment for the Qazaq EdTech platform.

## 📚 Documentation Overview

This repository now includes comprehensive deployment documentation:

1. **DOCKER_DEPLOYMENT.md** - Complete Docker deployment guide with architecture, quick start, configuration, troubleshooting
2. **DEPLOYMENT_CHECKLIST.md** - Pre-deployment verification, step-by-step deployment, post-deployment tests, maintenance tasks, rollback procedures
3. **docker/readme.md** - Docker-specific configuration details, service communication, debugging, performance tuning
4. **quickstart.sh** - Automated setup script (builds, starts services, verifies health)
5. **health-check.sh** - Monitoring script (service status, health checks, resource usage, recommendations)

## 🎯 Quick Start (5 Minutes)

```bash
# 1. Navigate to project directory
cd /Users/sanzar/Desktop/qazaq

# 2. Run quickstart script (handles everything)
./quickstart.sh

# 3. Access the platform
# Admin: http://localhost:3001
# Student: http://localhost:3000
# API Docs: http://localhost:8000/docs

# 4. Monitor system health
./health-check.sh watch
```

## ✅ What's Been Setup

### ✨ Docker Infrastructure
- **docker-compose.yml** - 5-service orchestration (PostgreSQL, FastAPI, Nginx, Admin SPA, Student SPA)
- **backend/Dockerfile** - Multi-stage build with health checks
- **admin-spa/Dockerfile** - Node.js → Nginx serve
- **student-spa/Dockerfile** - Node.js → Nginx serve (NEW)
- **docker/nginx.conf** - Reverse proxy with all routing configured
- **docker/init-db.sql** - PostgreSQL initialization with proper permissions
- **docker-entrypoint.sh** - Backend startup with migrations

### 🔧 Configuration Files
- **backend/.env.example** - Template with all required variables
- **admin-spa/.env.example** - Frontend configuration template
- **student-spa/.env.example** - Frontend configuration template
- **.gitignore** - Updated to exclude `.env` files

### 📖 Documentation
- **DOCKER_DEPLOYMENT.md** - 500+ lines of deployment docs
- **DEPLOYMENT_CHECKLIST.md** - 600+ lines of checklist & troubleshooting
- **docker/readme.md** - 400+ lines of Docker-specific docs
- **SETUP_GUIDE.md** - This file

### 🛠️ Utility Scripts
- **quickstart.sh** - One-command deployment setup
- **health-check.sh** - Real-time system monitoring

## 🏗️ Architecture

```
Internet (User Browser)
        ↓
   Port 80 (Nginx)
        ↓
   ┌────────────────────┐
   │  Nginx Proxy       │
   │  (Container)       │
   ├────────────────────┤
   │ Routes:            │
   │ /api/*  → Backend  │
   │ /admin/*→ Admin SPA│
   │ /*      → Student  │
   │ /uploads→ Volumes  │
   └────────────────────┘
        ↓
   ┌─────────────────────────────────────┐
   │   Docker Network (qazaq_network)    │
   ├─────────────────────────────────────┤
   │  Backend    │  Admin SPA │ Student  │
   │ :8000       │    :80     │   SPA    │
   │ FastAPI     │  Nginx     │  :80     │
   │ + Alembic   │  Serve     │ Nginx    │
   │ Migrations  │  React     │ Serve    │
   └─────────────────────────────────────┘
             ↓
   ┌────────────────────┐
   │  PostgreSQL 15     │
   │  :5432             │
   │  (Data)            │
   └────────────────────┘

Volumes:
- postgres_data: /var/lib/postgresql/data
- uploads: /app/uploads (backend) → /uploads (nginx)

⚠️ `docker compose down` безопасно останавливает сервисы; `docker compose down -v` удаляет named volumes (включая postgres_data) и очищает данные базы.
```

## 📋 Files Created/Modified

### Created (NEW)
```
✨ student-spa/Dockerfile             (Frontend for students)
✨ docker/nginx.conf                  (Reverse proxy config)
✨ docker/init-db.sql                 (PostgreSQL init)
✨ docker-entrypoint.sh               (Backend startup)
✨ backend/.env.example               (Config template)
✨ admin-spa/.env.example             (Config template)
✨ student-spa/.env.example           (Config template)
✨ DOCKER_DEPLOYMENT.md               (500+ line guide)
✨ DEPLOYMENT_CHECKLIST.md            (600+ line checklist)
✨ docker/readme.md                   (400+ line docs)
✨ SETUP_GUIDE.md                     (This file)
✨ quickstart.sh                      (Automated setup)
✨ health-check.sh                    (System monitoring)
```

### Updated
```
✓ docker-compose.yml                 (Production-ready, 5 services)
✓ backend/Dockerfile                 (Health checks, entrypoint)
✓ .gitignore                          (Exclude .env files)
```

### Verified
```
✓ backend/app/main.py                (FastAPI setup correct)
✓ backend/app/core/config.py         (Pydantic config correct)
✓ backend/app/db/session.py          (URL conversion correct)
✓ admin-spa/src/services/AuthService.js  (API URLs correct)
✓ Alembic migrations                 (Working correctly)
```

## 🚀 Deployment Process

### Phase 1: Pre-Deployment (5 min)
```bash
# ✓ Environment configuration
cp backend/.env.example backend/.env
# Edit backend/.env with your values

cp admin-spa/.env.example admin-spa/.env.local
cp student-spa/.env.example student-spa/.env.local
```

### Phase 2: Build (5-10 min)
```bash
# ✓ Build all Docker images
docker-compose build
```

### Phase 3: Deploy (2-3 min)
```bash
# ✓ Start all services
docker-compose up -d

# ✓ Wait for health checks to pass
docker-compose ps
# All should show "healthy" or "up"
```

### Phase 4: Verify (2-3 min)
```bash
# ✓ Test all endpoints
./health-check.sh

# ✓ Access applications
# http://localhost:3001 (admin)
# http://localhost:3000 (student)
# http://localhost:8000/docs (API)
```

## 🔐 Security Configuration

### Already Handled
✅ Database credentials in environment variables  
✅ API keys in environment variables  
✅ Session cookies with HttpOnly flag  
✅ CORS restricted by default  
✅ Secrets excluded from git  

### For Production Add:
- [ ] SSL/TLS certificates (Let's Encrypt)
- [ ] Secrets management (Vault, AWS Secrets Manager)
- [ ] Rate limiting (Nginx)
- [ ] WAF rules (Cloud CDN)
- [ ] DDoS protection (Cloudflare)
- [ ] Regular security scans

## 💾 Backup & Recovery

### Backup Database
```bash
docker-compose exec postgres pg_dump -U qazaq_user qazaq_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Backup Uploads
```bash
docker run --rm -v qazaq_uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz /data
```

### Backup Everything
```bash
# Add to crontab for automatic daily backups
0 2 * * * cd /Users/sanzar/Desktop/qazaq && \
  docker-compose exec postgres pg_dump -U qazaq_user qazaq_db > backup_$(date +\%Y\%m\%d).sql
```

## 🔄 Common Operations

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f nginx
```

### Database Shell
```bash
docker-compose exec postgres psql -U qazaq_user -d qazaq_db
```

### Backend Shell
```bash
docker-compose exec backend bash
```

### Restart a Service
```bash
docker-compose restart backend
docker-compose restart postgres
docker-compose restart nginx
```

### Apply New Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Scale Backend (if multiple workers)
```bash
docker-compose up -d --scale backend=3
```

## ⚠️ Troubleshooting

### Services Won't Start
```bash
# 1. Check logs
docker-compose logs

# 2. Verify .env files exist
ls backend/.env admin-spa/.env.local student-spa/.env.local

# 3. Check Docker is running
docker ps
```

### API Returns 500 Errors
```bash
# 1. Check backend logs
docker-compose logs backend

# 2. Check database connection
docker-compose exec backend python -c \
  "from app.db.session import SessionLocal; db = SessionLocal(); print('OK')"

# 3. Check migrations
docker-compose exec backend alembic current
```

### Frontend Shows Blank Page
```bash
# 1. Check browser console (F12)
# Should show API calls to http://localhost:8000

# 2. Check Nginx logs
docker-compose logs nginx

# 3. Verify env.local files have VITE_API_URL=/api
cat admin-spa/.env.local
cat student-spa/.env.local
```

### Database Issues
```bash
# Check connections
docker-compose exec postgres psql -U qazaq_user -d qazaq_db -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose exec postgres psql -U qazaq_user -d qazaq_db -c \
  "SELECT pg_size_pretty(pg_database.datsize) FROM pg_database WHERE datname='qazaq_db';"
```

## 📊 Monitoring

### Real-time Status
```bash
./health-check.sh watch
```

### Container Metrics
```bash
docker stats
```

### Historical Logs
```bash
# Last hour
docker-compose logs --since 1h

# Search for errors
docker-compose logs | grep ERROR
```

## 🔄 Update Procedure

### Update Code
```bash
git pull origin main
```

### Rebuild Services
```bash
docker-compose build
docker-compose up -d
```

### Run Migrations (if DB schema changed)
```bash
docker-compose exec backend alembic upgrade head
```

### Zero-downtime Update (load balancer required)
```bash
# Scale up new version
docker-compose up -d --scale backend=2

# Test new version
curl http://localhost:8000/docs

# Remove old version
docker-compose rm -f backend_old
```

## 📈 Performance Optimization

### Enable Compression
```bash
# Already in docker/nginx.conf
# Gzip level 6, client body buffer 10M
```

### Database Optimization
```bash
docker-compose exec postgres psql -U qazaq_user -d qazaq_db -c "VACUUM ANALYZE;"
```

### Multi-worker Backend
```bash
# Edit docker-entrypoint.sh
# Change: --workers 1
# To: --workers 4
```

### Connection Pooling
```bash
# Add to docker-compose.yml postgres section
command: ["postgres", "-c", "max_connections=200"]
```

## 🚨 Emergency Procedures

### Stop Everything
```bash
docker-compose down
```

### Emergency Restart
```bash
docker-compose down
docker-compose up -d
```

### Reset Database (⚠️ DATA LOSS)
```bash
# BACKUP FIRST!
docker-compose down -v
docker-compose up -d
```

### Check System Health
```bash
./health-check.sh
docker-compose ps
docker stats
```

## 📞 Support & Debugging

### Get Full System Information
```bash
echo "=== Docker Version ===" && docker --version
echo "=== Docker Compose Version ===" && docker-compose --version
echo "=== Container Status ===" && docker-compose ps
echo "=== Recent Logs ===" && docker-compose logs --tail=20
```

### Export Diagnostic Bundle
```bash
mkdir qazaq_diagnostics
docker-compose ps > qazaq_diagnostics/ps.txt
docker-compose logs > qazaq_diagnostics/logs.txt
docker stats --no-stream > qazaq_diagnostics/stats.txt
docker volume inspect qazaq_postgres_data > qazaq_diagnostics/postgres_volume.txt
```

## 📚 Further Reading

- [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) - Full deployment guide
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Pre/post deployment checklist
- [docker/readme.md](./docker/readme.md) - Docker configuration details
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

## ✨ Next Steps

1. **Configure Secrets** (5 min)
   ```bash
   nano backend/.env
   # Set: SECRET_KEY, GEMINI_API_KEY, etc.
   ```

2. **Build & Start** (10 min)
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. **Verify Deployment** (5 min)
   ```bash
   ./health-check.sh
   ```

4. **Setup Monitoring** (10 min)
   ```bash
   ./health-check.sh watch
   # Or integrate with: Prometheus, Grafana, Datadog
   ```

5. **Test Features** (30 min)
   - Admin panel: http://localhost:3001
   - Student app: http://localhost:3000
   - Run test suites: `docker-compose exec backend pytest tests/`

6. **Production Deployment** (ongoing)
   - Add SSL/TLS certificates
   - Configure secrets management
   - Setup log aggregation
   - Enable monitoring & alerting
   - Implement CI/CD pipeline

## 🎉 Deployment Complete!

Your Qazaq platform is now ready for deployment. All services are containerized, configured, and ready to scale.

**Key Resources:**
- 📖 Documentation: `DOCKER_DEPLOYMENT.md`
- ✅ Checklist: `DEPLOYMENT_CHECKLIST.md`
- 🛠️ Quick Setup: `./quickstart.sh`
- 📊 Monitoring: `./health-check.sh`

---

**Version**: 1.0  
**Last Updated**: 2025-12-17  
**Maintained By**: Qazaq Development Team

Questions? Check the troubleshooting sections in the documentation files above.
