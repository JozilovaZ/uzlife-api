from django.db import models
from django.utils import timezone


class City(models.Model):
    """Shahar. Koordinata kerak — Open-Meteo lat/lon bilan ishlaydi."""
    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug (URL)', max_length=120, unique=True)
    latitude = models.FloatField('Kenglik (lat)')
    longitude = models.FloatField('Uzunlik (lon)')
    is_default = models.BooleanField(
        'Asosiy shahar', default=False,
        help_text='Ticker va bosh sahifada ko‘rsatiladi (odatda Toshkent)',
    )
    is_active = models.BooleanField('Faol', default=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Shahar'
        verbose_name_plural = 'Shaharlar'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def today_forecast(self):
        """Bugungi prognoz (ticker/widget uchun)."""
        return self.forecasts.filter(date=timezone.localdate()).first()

    @property
    def upcoming_forecasts(self):
        """Bugundan boshlab keyingi kunlar (widget uchun)."""
        return self.forecasts.filter(date__gte=timezone.localdate()).order_by('date')

    def hourly_for(self, date):
        """Berilgan kun uchun soatlik prognoz (00:00 → 23:00)."""
        return self.hourly.filter(date=date).order_by('hour')


class WeatherForecast(models.Model):
    """Bir shahar uchun bir kunlik ob-havo prognozi.

    Har shahar uchun bir necha kun saqlanadi:
    ticker → bugun, widget → 3 kun, to'liq bo'lim → hammasi.
    Manba: Open-Meteo (bepul, API kalitsiz).
    """

    class Condition(models.TextChoices):
        CLEAR = 'clear', 'Ochiq ☀️'
        PARTLY = 'partly', 'Bulutli ochiq ⛅'
        CLOUDY = 'cloudy', 'Bulutli ☁️'
        FOG = 'fog', 'Tuman 🌫'
        RAIN = 'rain', 'Yomg‘ir 🌧'
        SNOW = 'snow', 'Qor ❄️'
        THUNDER = 'thunder', 'Momaqaldiroq ⛈'

    city = models.ForeignKey(
        City, on_delete=models.CASCADE,
        related_name='forecasts', verbose_name='Shahar',
    )
    date = models.DateField('Sana')
    temp_now = models.SmallIntegerField('Hozirgi harorat (°C)', null=True, blank=True)
    temp_min = models.SmallIntegerField('Eng past (°C)')
    temp_max = models.SmallIntegerField('Eng baland (°C)')
    condition = models.CharField(
        'Holat', max_length=12, choices=Condition.choices, default=Condition.CLEAR,
    )

    class Meta:
        verbose_name = 'Ob-havo prognozi'
        verbose_name_plural = 'Ob-havo prognozlari'
        ordering = ['city', 'date']
        # Bir shahar uchun bir kunda bitta prognoz
        unique_together = ('city', 'date')
        indexes = [
            models.Index(fields=['city', 'date']),
        ]

    def __str__(self):
        return f'{self.city.name} — {self.date} ({self.temp_max}°/{self.temp_min}°)'

    # Holat → Font Awesome ikonkasi (shablonlar shu yerdan oladi)
    ICONS = {
        Condition.CLEAR: 'fa-sun',
        Condition.PARTLY: 'fa-cloud-sun',
        Condition.CLOUDY: 'fa-cloud',
        Condition.FOG: 'fa-smog',
        Condition.RAIN: 'fa-cloud-rain',
        Condition.SNOW: 'fa-snowflake',
        Condition.THUNDER: 'fa-cloud-bolt',
    }

    @property
    def icon(self):
        return self.ICONS.get(self.condition, 'fa-cloud-sun')

    @property
    def is_today(self):
        return self.date == timezone.localdate()

    @property
    def weekday_short(self):
        """Du, Se, Ch, Pa, Ju, Sh, Ya — widget ostidagi kichik yorliq."""
        return ('Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya')[self.date.weekday()]


class HourlyForecast(models.Model):
    """Bir shahar uchun bir soatlik ob-havo (kun tafsilotida ko'rsatiladi).

    Manba: Open-Meteo hourly. Har kun uchun 24 ta yozuv.
    """

    city = models.ForeignKey(
        City, on_delete=models.CASCADE,
        related_name='hourly', verbose_name='Shahar',
    )
    date = models.DateField('Sana')
    hour = models.PositiveSmallIntegerField('Soat (0–23)')
    temp = models.SmallIntegerField('Harorat (°C)')
    feels = models.SmallIntegerField('His qilinishi (°C)', null=True, blank=True)
    condition = models.CharField(
        'Holat', max_length=12,
        choices=WeatherForecast.Condition.choices,
        default=WeatherForecast.Condition.CLEAR,
    )

    class Meta:
        verbose_name = 'Soatlik ob-havo'
        verbose_name_plural = 'Soatlik ob-havo'
        ordering = ['city', 'date', 'hour']
        unique_together = ('city', 'date', 'hour')
        indexes = [
            models.Index(fields=['city', 'date', 'hour']),
        ]

    def __str__(self):
        return f'{self.city.name} — {self.date} {self.hour:02d}:00 ({self.temp}°)'

    @property
    def icon(self):
        return WeatherForecast.ICONS.get(self.condition, 'fa-cloud-sun')

    @property
    def label(self):
        """00:00, 01:00 … — soat yorlig'i."""
        return f'{self.hour:02d}:00'
