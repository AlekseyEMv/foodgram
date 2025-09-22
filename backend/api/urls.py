from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet, RecipesViewSet, SetPasswordView,
                       ShoppingPDFView, TagsViewSet,
                       UserProfileViewSet)

app_name = 'api'

# Основной роутер
router = DefaultRouter()
router.register('users', UserProfileViewSet, basename='users')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/set_password/', SetPasswordView.as_view(), name='set_password'
    ),
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),
    path('', include(router.urls)),
]
