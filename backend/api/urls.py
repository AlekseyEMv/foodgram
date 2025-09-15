from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet, RecipesViewSet, SetPasswordView,
                       ShoppingPDFView, SubscribeViewSet, TagsViewSet,
                       UserProfileViewSet)

app_name = 'api'

# Основной роутер
router = DefaultRouter()
router.register('users', UserProfileViewSet, basename='users')
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
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/set_password/', SetPasswordView.as_view(), name='set_password'
    ),
    path('', include(router.urls)),
    path('', include(subscribe_router.urls)),
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),
]
