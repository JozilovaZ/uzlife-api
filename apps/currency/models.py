from django.db import models


class Currency(models.Model):
    """Valyuta turi: USD, EUR, RUB, ...

    Alohida model — chunki keyin bir nechta valyuta ko'rsatamiz,
    ro'yxatni admin'dan kengaytirish oson bo'lsin.
    """
    code = models.CharField('Kod', max_length=3, unique=True, help_text='USD, EUR, RUB')
    name = models.CharField('Nomi', max_length=100)
    symbol = models.CharField('Belgi', max_length=8, blank=True, help_text='$, €, ₽')
    flag_emoji = models.CharField('Bayroq (emoji)', max_length=8, blank=True)
    image = models.ImageField(
        'Rasm', upload_to='currency/', blank=True, null=True,
        help_text='Valyuta uchun rasm (masalan, oltin tanga).',
    )
    is_active = models.BooleanField('Faol', default=True)
    is_featured = models.BooleanField(
        'Bosh sahifada', default=False,
        help_text='Bosh sahifadagi medalyon va grafikda ko‘rsatiladi. '
                  'Ko‘p valyuta belgilansa grafik o‘qilmay qoladi — 3-4 tadan oshirmang.',
    )
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Valyuta'
        verbose_name_plural = 'Valyutalar'
        ordering = ['order', 'code']

    def __str__(self):
        return self.code

    @property
    def latest_rate(self):
        """Eng so'nggi kurs yozuvi (ticker/widget uchun)."""
        return self.rates.order_by('-date').first()


class CurrencyRate(models.Model):
    """Bir kunlik valyuta kursi.

    Har kuni har valyuta uchun bittadan yozuv → grafik va
    "o'zgarish" (↑/↓) shu tarixdan hisoblanadi. Manba: CBU API (cbu.uz).
    """
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE,
        related_name='rates', verbose_name='Valyuta',
    )
    rate = models.DecimalField('Kurs (so‘m)', max_digits=12, decimal_places=2)
    diff = models.DecimalField(
        'O‘zgarish', max_digits=10, decimal_places=2, default=0,
        help_text='Bir kun oldingi kursga nisbatan (+ oshgan, − tushgan)',
    )
    date = models.DateField('Sana')

    class Meta:
        verbose_name = 'Valyuta kursi'
        verbose_name_plural = 'Valyuta kurslari'
        ordering = ['-date']
        # Bir valyuta uchun bir kunda faqat bitta kurs
        unique_together = ('currency', 'date')
        indexes = [
            models.Index(fields=['currency', '-date']),
        ]

    def __str__(self):
        return f'{self.currency.code} — {self.rate} ({self.date})'

    @property
    def is_up(self):
        return self.diff > 0

    @property
    def is_down(self):
        return self.diff < 0
