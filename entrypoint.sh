#!/bin/sh
set -e

# Postgres tayyor bo'lguncha kutamiz
if [ -n "$POSTGRES_HOST" ]; then
    echo "Postgres ($POSTGRES_HOST:${POSTGRES_PORT:-5432}) kutilmoqda..."
    until python -c "import socket,sys; s=socket.socket(); s.settimeout(2); \
        sys.exit(0) if s.connect_ex(('$POSTGRES_HOST', int('${POSTGRES_PORT:-5432}')))==0 else sys.exit(1)" 2>/dev/null; do
        sleep 1
    done
    echo "Postgres tayyor."
fi

# Migratsiya va statik fayllar
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Gunicorn (WSGI)
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
