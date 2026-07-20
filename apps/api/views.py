"""UzLife API viewsetlari."""
from django.utils import translation
from rest_framework import generics, permissions, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.translit import to_cyrillic
from apps.currency.models import Currency
from apps.news.models import Article, Category
from apps.weather.models import City

from .permissions import IsAuthorOrStaffOrReadOnly
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    CitySerializer,
    CurrencySerializer,
    HourlyForecastSerializer,
    RegisterSerializer,
    UserSerializer,
    WeatherForecastSerializer,
)

SUPPORTED_LANGS = {'uz', 'uz-cyrl', 'ru', 'en'}


def _translit_data(data):
    """uz-cyrl uchun javobdagi barcha matnlarni kirillga o‘giradi."""
    if isinstance(data, dict):
        return {k: _translit_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_translit_data(v) for v in data]
    if isinstance(data, str):
        return to_cyrillic(data)
    return data


class LanguageMixin:
    """?lang=uz|uz-cyrl|ru|en — kontent tilini tanlaydi.

    uz-cyrl modeltranslation'da yo‘q → uz (lotin) olinadi, so‘ng javob kirillga
    o‘giriladi.
    """

    def initial(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        if lang not in SUPPORTED_LANGS:
            lang = translation.get_language_from_request(request) or 'uz'
        self._req_lang = lang
        translation.activate('uz' if lang == 'uz-cyrl' else lang)
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if getattr(self, '_req_lang', None) == 'uz-cyrl' and response.data is not None:
            response.data = _translit_data(response.data)
        return response


# ---------- Bosh sahifa ----------
class HomeView(LanguageMixin, views.APIView):
    """Bosh sahifa uchun yig‘ma ma’lumot: ob-havo + valyuta + yangiliklar.

    Frontend bosh sahifani bitta so‘rov bilan to‘ldiradi. Ob-havo — standart
    shahar (Toshkent) bo‘yicha bugungi prognoz bilan.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ctx = {'request': request}

        # Ob-havo: standart (yoki birinchi faol) shahar, bugungi prognoz bilan
        city = (City.objects.filter(is_active=True, is_default=True).first()
                or City.objects.filter(is_active=True).first())
        weather = CitySerializer(city, context=ctx).data if city else None

        # Valyuta: bosh sahifada ko‘rsatiladiganlar (dollar, oltin, ...)
        currencies = (Currency.objects.filter(is_active=True, is_featured=True)
                      .prefetch_related('rates').order_by('order', 'id'))
        currency_data = CurrencySerializer(currencies, many=True, context=ctx).data

        # Yangiliklar: bosh (featured) va so‘nggilar
        published = Article.objects.filter(
            status=Article.Status.PUBLISHED).select_related('category', 'author')
        featured = published.filter(is_featured=True).order_by('-published_at')[:5]
        latest = published.order_by('-published_at')[:10]

        return Response({
            'weather': weather,
            'currencies': currency_data,
            'featured_news': ArticleListSerializer(featured, many=True, context=ctx).data,
            'latest_news': ArticleListSerializer(latest, many=True, context=ctx).data,
        })


# ---------- Auth ----------
class RegisterView(generics.CreateAPIView):
    """Ro‘yxatdan o‘tish. Muvaffaqiyatli bo‘lsa JWT token juftini ham qaytaradi."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=201)


class MeView(generics.RetrieveUpdateAPIView):
    """Joriy foydalanuvchi profili (JWT talab qilinadi)."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------- News ----------
class CategoryViewSet(LanguageMixin, viewsets.ReadOnlyModelViewSet):
    """Yangilik kategoriyalari."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    pagination_class = None


class ArticleViewSet(LanguageMixin, viewsets.ModelViewSet):
    """Yangiliklar (o‘qish + yozish).

    Ro‘yxat/detal hammaga ochiq. Yaratish/tahrirlash/o‘chirish — JWT bilan
    kirgan foydalanuvchiga; tahrir/o‘chirish faqat muallif yoki xodimga.
    Filtr: ?category__slug=&is_featured=&search=&ordering=
    """
    lookup_field = 'slug'
    permission_classes = [IsAuthorOrStaffOrReadOnly]
    filterset_fields = {'category__slug': ['exact'], 'is_featured': ['exact']}
    search_fields = ('title', 'summary', 'body')
    ordering_fields = ('published_at', 'views_count')
    ordering = ('-published_at',)

    def get_queryset(self):
        qs = Article.objects.select_related('category', 'author')
        # Ro‘yxat/detalda faqat e’lon qilinganlar; yozuv amallarida hammasi
        if self.action in ('list', 'retrieve'):
            qs = qs.filter(status=Article.Status.PUBLISHED)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleListSerializer


# ---------- Currency ----------
class CurrencyViewSet(LanguageMixin, viewsets.ReadOnlyModelViewSet):
    """Valyutalar va so‘nggi kurslar."""
    queryset = Currency.objects.filter(is_active=True).prefetch_related('rates')
    serializer_class = CurrencySerializer
    lookup_field = 'code'
    pagination_class = None

    @action(detail=True, methods=['get'])
    def history(self, request, code=None):
        """Valyuta kurslari tarixi (so‘nggi 90 kun)."""
        from .serializers import CurrencyRateSerializer
        currency = self.get_object()
        rates = currency.rates.all()[:90]
        return Response(CurrencyRateSerializer(rates, many=True).data)


# ---------- Weather ----------
class CityViewSet(LanguageMixin, viewsets.ReadOnlyModelViewSet):
    """Shaharlar va ob-havo prognozlari."""
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitySerializer
    lookup_field = 'slug'
    pagination_class = None

    @action(detail=True, methods=['get'])
    def forecast(self, request, slug=None):
        """Bugundan boshlab kunlik prognozlar."""
        city = self.get_object()
        data = WeatherForecastSerializer(city.upcoming_forecasts, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def hourly(self, request, slug=None):
        """Soatlik prognoz. ?date=YYYY-MM-DD (standart: bugun)."""
        from django.utils import timezone
        city = self.get_object()
        date = request.query_params.get('date') or timezone.localdate()
        data = HourlyForecastSerializer(city.hourly_for(date), many=True).data
        return Response(data)
