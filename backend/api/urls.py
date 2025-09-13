from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUsersViewSet, IngredientsViewSet, RecipesViewSet,
                       ShoppingPDFView, SubscribeViewSet, TagsViewSet)

app_name = 'api'

# Основной роутер
router = DefaultRouter()
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')
router.register('users', CustomUsersViewSet, basename='users')

# Роутер для подписки
subscribe_router = DefaultRouter()
subscribe_router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    SubscribeViewSet,
    basename='subscribe'
)

urlpatterns = [
    # Скачивание списка покупок
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),

    # Аутентификация
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    # Основные маршруты
    path('', include(router.urls)),
    path('', include(subscribe_router.urls)),
]
