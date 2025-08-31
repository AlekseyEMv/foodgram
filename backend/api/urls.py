from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUserViewSet,
    IngredientsViewSet,
    RecipesViewSet,
    SubscribeViewSet,
    TagsViewSet
)


# router.register('recipes/download_shopping_cart', ..., basename='get_shopping_cart')
# router.register(r'recipes/(?P<recipe_id>\d+)/favorite/', ..., basename='favorite')
# router.register(r'recipes/(?P<recipe_id>\d+)/get-link', ..., basename='get_link')
# router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart/', ..., basename='shopping_cart')
# router.register('users/subscriptions', ..., basename='subscriptions')
app_name = 'api'

router = DefaultRouter()
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')
router.register('users', CustomUserViewSet, basename='users')
router.register(
    r'users/(?P<user_id>\d+)/subscribe/',
    SubscribeViewSet,
    basename='subscribe')


auth_patterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]

urlpatterns = [
    re_path(r'^auth/', include(auth_patterns)),
    path('', include(router.urls)),
]
