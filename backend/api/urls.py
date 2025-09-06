from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUsersViewSet,
    IngredientsViewSet,
    RecipesViewSet,
    ShoppingPDFView,
    SubscribeViewSet,
    TagsViewSet
)

app_name = 'api'

router = DefaultRouter()
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')
router.register('users', CustomUsersViewSet, basename='users')
router.register(
    r'users/(?P<user_id>\d+)/subscribe/',
    SubscribeViewSet,
    basename='subscribe')


auth_patterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        ShoppingPDFView.as_view(),
        name='shopping-pdf'
    ),
    re_path(r'^auth/', include(auth_patterns)),
    path('', include(router.urls)),
]
