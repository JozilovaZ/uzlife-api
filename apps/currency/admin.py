from django.contrib import admin

from .models import Currency, CurrencyRate


class CurrencyRateInline(admin.TabularInline):
    model = CurrencyRate
    extra = 0
    fields = ('date', 'rate', 'diff')
    ordering = ('-date',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'flag_emoji', 'is_active', 'is_featured', 'order')
    list_editable = ('is_active', 'is_featured', 'order')
    search_fields = ('code', 'name')
    inlines = [CurrencyRateInline]


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'diff', 'date')
    list_filter = ('currency', 'date')
    date_hierarchy = 'date'
    ordering = ('-date', 'currency')
