"""UzLife API serializerlari.

Kontent maydonlari (title, body, name...) modeltranslation orqali faol tilga
mos qiymatni qaytaradi — LanguageMixin so‘rovdagi tilni faollashtiradi.
"""
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.currency.models import Currency, CurrencyRate
from apps.news.models import Article, ArticleImage, Category, Comment
from apps.weather.models import City, HourlyForecast, WeatherForecast


# ---------- Auth / foydalanuvchi ----------
class RegisterSerializer(serializers.ModelSerializer):
    """Ro‘yxatdan o‘tish. Email majburiy va noyob, parol ikki marta tekshiriladi."""
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'},
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'},
        label=_('Parolni takrorlang'),
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2',
                  'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_('Bu email allaqachon ro‘yxatdan o‘tgan.'))
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(_('Bu foydalanuvchi nomi allaqachon band.'))
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password2': _('Parollar mos kelmadi.')})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_staff', 'date_joined')


# ---------- News ----------
class CategorySerializer(serializers.ModelSerializer):
    articles_count = serializers.IntegerField(source='articles.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'order', 'articles_count')


class ArticleListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='api:article-detail', lookup_field='slug')

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'summary', 'category', 'category_name',
            'cover_image', 'is_featured', 'views_count', 'published_at', 'url',
        )


class ArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImage
        fields = ('id', 'image', 'caption', 'order')


class ArticleDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author = serializers.CharField(source='author.username', read_only=True, default=None)
    images = ArticleImageSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'summary', 'body', 'cover_image', 'images',
            'category', 'author', 'status', 'is_featured', 'views_count',
            'comments_count', 'published_at', 'created_at', 'updated_at',
        )

    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()


class ArticleWriteSerializer(serializers.ModelSerializer):
    """Yangilik yaratish/tahrirlash. Kategoriya slug orqali beriladi.

    `author` avtomatik — so‘rov yuborgan foydalanuvchi. `slug` bo‘sh qoldirilsa
    sarlavhadan hosil bo‘ladi.
    """
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'summary', 'body', 'cover_image',
            'category', 'status', 'is_featured', 'published_at',
        )
        extra_kwargs = {'slug': {'required': False}}

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """Yangilik ostidagi izoh.

    O‘qishda `display_name` — muallif ismi (foydalanuvchi yoki mehmon).
    Yozishda: kirgan foydalanuvchi uchun ism avtomatik; mehmon `author_name`
    yuboradi. `parent` — javob (reply) uchun ixtiyoriy.
    """
    display_name = serializers.CharField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'article', 'author', 'author_name', 'display_name',
            'parent', 'body', 'created_at', 'replies',
        )
        read_only_fields = ('article', 'author', 'created_at')

    def get_replies(self, obj):
        # Faqat yuqori darajadagi izohlar ostida tasdiqlangan javoblar
        if obj.parent_id:
            return []
        qs = obj.replies.filter(is_approved=True)
        return CommentSerializer(qs, many=True, context=self.context).data

    def validate(self, attrs):
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            if not attrs.get('author_name', '').strip():
                raise serializers.ValidationError(
                    {'author_name': _('Ism majburiy (yoki tizimga kiring).')})
        parent = attrs.get('parent')
        if parent is not None:
            article = self.context.get('article')
            if article is not None and parent.article_id != article.id:
                raise serializers.ValidationError(
                    {'parent': _('Javob shu yangilikning izohiga tegishli emas.')})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['article'] = self.context['article']
        if request.user.is_authenticated:
            validated_data['author'] = request.user
            validated_data['author_name'] = ''
        return super().create(validated_data)


# ---------- Currency ----------
class CurrencyRateSerializer(serializers.ModelSerializer):
    is_up = serializers.BooleanField(read_only=True)
    is_down = serializers.BooleanField(read_only=True)

    class Meta:
        model = CurrencyRate
        fields = ('id', 'rate', 'diff', 'is_up', 'is_down', 'date')


class CurrencySerializer(serializers.ModelSerializer):
    latest_rate = CurrencyRateSerializer(read_only=True)

    class Meta:
        model = Currency
        fields = (
            'id', 'code', 'name', 'symbol', 'flag_emoji', 'image',
            'is_active', 'is_featured', 'order', 'latest_rate',
        )


# ---------- Weather ----------
class WeatherForecastSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(
        source='get_condition_display', read_only=True)
    icon = serializers.CharField(read_only=True)

    class Meta:
        model = WeatherForecast
        fields = (
            'id', 'date', 'temp_now', 'temp_min', 'temp_max',
            'condition', 'condition_display', 'icon',
        )


class HourlyForecastSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(
        source='get_condition_display', read_only=True)
    icon = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)

    class Meta:
        model = HourlyForecast
        fields = (
            'id', 'date', 'hour', 'label', 'temp', 'feels',
            'condition', 'condition_display', 'icon',
        )


class CitySerializer(serializers.ModelSerializer):
    today = WeatherForecastSerializer(source='today_forecast', read_only=True)

    class Meta:
        model = City
        fields = (
            'id', 'name', 'slug', 'latitude', 'longitude',
            'is_default', 'is_active', 'order', 'today',
        )
