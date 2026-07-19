from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('articles', views.ArticleViewSet, basename='article')
router.register('currencies', views.CurrencyViewSet, basename='currency')
router.register('cities', views.CityViewSet, basename='city')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
