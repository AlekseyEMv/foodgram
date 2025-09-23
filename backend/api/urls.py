from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet, RecipesViewSet, SetPasswordView,
                       ShoppingPDFView, TagsViewSet, UserProfileViewSet)

app_name = 'api'

"""
URL конфигурации для API приложения

Содержит маршруты для:
* Аутентификации
* Управления пользователями
* Работы с рецептами
* Работы с ингредиентами
* Работы с тегами
"""

# Основной роутер
router = DefaultRouter()
router.register('users', UserProfileViewSet, basename='users')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')

urlpatterns = [
    # Аутентификационные эндпоинты
    path('auth/', include('djoser.urls.authtoken')),
    # Специальный эндпоинт для смены пароля
    path(
        'users/set_password/', SetPasswordView.as_view(), name='set_password'
    ),
    # Скачивание списка покупок в PDF формате
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),
    path('', include(router.urls)),
]
