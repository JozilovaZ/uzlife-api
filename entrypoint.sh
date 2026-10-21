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

# Baza bo'sh bo'lsa — demo kontent (har kategoriyaga 10 ta yangilik),
# valyuta kurslari va ob-havoni yuklaymiz. Tarmoq xatosi serverni to'xtatmaydi.
if [ "$(python manage.py shell -c 'from apps.news.models import Article; print(Article.objects.exists())' | tail -n 1)" = "False" ]; then
    echo "Baza bo'sh — demo ma'lumotlar yuklanmoqda..."
    python manage.py seed_rich --count 10 || true
    python manage.py fetch_rates || true
    python manage.py fetch_weather || true

    # Mavzuga mos haqiqiy rasmlar (Wikimedia) — bir necha daqiqa oladi,
    # shuning uchun fonda: API shu orada ishlay boshlaydi.
    ( python manage.py set_topic_covers --force \
        && python manage.py add_gallery_images --count 2 ) \
        > /tmp/rasmlar.log 2>&1 &
fi

# Gunicorn (WSGI)
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
