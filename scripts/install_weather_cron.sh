#!/bin/sh
# Ob-havoni har soatda avtomatik yangilab turish uchun host crontab'iga
# vazifa qo'shadi (idempotent — qayta ishga tushirsa dublikat bo'lmaydi).
#
# Ishlatish (server, uzlife-api papkasida):
#     sh scripts/install_weather_cron.sh
#
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJECT_DIR/weather_cron.log"

# Har soat boshida 3 kunlik soatlik prognozni yangilaydi
CRON_LINE="0 * * * * cd $PROJECT_DIR && docker compose exec -T web python manage.py fetch_weather --days 3 >> $LOG 2>&1"
MARKER="# uzlife-weather"

# Mavjud crontab (bo'lmasa bo'sh), eski uzlife-weather qatorini olib tashlaymiz
existing="$(crontab -l 2>/dev/null | grep -v "$MARKER" || true)"

# Yangi qatorni marker bilan qo'shamiz
printf '%s\n%s %s\n' "$existing" "$CRON_LINE" "$MARKER" | crontab -

echo "Tayyor. O'rnatilgan cron vazifasi:"
crontab -l | grep "$MARKER"
echo "Loglar: $LOG"
