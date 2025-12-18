#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U qazaq_user > /dev/null 2>&1; do
    echo "   Waiting for postgres..."
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
# Use "heads" to avoid failure when multiple head revisions exist.
alembic upgrade heads || {
    echo "WARNING: Migration failed, but continuing..."
    alembic current || true
}

echo "Starting Qazaq backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
