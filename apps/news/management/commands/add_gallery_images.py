"""Har bir yangilikka mavzuga MOS bir nechta qo‘shimcha rasm (galereya) qo‘shadi.

Rasm manbai: Wikimedia Commons — set_topic_covers'dagi yordamchilar qayta
ishlatiladi. Rasmlar ArticleImage sifatida saqlanadi va detal API'da `images`
maydonida chiqadi.

Ishlatish:
    python manage.py add_gallery_images                 # har maqolaga 3 tadan
    python manage.py add_gallery_images --count 4
    python manage.py add_gallery_images --category sport
    python manage.py add_gallery_images --force         # bor bo‘lsa ham qayta
"""
import random
import time

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.news.models import ArticleImage, Category

from .set_topic_covers import (
    CATEGORY_QUERIES,
    _download_cover,
    _fetch_candidates,
)


class Command(BaseCommand):
    help = 'Yangiliklarga mavzuga mos qo‘shimcha rasmlar (galereya) qo‘shadi.'

    def add_arguments(self, parser):
        parser.add_argument('--category', help='Faqat shu kategoriya slug‘i')
        parser.add_argument('--count', type=int, default=3,
                            help='Har maqolaga nechta rasm (default: 3)')
        parser.add_argument('--force', action='store_true',
                            help='Galereyasi bor maqolalarni ham qayta to‘ldiradi')

    def handle(self, *args, **opts):
        per = max(1, opts['count'])
        cats = Category.objects.all()
        if opts.get('category'):
            cats = cats.filter(slug=opts['category'])
            if not cats:
                self.stderr.write(f'Kategoriya topilmadi: {opts["category"]}')
                return

        total_imgs = 0
        for cat in cats:
            queries = CATEGORY_QUERIES.get(cat.slug)
            if not queries:
                self.stdout.write(f'  ! {cat.slug}: qidiruv so‘zi yo‘q, o‘tkazildi')
                continue

            articles = list(cat.articles.order_by('id'))
            if not opts.get('force'):
                articles = [a for a in articles if not a.images.exists()]
            if not articles:
                self.stdout.write(f'  = {cat.name}: yangilanadigan maqola yo‘q')
                continue

            need = len(articles) * per + 20
            pool, seen = [], set()
            for q in queries:
                try:
                    for u in _fetch_candidates(q):
                        if u not in seen:
                            seen.add(u)
                            pool.append(u)
                    time.sleep(1.0)
                except Exception as e:
                    self.stdout.write(f'    qidiruv xatosi ({q}): {e}')
                if len(pool) >= need:
                    break

            # Muqova pool boshidan olingan — galereya boshqa rasmlarni ko‘rsatishi
            # uchun tartibni aralashtiramiz (kategoriya bo‘yicha izchil).
            random.Random(cat.slug).shuffle(pool)

            self.stdout.write(
                f'\n{cat.name}: {len(articles)} maqola, {len(pool)} nomzod rasm')

            pi = 0
            for art in articles:
                if opts.get('force'):
                    art.images.all().delete()
                added = 0
                while added < per and pi < len(pool):
                    url = pool[pi]
                    pi += 1
                    try:
                        buf = _download_cover(url)
                    except Exception:
                        continue
                    img = ArticleImage(
                        article=art, order=added,
                        caption=f'{cat.name}: mavzuga oid tasvir',
                    )
                    img.image.save(f'{cat.slug}-{art.id}-{added + 1}.jpg',
                                   ContentFile(buf.read()), save=True)
                    added += 1
                    total_imgs += 1
                    time.sleep(0.3)
                self.stdout.write(f'  + {art.title[:42]}… ({added} rasm)')

        self.stdout.write(self.style.SUCCESS(
            f'\nTayyor: {total_imgs} ta galereya rasmi qo‘shildi.'))
