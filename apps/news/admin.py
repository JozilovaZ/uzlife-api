from django.contrib import admin
from django.utils.html import format_html

from .models import Article, ArticleImage, Category


class ArticleImageInline(admin.TabularInline):
    """Yangilik detalida qo‘shimcha rasmlarni shu yerdan qo‘shish mumkin."""
    model = ArticleImage
    extra = 1
    fields = ('image', 'thumb', 'caption', 'order')
    readonly_fields = ('thumb',)

    @admin.display(description='Ko‘rinishi')
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:90px;border-radius:6px;">',
                obj.image.url,
            )
        return '—'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'articles_count')
    list_editable = ('order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'id')

    @admin.display(description='Yangiliklar soni')
    def articles_count(self, obj):
        return obj.articles.count()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'status', 'is_featured',
        'views_count', 'published_at',
    )
    list_filter = ('status', 'is_featured', 'category', 'published_at')
    list_editable = ('status', 'is_featured')
    search_fields = ('title', 'summary', 'body')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('category',)
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'cover_preview')
    list_per_page = 30
    actions = ('make_published', 'make_draft', 'make_featured')
    inlines = (ArticleImageInline,)

    fieldsets = (
        ('Asosiy', {
            'fields': ('title', 'slug', 'category', 'author'),
        }),
        ('Matn', {
            'fields': ('summary', 'body', 'cover_image', 'cover_preview'),
        }),
        ('Nashr', {
            'fields': ('status', 'is_featured', 'published_at'),
        }),
        ('Statistika', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Muqova')
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height:160px;border-radius:8px;">',
                obj.cover_image.url,
            )
        return '—'

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='Tanlanganlarni e’lon qilish')
    def make_published(self, request, queryset):
        updated = queryset.update(status=Article.Status.PUBLISHED)
        self.message_user(request, f'{updated} ta yangilik e’lon qilindi.')

    @admin.action(description='Tanlanganlarni qoralamaga o‘tkazish')
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Article.Status.DRAFT)
        self.message_user(request, f'{updated} ta yangilik qoralamaga o‘tkazildi.')

    @admin.action(description='Bosh sahifada (katta) qilib belgilash')
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} ta yangilik tanlandi.')
