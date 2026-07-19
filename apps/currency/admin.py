from django.contrib import admin
from django.utils.html import format_html

from .models import Currency, CurrencyRate


class CurrencyRateInline(admin.TabularInline):
    model = CurrencyRate
    extra = 0
    fields = ('date', 'rate', 'diff')
    ordering = ('-date',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'flag_emoji', 'image_preview', 'is_active', 'is_featured', 'order')
    list_editable = ('is_active', 'is_featured', 'order')
    search_fields = ('code', 'name')
    readonly_fields = ('image_preview',)
    inlines = [CurrencyRateInline]

    @admin.display(description='Rasm')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:6px;">', obj.image.url,
            )
        return '—'


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'diff', 'date')
    list_filter = ('currency', 'date')
    date_hierarchy = 'date'
    ordering = ('-date', 'currency')
