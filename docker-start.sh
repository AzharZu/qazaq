#!/bin/bash

set -e

echo "🚀 Starting Qazaq Platform with Docker..."

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env not found. Creating from template..."
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
    else
        cat > backend/.env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql+asyncpg://qazaq_user:qazaq_pass@postgres:5432/qazaq_db
ALLOWED_ORIGINS=["http://localhost","http://localhost:80","http://127.0.0.1"]
ADMIN_EMAILS=["admin@example.com"]
EOF
    fi
fi

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build and start services
echo "📦 Building images (this may take a while the first time)..."
docker-compose build --parallel

echo "🔄 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 5

# Wait for backend to be ready
echo "🔍 Checking backend health..."
timeout=60
elapsed=0
while ! docker exec qazaq_backend curl -fs http://localhost:8000/docs >/dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        docker-compose logs backend
        exit 1
    fi
    echo "   Waiting for backend... ($elapsed/$timeout seconds)"
    sleep 2
    elapsed=$((elapsed + 2))
done

echo ""
echo "✅ All services are running!"
echo ""
echo "📍 Access points:"
echo "   - Admin Panel:  http://localhost:3001"
echo "   - API Docs:     http://localhost:8000/docs"
echo "   - Main Site:    http://localhost (via nginx)"
echo ""
echo "📝 Useful commands:"
echo "   - View logs:    docker-compose logs -f [service]"
echo "   - Stop:         docker-compose down"
echo "   - Rebuild:      docker-compose build --no-cache"
echo ""
