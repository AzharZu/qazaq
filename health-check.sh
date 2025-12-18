#!/bin/bash
# Qazaq Platform - Health Check & Monitoring Script
# Usage: ./health-check.sh [watch]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if watch mode
WATCH=false
if [ "$1" == "watch" ]; then
    WATCH=true
    INTERVAL=5
fi

run_checks() {
    clear
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🎓 Qazaq Platform - Health Check & System Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Timestamp
    echo "Last checked: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Container Status
    echo -e "${BLUE}📦 Container Status${NC}"
    echo "─────────────────────────────────────────────────────────────"
    docker-compose ps
    echo ""
    
    # Service Health
    echo -e "${BLUE}🏥 Service Health Checks${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # PostgreSQL
    if docker-compose exec postgres pg_isready -U qazaq_user -q; then
        echo -e "${GREEN}✓ PostgreSQL${NC} (postgres:5432)"
    else
        echo -e "${RED}✗ PostgreSQL${NC} (postgres:5432) - Not responding"
    fi
    
    # Backend
    if curl -s http://localhost:8000/docs > /dev/null; then
        echo -e "${GREEN}✓ Backend API${NC} (localhost:8000/docs)"
    else
        echo -e "${RED}✗ Backend API${NC} (localhost:8000) - Not responding"
    fi
    
    # Nginx Health
    if curl -s http://localhost/health > /dev/null; then
        echo -e "${GREEN}✓ Nginx Reverse Proxy${NC} (localhost:80)"
    else
        echo -e "${RED}✗ Nginx${NC} (localhost:80) - Not responding"
    fi
    
    # Admin SPA
    if curl -s http://localhost:3001 > /dev/null; then
        echo -e "${GREEN}✓ Admin SPA${NC} (localhost:3001)"
    else
        echo -e "${RED}✗ Admin SPA${NC} (localhost:3001) - Not responding"
    fi
    
    # Student SPA
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Student SPA${NC} (localhost:3000)"
    else
        echo -e "${RED}✗ Student SPA${NC} (localhost:3000) - Not responding"
    fi
    echo ""
    
    # Resource Usage
    echo -e "${BLUE}💾 Resource Usage${NC}"
    echo "─────────────────────────────────────────────────────────────"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "Docker stats unavailable"
    echo ""
    
    # Volume Status
    echo -e "${BLUE}📁 Storage Volumes${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # PostgreSQL Data Volume
    PG_VOLUME=$(docker volume inspect qazaq_postgres_data 2>/dev/null | grep -A 1 "Mountpoint" | tail -1 | awk '{print $2}')
    if [ -n "$PG_VOLUME" ]; then
        PG_SIZE=$(du -sh "$PG_VOLUME" 2>/dev/null | awk '{print $1}')
        echo "📊 PostgreSQL Data: $PG_SIZE"
    fi
    
    # Uploads Volume
    UPLOAD_VOLUME=$(docker volume inspect qazaq_uploads 2>/dev/null | grep -A 1 "Mountpoint" | tail -1 | awk '{print $2}')
    if [ -n "$UPLOAD_VOLUME" ]; then
        UPLOAD_SIZE=$(du -sh "$UPLOAD_VOLUME" 2>/dev/null | awk '{print $1}')
        UPLOAD_COUNT=$(find "$UPLOAD_VOLUME" -type f 2>/dev/null | wc -l)
        echo "📤 Uploads: $UPLOAD_SIZE ($UPLOAD_COUNT files)"
    fi
    echo ""
    
    # Error Check
    echo -e "${BLUE}⚠️  Recent Errors & Warnings${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    ERROR_COUNT=$(docker-compose logs --since 1h 2>/dev/null | grep -i error | wc -l)
    WARNING_COUNT=$(docker-compose logs --since 1h 2>/dev/null | grep -i warning | wc -l)
    
    if [ $ERROR_COUNT -eq 0 ]; then
        echo -e "${GREEN}✓ No errors in last hour${NC}"
    else
        echo -e "${RED}✗ $ERROR_COUNT errors found${NC}"
        echo ""
        docker-compose logs --since 1h 2>/dev/null | grep -i error | tail -5
    fi
    
    if [ $WARNING_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNING_COUNT warnings found${NC}"
        docker-compose logs --since 1h 2>/dev/null | grep -i warning | tail -3
    fi
    echo ""
    
    # Database Stats
    echo -e "${BLUE}📊 Database Statistics${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # Connection count
    CONN_COUNT=$(docker-compose exec -T postgres psql -U qazaq_user -d qazaq_db -t -c \
        "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null || echo "N/A")
    echo "Active connections: $CONN_COUNT"
    
    # Database size
    DB_SIZE=$(docker-compose exec -T postgres psql -U qazaq_user -d qazaq_db -t -c \
        "SELECT pg_size_pretty(pg_database.datsize) FROM pg_database WHERE datname = 'qazaq_db';" 2>/dev/null || echo "N/A")
    echo "Database size: $DB_SIZE"
    
    # Table count
    TABLE_COUNT=$(docker-compose exec -T postgres psql -U qazaq_user -d qazaq_db -t -c \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "N/A")
    echo "Tables: $TABLE_COUNT"
    
    echo ""
    
    # API Response Times
    echo -e "${BLUE}⚡ API Response Times${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    START=$(date +%s%N)
    curl -s http://localhost:8000/docs > /dev/null
    END=$(date +%s%N)
    RESPONSE_TIME=$(( (END - START) / 1000000 ))
    echo "Backend /docs: ${RESPONSE_TIME}ms"
    
    START=$(date +%s%N)
    curl -s http://localhost/health > /dev/null
    END=$(date +%s%N)
    RESPONSE_TIME=$(( (END - START) / 1000000 ))
    echo "Nginx /health: ${RESPONSE_TIME}ms"
    
    echo ""
    
    # Recommendations
    echo -e "${BLUE}💡 Recommendations${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # Check memory
    MEM_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" 2>/dev/null | head -1 | tr -d '%')
    if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
        echo -e "${YELLOW}⚠ High memory usage: $MEM_USAGE%${NC}"
        echo "  Consider: increasing Docker memory or optimizing queries"
    fi
    
    # Check disk space
    DISK_USAGE=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo -e "${YELLOW}⚠ Low disk space: $DISK_USAGE% used${NC}"
        echo "  Consider: cleaning up old volumes or backups"
    fi
    
    # Check database size
    if [ "$DB_SIZE" != "N/A" ]; then
        DB_SIZE_NUM=$(echo "$DB_SIZE" | grep -oE '[0-9]+' | head -1)
        if (( DB_SIZE_NUM > 500 )); then
            echo -e "${YELLOW}⚠ Large database: $DB_SIZE${NC}"
            echo "  Consider: archiving old data or optimizing tables"
        fi
    fi
    
    # Backup status
    LATEST_BACKUP=$(ls -t /Users/sanzar/Desktop/qazaq/backup*.sql 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(stat -f "%m" "$LATEST_BACKUP" 2>/dev/null || echo "0")
        CURRENT_TIME=$(date +%s)
        DAYS_OLD=$(( (CURRENT_TIME - BACKUP_AGE) / 86400 ))
        if [ "$DAYS_OLD" -gt 7 ]; then
            echo -e "${YELLOW}⚠ Backup is $DAYS_OLD days old${NC}"
            echo "  Consider: running a fresh backup"
        fi
    else
        echo -e "${YELLOW}⚠ No recent backups found${NC}"
        echo "  Consider: backing up database: docker-compose exec postgres pg_dump -U qazaq_user qazaq_db > backup.sql"
    fi
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    if [ "$WATCH" == true ]; then
        echo "Auto-refreshing in ${INTERVAL}s (Press Ctrl+C to stop)..."
        sleep $INTERVAL
    fi
}

# Main loop
if [ "$WATCH" == true ]; then
    while true; do
        run_checks
    done
else
    run_checks
    echo ""
    echo "💡 Tip: Run './health-check.sh watch' for continuous monitoring"
fi
