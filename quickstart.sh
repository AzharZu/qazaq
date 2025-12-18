#!/bin/bash
# Quick start script for Qazaq Docker deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎓 Qazaq Platform - Docker Quick Start"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Docker
echo "📋 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}: $(docker-compose --version)"
echo ""

# Check .env files
echo "🔧 Checking environment configuration..."
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠ Creating backend/.env from template${NC}"
    cp backend/.env.example backend/.env
fi
echo -e "${GREEN}✓ backend/.env ready${NC}"

if [ ! -f "admin-spa/.env.local" ]; then
    echo -e "${YELLOW}⚠ Creating admin-spa/.env.local from template${NC}"
    cp admin-spa/.env.example admin-spa/.env.local
fi
echo -e "${GREEN}✓ admin-spa/.env.local ready${NC}"

if [ ! -f "student-spa/.env.local" ]; then
    echo -e "${YELLOW}⚠ Creating student-spa/.env.local from template${NC}"
    cp student-spa/.env.example student-spa/.env.local
fi
echo -e "${GREEN}✓ student-spa/.env.local ready${NC}"
echo ""

# Build images
echo "🏗 Building Docker images..."
if docker-compose build; then
    echo -e "${GREEN}✓ All images built successfully${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
echo ""

# Start services
echo "🚀 Starting services..."
if docker-compose up -d; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy (this may take 30-60 seconds)..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ Services are healthy${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -ne "\r  Checking health... ($attempt/$max_attempts)"
    sleep 1
done
echo ""

# Show status
echo "📊 Service Status:"
docker-compose ps
echo ""

# Test connectivity
echo "🔌 Testing connectivity..."
sleep 2

if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✓ Backend API is responding${NC}"
else
    echo -e "${YELLOW}⚠ Backend API not responding yet, may still be starting${NC}"
fi

if curl -s http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ Nginx health check passing${NC}"
else
    echo -e "${YELLOW}⚠ Nginx health check not passing yet${NC}"
fi

echo ""
echo "✅ Qazaq Platform is running!"
echo ""
echo "📱 Access points:"
echo "  Admin Panel:  http://localhost:3001"
echo "  Student App: http://localhost:3000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Health:      http://localhost/health"
echo ""
echo "📖 Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Enter bash:       docker-compose exec backend bash"
echo "  Database shell:   docker-compose exec postgres psql -U qazaq_user -d qazaq_db"
echo ""
echo "💡 Tip: Check DOCKER_DEPLOYMENT.md for complete documentation"
