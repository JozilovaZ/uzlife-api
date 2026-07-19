from django.contrib import admin

from .models import City, HourlyForecast, WeatherForecast


class WeatherForecastInline(admin.TabularInline):
    model = WeatherForecast
    extra = 0
    fields = ('date', 'temp_now', 'temp_min', 'temp_max', 'condition')
    ordering = ('date',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'latitude', 'longitude', 'is_default', 'is_active', 'order')
    list_editable = ('is_default', 'is_active', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [WeatherForecastInline]


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ('city', 'date', 'temp_now', 'temp_max', 'temp_min', 'condition')
    list_filter = ('city', 'condition', 'date')
    date_hierarchy = 'date'
    ordering = ('-date', 'city')


@admin.register(HourlyForecast)
class HourlyForecastAdmin(admin.ModelAdmin):
    list_display = ('city', 'date', 'hour', 'temp', 'feels', 'condition')
    list_filter = ('city', 'condition', 'date')
    date_hierarchy = 'date'
    ordering = ('-date', 'city', 'hour')
