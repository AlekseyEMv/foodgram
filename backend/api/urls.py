from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUserViewSet, IngredientsViewSet, RecipesViewSet, TagsViewSet
)

router = DefaultRouter()
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
# router.register('recipes/download_shopping_cart', ..., basename='get_shopping_cart')
# router.register(r'recipes/{id}/favorite/', ..., basename='favorite')
# router.register(r'recipes/(?P<recipe_id>\d+)/get-link', ..., basename='get_link')
# router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart/', ..., basename='shopping_cart')
router.register('tags', TagsViewSet, basename='tags')
router.register('users', CustomUserViewSet, basename='users')
# router.register(r'users/set password', ..., basename='set_password')
# router.register(r'users/(?P<user_id>\d+)/subscribe/', ..., basename='subscribe')
# router.register('users/subscriptions', ..., basename='subscriptions')


auth_patterns = [
    # path('token/login/', ..., name='login'),
    # path('token/logout/', ..., name='logout'),
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('', include(router.urls)),
]
