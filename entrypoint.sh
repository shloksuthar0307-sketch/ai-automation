#!/bin/sh
set -e

echo "[Sitewright Entrypoint] Initializing production environment..."

# Wait for PostgreSQL if configured
if [ -n "$POSTGRES_HOST" ]; then
  echo "[Sitewright Entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
  timeout=30
  while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}" 2>/dev/null; do
    timeout=$((timeout - 1))
    if [ "$timeout" -le 0 ]; then
      echo "[Sitewright Entrypoint] Warning: Timed out waiting for PostgreSQL. Continuing with fallback..."
      break
    fi
    sleep 1
  done
fi

# Run database migrations
echo "[Sitewright Entrypoint] Applying database migrations..."
python manage.py migrate --noinput

# Collect static files if not already collected
echo "[Sitewright Entrypoint] Collecting static assets..."
python manage.py collectstatic --noinput

# Start application server
echo "[Sitewright Entrypoint] Starting Gunicorn server..."
exec gunicorn sitewright.wsgi:application --config gunicorn.conf.py "$@"

