"""Open-Meteo'dan ob-havo prognozini yuklab olish.

Ishlatish:
    python manage.py fetch_weather            # 7 kunlik prognoz
    python manage.py fetch_weather --days 3   # faqat 3 kun

Open-Meteo bepul va API kalit talab qilmaydi. Har kuni bir-ikki marta
(cron/Task Scheduler) chaqirilsa, ticker va bosh sahifadagi ob-havo
o'z-o'zidan yangilanib turadi.
"""
from __future__ import annotations

import datetime as dt

import requests
from django.core.management.base import BaseCommand

from apps.weather.models import City, HourlyForecast, WeatherForecast

# Boshlang'ich shaharlar (nom, slug, lat, lon, asosiymi, tartib)
SEED_CITIES = [
    ('Toshkent', 'toshkent', 41.2995, 69.2401, True, 1),
    ('Samarqand', 'samarqand', 39.6270, 66.9750, False, 2),
    ('Buxoro', 'buxoro', 39.7680, 64.4210, False, 3),
    ('Namangan', 'namangan', 40.9983, 71.6726, False, 4),
    ('Andijon', 'andijon', 40.7821, 72.3442, False, 5),
    ('Farg‘ona', 'fargona', 40.3864, 71.7864, False, 6),
    ('Qarshi', 'qarshi', 38.8600, 65.7890, False, 7),
    ('Nukus', 'nukus', 42.4600, 59.6170, False, 8),
    ('Urganch', 'urganch', 41.5500, 60.6333, False, 9),
    ('Jizzax', 'jizzax', 40.1250, 67.8800, False, 10),
    ('Navoiy', 'navoiy', 40.0844, 65.3792, False, 11),
    ('Guliston', 'guliston', 40.4897, 68.7842, False, 12),
    ('Termiz', 'termiz', 37.2242, 67.2783, False, 13),
]

API_URL = 'https://api.open-meteo.com/v1/forecast'

# WMO ob-havo kodi → bizdagi Condition
# https://open-meteo.com/en/docs — "Weather variable documentation"
WMO_MAP = {
    0: WeatherForecast.Condition.CLEAR,
    1: WeatherForecast.Condition.CLEAR,
    2: WeatherForecast.Condition.PARTLY,
    3: WeatherForecast.Condition.CLOUDY,
    45: WeatherForecast.Condition.FOG,
    48: WeatherForecast.Condition.FOG,
    51: WeatherForecast.Condition.RAIN,
    53: WeatherForecast.Condition.RAIN,
    55: WeatherForecast.Condition.RAIN,
    56: WeatherForecast.Condition.RAIN,
    57: WeatherForecast.Condition.RAIN,
    61: WeatherForecast.Condition.RAIN,
    63: WeatherForecast.Condition.RAIN,
    65: WeatherForecast.Condition.RAIN,
    66: WeatherForecast.Condition.RAIN,
    67: WeatherForecast.Condition.RAIN,
    71: WeatherForecast.Condition.SNOW,
    73: WeatherForecast.Condition.SNOW,
    75: WeatherForecast.Condition.SNOW,
    77: WeatherForecast.Condition.SNOW,
    80: WeatherForecast.Condition.RAIN,
    81: WeatherForecast.Condition.RAIN,
    82: WeatherForecast.Condition.RAIN,
    85: WeatherForecast.Condition.SNOW,
    86: WeatherForecast.Condition.SNOW,
    95: WeatherForecast.Condition.THUNDER,
    96: WeatherForecast.Condition.THUNDER,
    99: WeatherForecast.Condition.THUNDER,
}


