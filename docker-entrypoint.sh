#!/bin/sh
# Production by default. Set USE_GUNICORN=false only for local development.
set -eu
WORKERS="${GUNICORN_WORKERS:-1}"
PORT="${GUNICORN_PORT:-8000}"
# Never start background ingestion inside a short-lived management process.
echo "Running database migrations..."
REALTIME_INGESTION_AUTO_START=false python manage.py migrate --noinput
# Startup must not depend on a remote exchange or silently place any orders.
if [ "${USE_GUNICORN:-true}" = "true" ] || [ "${USE_GUNICORN:-true}" = "1" ]; then
    exec gunicorn -w "$WORKERS" -k uvicorn.workers.UvicornWorker \
        -b "0.0.0.0:${PORT}" --max-requests 10000 \
        --max-requests-jitter 1000 --timeout 60 --graceful-timeout 30 \
        --access-logfile - --error-logfile - geneticgrid.asgi:application
else
    exec python manage.py runserver "0.0.0.0:${PORT}"
fi
