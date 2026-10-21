"""Demo yangiliklarga loyiha ichidagi mavzuga MOS fotolarni muqova qilib qo‘yadi.

Fotolar `apps/news/seed_photos/<kategoriya>-<NN>.jpg` da saqlangan (Wikimedia
Commons, ochiq litsenziya) — server internetdan qidirmaydi. Har bir fayl
seed_rich TITLES ro‘yxatidagi shu tartibdagi sarlavhaga mos.

Ishlatish:
    python manage.py apply_seed_photos          # hali foto qo‘yilmaganlarga
    python manage.py apply_seed_photos --force  # hammasini qayta qo‘yadi

Takroriy ishga tushirish xavfsiz — entrypoint har startda chaqiradi.
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.news.models import Article

from .seed_rich import TITLES

PHOTO_DIR = Path(__file__).resolve().parents[2] / 'seed_photos'
PREFIX = 'photo-'


def seed_photo_path(cat_name, index):
    """Kategoriya va 0 dan boshlangan tartib raqami bo‘yicha foto yo‘li (yoki None)."""
    path = PHOTO_DIR / f'{slugify(cat_name)}-{index + 1:02d}.jpg'
    return path if path.exists() else None


class Command(BaseCommand):
    help = 'Demo yangiliklarga mavzuga mos fotolarni (seed_photos) muqova qiladi.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Foto qo‘yilganlarini ham qayta yozadi.')

    def handle(self, *args, **opts):
        done = 0
        for cat_name, titles in TITLES.items():
            for i, title in enumerate(titles):
                path = seed_photo_path(cat_name, i)
                if not path:
                    continue
                for art in Article.objects.filter(title_uz=title):
                    name = art.cover_image.name.rsplit('/', 1)[-1] if art.cover_image else ''
                    if name.startswith(PREFIX) and not opts['force']:
                        continue
                    if art.cover_image:
                        art.cover_image.delete(save=False)
                    with path.open('rb') as fh:
                        art.cover_image.save(PREFIX + path.name, File(fh), save=True)
                    done += 1
                    self.stdout.write(f'  + {title[:45]}…')

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {done} ta yangilikka mos foto qo‘yildi.'))
