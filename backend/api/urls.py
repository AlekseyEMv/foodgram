from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet, RecipesViewSet, ShoppingPDFView,
                       SubscribeViewSet, TagsViewSet, UserProfileViewSet)

app_name = 'api'

# Основной роутер
router = DefaultRouter()
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')

# Роутер для подписки
subscribe_router = DefaultRouter()
subscribe_router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    SubscribeViewSet,
    basename='subscribe'
)

urlpatterns = [
    # Аутентификация через Djoser
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    # Пользовательские эндпоинты
    path(
        'users/me/', UserProfileViewSet.as_view({'get': 'me'}), name='user-me'
    ),
    path(
        'users/me/avatar/',
        UserProfileViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='user-avatar'
    ),
    path(
        'users/subscriptions/',
        UserProfileViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),

    # Основные маршруты
    path('', include(router.urls)),
    path('', include(subscribe_router.urls)),

    # Другие маршруты
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),
]
