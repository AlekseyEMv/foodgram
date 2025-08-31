from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN
from recipes.models import (
    Ingredient,
    IngredientRecipe,
    FavoriteRecipe,    
    Recipe,
    ShoppingRecipe,
    Tag
)


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


class RecipesGetSerializer(ss.ModelSerializer):
    """
    """


class TagSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с тегами.

    Отвечает за преобразование объектов модели Tags в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)