class Command(BaseCommand):
    help = 'Open-Meteo\'dan shaharlar bo\'yicha ob-havo prognozini yuklab oladi.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=10,
            help='Necha kunlik prognoz (default: 10, maksimum: 16).',
        )
        parser.add_argument(
            '--city', type=str, default='',
            help='Faqat bitta shahar (slug bo‘yicha).',
        )

    def handle(self, *args, **options):
        days = min(16, max(1, options['days']))
        cities = self._ensure_cities()

        if options['city']:
            cities = [c for c in cities if c.slug == options['city']]
            if not cities:
                self.stderr.write(f'Bunday shahar yo‘q: {options["city"]}')
                return

        created = updated = failed = 0

        for city in cities:
            result = self._fetch(city, days)
            if result is None:
                failed += 1
                continue
            rows, hours = result
            for row in rows:
                _, was_created = WeatherForecast.objects.update_or_create(
                    city=city, date=row['date'],
                    defaults={
                        'temp_now': row['temp_now'],
                        'temp_min': row['temp_min'],
                        'temp_max': row['temp_max'],
                        'condition': row['condition'],
                    },
                )
                created += was_created
                updated += (not was_created)

            for hr in hours:
                HourlyForecast.objects.update_or_create(
                    city=city, date=hr['date'], hour=hr['hour'],
                    defaults={
                        'temp': hr['temp'],
                        'feels': hr['feels'],
                        'condition': hr['condition'],
                    },
                )

        self._prune()

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {created} ta yangi, {updated} ta yangilandi, {failed} ta shahar o‘tkazib yuborildi.'
        ))

    # --- yordamchilar ---------------------------------------------------

    def _ensure_cities(self) -> list[City]:
        for name, slug, lat, lon, is_default, order in SEED_CITIES:
            City.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'latitude': lat, 'longitude': lon,
                          'is_default': is_default, 'order': order},
            )
        return list(City.objects.filter(is_active=True))

    def _fetch(self, city: City, days: int) -> tuple[list[dict], list[dict]] | None:
        params = {
            'latitude': city.latitude,
            'longitude': city.longitude,
            'daily': 'weather_code,temperature_2m_max,temperature_2m_min',
            'hourly': 'temperature_2m,apparent_temperature,weather_code',
            'current': 'temperature_2m',
            'timezone': 'Asia/Tashkent',
            'forecast_days': days,
        }
        try:
            resp = requests.get(API_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            self.stderr.write(f'  {city.name}: {exc}')
            return None

        daily = data.get('daily') or {}
        dates = daily.get('time') or []
        if not dates:
            self.stderr.write(f'  {city.name}: prognoz bo‘sh keldi')
            return None

        # "Hozirgi harorat" faqat bugungi kunga tegishli
        temp_now = (data.get('current') or {}).get('temperature_2m')

        rows = []
        for i, iso in enumerate(dates):
            date = dt.date.fromisoformat(iso)
            code = self._at(daily.get('weather_code'), i)
            rows.append({
                'date': date,
                'temp_now': round(temp_now) if (i == 0 and temp_now is not None) else None,
                'temp_min': round(self._at(daily.get('temperature_2m_min'), i) or 0),
                'temp_max': round(self._at(daily.get('temperature_2m_max'), i) or 0),
                'condition': WMO_MAP.get(code, WeatherForecast.Condition.CLEAR),
            })

        # Soatlik — "2026-07-17T14:00" ko'rinishidagi vaqtlar
        hourly = data.get('hourly') or {}
        times = hourly.get('time') or []
        temps = hourly.get('temperature_2m') or []
        feels = hourly.get('apparent_temperature') or []
        codes = hourly.get('weather_code') or []
        hours = []
        for i, iso in enumerate(times):
            when = dt.datetime.fromisoformat(iso)
            t = self._at(temps, i)
            if t is None:
                continue
            f = self._at(feels, i)
            hours.append({
                'date': when.date(),
                'hour': when.hour,
                'temp': round(t),
                'feels': round(f) if f is not None else None,
                'condition': WMO_MAP.get(self._at(codes, i), WeatherForecast.Condition.CLEAR),
            })

        return rows, hours

    def _prune(self):
        """Eski prognozlarni tozalash — ular endi kerak emas."""
        cutoff = dt.date.today() - dt.timedelta(days=2)
        WeatherForecast.objects.filter(date__lt=cutoff).delete()
        HourlyForecast.objects.filter(date__lt=cutoff).delete()

    @staticmethod
    def _at(seq, i):
        if not seq or i >= len(seq):
            return None
        return seq[i]
