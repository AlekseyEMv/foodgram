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

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
