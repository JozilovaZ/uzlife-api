"""Yangilik va kategoriyalar kontentini o‘zbekchadan rus/ingliz tiliga tarjima qiladi.

modeltranslation maydonlarini (title_ru, body_en, ...) to‘ldiradi. Bepul Google
Translate endpoint'idan foydalanadi. HTML body'da faqat matn tugunlari tarjima
qilinadi — teglar, atributlar, <img>, entitylar tegilmaydi. Takroriy matnlar
keshlanadi, shu bois so‘rovlar soni kamayadi.
"""
import json
import re
import time
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand

from apps.news.models import Article, Category

ENDPOINT = 'https://translate.googleapis.com/translate_a/single'

# HTML: teg / script / style / entity — tarjima qilinmaydi
_SKIP = re.compile(
    r'(<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>|&[#a-zA-Z0-9]+;)',
    re.S | re.I,
)


class Translator:
    def __init__(self, stdout):
        self.cache = {}
        self.stdout = stdout
        self.calls = 0

    def _raw(self, text, tl):
        params = urllib.parse.urlencode({
            'client': 'gtx', 'sl': 'uz', 'tl': tl, 'dt': 't', 'q': text,
        })
        req = urllib.request.Request(
            f'{ENDPOINT}?{params}', headers={'User-Agent': 'Mozilla/5.0'})
        for attempt in range(4):
            try:
                data = json.loads(
                    urllib.request.urlopen(req, timeout=20).read().decode('utf-8'))
                self.calls += 1
                return ''.join(seg[0] for seg in data[0] if seg[0])
            except Exception as e:  # noqa: BLE001 — tarmoq/limit xatosi, qayta urinamiz
                if attempt == 3:
                    self.stdout.write(f'  ! tarjima xatosi: {e}')
                    return text
                time.sleep(1.5 * (attempt + 1))

    def text(self, text, tl):
        """Bitta oddiy matnni (keshlab) tarjima qiladi."""
        text = (text or '').strip()
        if not text:
            return text
        key = (tl, text)
        if key not in self.cache:
            self.cache[key] = self._raw(text, tl)
        return self.cache[key]

    def html(self, html, tl):
        """HTML matn tugunlarini tarjima qiladi, teglarni saqlaydi."""
        parts = _SKIP.split(html or '')
        for i in range(0, len(parts), 2):
            seg = parts[i]
            if seg.strip():
                # tegdan tashqari bo'sh joyni saqlash uchun trim qismini ajratamiz
                lead = seg[:len(seg) - len(seg.lstrip())]
                trail = seg[len(seg.rstrip()):]
                parts[i] = lead + self.text(seg, tl) + trail
        return ''.join(parts)


class Command(BaseCommand):
    help = 'Kontentni uz -> ru/en ga tarjima qiladi (modeltranslation maydonlariga).'

    def add_arguments(self, parser):
        parser.add_argument('--langs', default='ru,en',
                            help='Vergul bilan: ru,en')
        parser.add_argument('--force', action='store_true',
                            help='Allaqachon tarjima qilinganlarni ham qayta yozadi.')

    def handle(self, *args, **opts):
        langs = [l.strip() for l in opts['langs'].split(',') if l.strip()]
        force = opts['force']
        tr = Translator(self.stdout)

        # Kategoriyalar
        for cat in Category.objects.all():
            changed = False
            for tl in langs:
                if force or not getattr(cat, f'name_{tl}'):
                    setattr(cat, f'name_{tl}', tr.text(cat.name_uz or cat.name, tl))
                    changed = True
            if changed:
                cat.save()
        self.stdout.write('Kategoriyalar tarjima qilindi.')

        # Maqolalar
        total = Article.objects.count()
        for n, art in enumerate(Article.objects.all(), 1):
            changed = False
            for tl in langs:
                if force or not getattr(art, f'title_{tl}'):
                    setattr(art, f'title_{tl}', tr.text(art.title_uz or art.title, tl))
                    changed = True
                if force or not getattr(art, f'summary_{tl}'):
                    setattr(art, f'summary_{tl}', tr.text(art.summary_uz or art.summary, tl))
                    changed = True
                if force or not getattr(art, f'body_{tl}'):
                    setattr(art, f'body_{tl}', tr.html(art.body_uz or art.body, tl))
                    changed = True
            if changed:
                art.save()
            if n % 10 == 0 or n == total:
                self.stdout.write(f'  {n}/{total} maqola ({tr.calls} so‘rov)')

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor. Jami {tr.calls} ta tarjima so‘rovi bajarildi.'))
