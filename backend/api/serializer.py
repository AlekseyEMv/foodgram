from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss


from recipes.models import (
    Ingredient,
    IngredientRecipe,
    FavoriteRecipe,
    Follow,
    Recipe,
    ShoppingRecipe,
    Tag
)

User = get_user_model()


class IngredientSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Отвечает за преобразование объектов модели Ingredient в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
