#!/bin/bash
set -e

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-qazaq_user}"
DB_NAME="${DB_NAME:-qazaq_db}"

echo "Waiting for PostgreSQL to be ready at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
alembic upgrade head

echo "Starting backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
