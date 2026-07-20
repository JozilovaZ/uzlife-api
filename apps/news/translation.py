from modeltranslation.translator import TranslationOptions, register

from .models import Article, ArticleImage, Category


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('title', 'summary', 'body')


@register(ArticleImage)
class ArticleImageTranslationOptions(TranslationOptions):
    fields = ('caption',)
