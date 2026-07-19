"""CBU (cbu.uz) rasmiy valyuta kurslarini yuklab olish.

Ishlatish:
    python manage.py fetch_rates            # bugungi kursni yangilaydi
    python manage.py fetch_rates --days 30  # oxirgi 30 kunlik tarixni to'ldiradi

Har kuni bir marta (masalan cron/Task Scheduler) `fetch_rates` chaqirilsa,
bosh sahifadagi kurs va grafik o'z-o'zidan yangilanib turadi.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.currency.models import Currency, CurrencyRate

# Biz kuzatadigan valyutalar (kod → nom, belgi, bayroq, tartib, bosh sahifada)
TRACKED = [
    ('USD', 'AQSH dollari', '$', '🇺🇸', 1, True),
    ('EUR', 'Yevro', '€', '🇪🇺', 2, True),
    ('RUB', 'Rossiya rubli', '₽', '🇷🇺', 3, True),
    ('GBP', 'Angliya funt sterlingi', '£', '🇬🇧', 4, False),
    ('CHF', 'Shveytsariya franki', '₣', '🇨🇭', 5, False),
    ('CNY', 'Xitoy yuani', '¥', '🇨🇳', 6, False),
    ('JPY', 'Yaponiya iyenasi', '¥', '🇯🇵', 7, False),
    ('KZT', 'Qozogʻiston tengesi', '₸', '🇰🇿', 8, False),
]

CBU_URL = 'https://cbu.uz/uz/arkhiv-kursov-valyut/json/{ccy}/{date}/'


class Command(BaseCommand):
    help = 'CBU rasmiy valyuta kurslarini yuklab oladi (USD, EUR, RUB).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=1,
            help='Necha kunlik tarixni to‘ldirish (default: 1 — faqat bugun).',
        )

    def handle(self, *args, **options):
        days = max(1, options['days'])
        currencies = self._ensure_currencies()

        today = timezone.localdate()
        created = updated = failed = 0

        for offset in range(days):
            date = today - dt.timedelta(days=offset)
            for ccy in currencies.values():
                row = self._fetch(ccy.code, date)
                if row is None:
                    failed += 1
                    continue
                rate = self._to_decimal(row.get('Rate'))
                diff = self._to_decimal(row.get('Diff')) or Decimal('0')
                if rate is None:
                    failed += 1
                    continue
                _, was_created = CurrencyRate.objects.update_or_create(
                    currency=ccy, date=date,
                    defaults={'rate': rate, 'diff': diff},
                )
                created += was_created
                updated += (not was_created)

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {created} ta yangi, {updated} ta yangilandi, {failed} ta o‘tkazib yuborildi.'
        ))

    # --- yordamchilar ---------------------------------------------------

    def _ensure_currencies(self) -> dict[str, Currency]:
        result = {}
        for code, name, symbol, flag, order, featured in TRACKED:
            obj, _ = Currency.objects.get_or_create(
                code=code,
                defaults={'name': name, 'symbol': symbol, 'flag_emoji': flag,
                          'order': order, 'is_featured': featured},
            )
            result[code] = obj
        return result

    def _fetch(self, ccy: str, date: dt.date) -> dict | None:
        url = CBU_URL.format(ccy=ccy, date=date.isoformat())
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            self.stderr.write(f'  {ccy} {date}: {exc}')
            return None
        # CBU ro'yxat qaytaradi; birinchi element kerakli valyuta
        if isinstance(data, list) and data:
            return data[0]
        return None

    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        if value in (None, ''):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return None
