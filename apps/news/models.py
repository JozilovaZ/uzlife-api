from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """Yangilik rubrikasi: Siyosat, Iqtisod, Sport, ..."""
    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug (URL)', max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    """Yangilik / maqola."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Qoralama'
        PUBLISHED = 'published', 'E’lon qilingan'

    title = models.CharField('Sarlavha', max_length=250)
    slug = models.SlugField('Slug (URL)', max_length=270, unique=True, blank=True)
    summary = models.TextField('Qisqa mazmun', max_length=500, blank=True)
    body = models.TextField('Matn')
    cover_image = models.ImageField('Muqova rasm', upload_to='news/%Y/%m/', blank=True, null=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='articles', verbose_name='Kategoriya',
    )
    author = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='articles', verbose_name='Muallif',
    )

    status = models.CharField('Holat', max_length=10, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField('Bosh sahifada (katta)', default=False)
    views_count = models.PositiveIntegerField('Ko‘rishlar', default=0)

    published_at = models.DateTimeField('E’lon vaqti', default=timezone.now)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)

    class Meta:
        verbose_name = 'Yangilik'
        verbose_name_plural = 'Yangiliklar'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:250] or 'maqola'
            slug, i = base, 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f'{base}-{i}'
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class ArticleImage(models.Model):
    """Yangilik galereyasi — muqovadan tashqari qo‘shimcha rasmlar.

    Detal sahifada muqova ostida ko‘rsatiladi. Admin paneldan har bir
    yangilikka qo‘lda ham qo‘shish mumkin (inline).
    """
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE,
        related_name='images', verbose_name='Yangilik',
    )
    image = models.ImageField('Rasm', upload_to='news/gallery/%Y/%m/')
    caption = models.CharField('Izoh', max_length=250, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Yangilik rasmi'
        verbose_name_plural = 'Yangilik rasmlari (galereya)'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.article.title[:40]} — rasm #{self.pk}'
