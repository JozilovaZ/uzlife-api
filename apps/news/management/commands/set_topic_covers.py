"""Har bir yangilikning muqova rasmini mavzuga MOS haqiqiy fotoga almashtiradi.

Rasm manbai: Wikimedia Commons (kalitsiz, ochiq litsenziyali). Har kategoriyaga
mos qidiruv so‘zlari orqali fotolar qidirilib, 1200x630 muqovaga qirqiladi va
saqlanadi.

Ishlatish:
    python manage.py set_topic_covers                 # barcha maqolalar
    python manage.py set_topic_covers --category sport # faqat bitta kategoriya
    python manage.py set_topic_covers --force          # rasm bor bo‘lsa ham qayta yuklaydi
"""
import io
import ssl
import time
import json
import urllib.error
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from PIL import Image

from apps.news.models import Article, Category

# Kategoriya slug -> Openverse qidiruv so‘zlari (ingliz tilida — natija ko‘proq).
# Har xil so‘zlar rasm xilma-xilligini oshiradi.
CATEGORY_QUERIES = {
    'siyosat': ['parliament building', 'government meeting', 'flag politics',
                'diplomacy handshake', 'congress hall'],
    'iqtisod': ['finance business', 'stock market', 'bank money',
                'economy office', 'trade export'],
    'jamiyat': ['city people', 'crowd street', 'community volunteers',
                'family society', 'public transport'],
    'dunyo': ['world globe', 'international flags', 'united nations',
              'earth map', 'global city skyline'],
    'sport': ['football stadium', 'athletics running', 'basketball game',
              'olympic sport', 'tennis court'],
    'texnologiya': ['technology computer', 'artificial intelligence',
                    'smartphone gadget', 'data server', 'robotics'],
    'madaniyat': ['theater stage', 'art museum', 'music concert',
                  'traditional dance', 'cinema film'],
    'talim': ['university students', 'classroom school', 'library books',
              'graduation education', 'science laboratory'],
}

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'UzLifeNewsBot/1.0 (https://yangilik.uz; davronovtuit0397@gmail.com)'}
COVER_W, COVER_H = 1200, 630
_ctx = ssl.create_default_context()


def _urlopen_retry(url, timeout=25, tries=4):
    """URL'ni ochadi; 429/5xx/tarmoq xatosida backoff bilan qayta urinadi."""
    delay = 2.0
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout, context=_ctx).read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                # Retry-After bo‘lsa unga amal qilamiz
                ra = e.headers.get('Retry-After') if e.headers else None
                wait = float(ra) if (ra and ra.isdigit()) else delay
                time.sleep(min(wait, 30))
                delay *= 2
                continue
            raise
        except Exception as e:  # noqa: BLE001 — DNS/timeout va h.k.
            last = e
            time.sleep(delay)
            delay *= 2
    if last:
        raise last
    raise RuntimeError('urlopen: noma’lum xato')


def _fetch_candidates(query, limit=30):
    """Wikimedia Commons'dan berilgan so‘z bo‘yicha rasm URL ro‘yxatini qaytaradi."""
    qs = urllib.parse.urlencode({
        'action': 'query', 'generator': 'search', 'gsrsearch': query,
        'gsrnamespace': 6, 'gsrlimit': limit,
        'prop': 'imageinfo', 'iiprop': 'url|mime',
        'iiurlwidth': COVER_W, 'format': 'json',
    })
    data = json.loads(_urlopen_retry(COMMONS_API + '?' + qs))
    pages = (data.get('query') or {}).get('pages', {})
    urls = []
    for p in pages.values():
        ii = (p.get('imageinfo') or [{}])[0]
        mime = ii.get('mime', '')
        if mime not in ('image/jpeg', 'image/png'):
            continue  # svg/tif/gif — muqovaga yaramaydi
        u = ii.get('thumburl') or ii.get('url')
        if u:
            urls.append(u)
    return urls


def _download_cover(url):
    """Rasmni yuklab, 1200x630 muqovaga qirqadi. Muvaffaqiyatsizda None."""
    raw = _urlopen_retry(url)
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    # Markazdan crop qilib, muqova nisbatiga (1200x630) keltiramiz
    tw, th = COVER_W, COVER_H
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf


class Command(BaseCommand):
    help = 'Yangiliklarga mavzuga mos haqiqiy muqova rasmlarini qo‘yadi (Wikimedia Commons).'

    def add_arguments(self, parser):
        parser.add_argument('--category', help='Faqat shu kategoriya slug‘i')
        parser.add_argument('--force', action='store_true',
                            help='Muqova bor bo‘lsa ham qayta yuklaydi')

    def handle(self, *args, **opts):
        cats = Category.objects.all()
        if opts.get('category'):
            cats = cats.filter(slug=opts['category'])
            if not cats:
                self.stderr.write(f'Kategoriya topilmadi: {opts["category"]}')
                return

        total_ok = 0
        for cat in cats:
            queries = CATEGORY_QUERIES.get(cat.slug)
            if not queries:
                self.stdout.write(f'  ! {cat.slug}: qidiruv so‘zi yo‘q, o‘tkazildi')
                continue

            articles = list(cat.articles.order_by('id'))
            if not opts.get('force'):
                articles = [a for a in articles if not a.cover_image]
            if not articles:
                self.stdout.write(f'  = {cat.name}: yangilanadigan maqola yo‘q')
                continue

            # Bir necha so‘z bo‘yicha nomzod rasmlarni yig‘amiz (xilma-xillik uchun)
            pool = []
            seen = set()
            for q in queries:
                try:
                    for u in _fetch_candidates(q):
                        if u not in seen:
                            seen.add(u)
                            pool.append(u)
                    time.sleep(1.0)  # Wikimedia'ni charchatmaslik
                except Exception as e:
                    self.stdout.write(f'    qidiruv xatosi ({q}): {e}')
                if len(pool) >= len(articles) + 15:
                    break

            self.stdout.write(
                f'\n{cat.name}: {len(articles)} maqola, {len(pool)} nomzod rasm')

            pi = 0
            for art in articles:
                saved = False
                while pi < len(pool) and not saved:
                    url = pool[pi]
                    pi += 1
                    try:
                        buf = _download_cover(url)
                    except Exception:
                        continue  # keyingi nomzodga o‘tamiz
                    # Eski placeholder faylni o‘chiramiz
                    if art.cover_image:
                        art.cover_image.delete(save=False)
                    fname = f'{cat.slug}-{art.id}.jpg'
                    art.cover_image.save(fname, ContentFile(buf.read()), save=True)
                    saved = True
                    total_ok += 1
                    self.stdout.write(f'  + {art.title[:45]}…')
                    time.sleep(0.3)  # yuklab olishlar orasida kichik pauza
                if not saved:
                    self.stdout.write(
                        f'  ! rasm topilmadi: {art.title[:45]}…')

        self.stdout.write(self.style.SUCCESS(
            f'\nTayyor: {total_ok} ta yangilik muqovasi mavzuga mos rasmga almashtirildi.'))
