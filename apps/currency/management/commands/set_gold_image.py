"""Valyutalarga oltin (sariq) tanga rasmini biriktiradi.

    python manage.py set_gold_image          # rasmi yo‘q valyutalarga qo‘yadi
    python manage.py set_gold_image --all     # barcha valyutalarga qayta qo‘yadi
"""
import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont

from apps.currency.models import Currency


def _font(size):
    import os.path
    import PIL
    pil_fonts = os.path.join(os.path.dirname(PIL.__file__), 'fonts')
    for path in (
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        os.path.join(pil_fonts, 'DejaVuSans-Bold.ttf'),
        os.path.join(pil_fonts, 'DejaVuSans.ttf'),
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_gold_coin(symbol='$'):
    """Sariq/oltin tanga rasmini yaratadi (512x512, shaffof fon)."""
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = size // 2

    # Tashqi oltin doira (radial ko‘rinish uchun konsentrik doiralar)
    outer = (218, 165, 32)   # goldenrod
    inner = (255, 215, 0)    # gold
    r0 = 240
    for i in range(r0, 0, -1):
        t = i / r0
        col = tuple(int(inner[k] * (1 - t) + outer[k] * t) for k in range(3))
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col + (255,))

    # Ichki halqa (relyef effekti)
    d.ellipse([cx - 190, cy - 190, cx + 190, cy + 190],
              outline=(184, 134, 11), width=10)
    d.ellipse([cx - 165, cy - 165, cx + 165, cy + 165],
              outline=(255, 236, 139), width=4)

    # Markaziy belgi
    font = _font(230)
    bbox = d.textbbox((0, 0), symbol, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), symbol,
           font=font, fill=(140, 100, 10, 255))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'Valyutalarga oltin tanga rasmini biriktiradi.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                            help='Rasmi bor valyutalarni ham qayta yozadi.')

    def handle(self, *args, **opts):
        qs = Currency.objects.all()
        if not opts['all']:
            qs = qs.filter(image='')
        count = 0
        for cur in qs:
            symbol = (cur.symbol or cur.code[:1] or '$')[:1]
            cur.image.save(f'gold-{cur.code.lower()}.png',
                           make_gold_coin(symbol), save=True)
            count += 1
            self.stdout.write(f'  + {cur.code}: oltin rasm qo‘yildi')
        self.stdout.write(self.style.SUCCESS(f'Tayyor: {count} ta valyutaga rasm qo‘yildi.'))
