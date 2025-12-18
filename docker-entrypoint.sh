#!/bin/bash
# Backend startup script for Docker
# Runs database migrations and starts Uvicorn server

set -e

echo "Starting Qazaq backend..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run Alembic migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

# Start Uvicorn server
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
