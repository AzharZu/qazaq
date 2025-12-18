FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps needed for pg_isready (start.sh) and healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code explicitly (no accidental misses if root context is used)
COPY backend/start.sh /app/start.sh
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

RUN mkdir -p /app/uploads && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
