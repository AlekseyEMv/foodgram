from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.exceptions import PermissionDenied
from rest_framework.validators import UniqueTogetherValidator

from foodgram_backend.settings import (INGREDIENT_MAX_LENGTH,
                                       INGRIGIENTS_MIN_VALUE, MIN_COOKING_TIME,
                                       UNIT_MAX_LENGTH)
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            Shopping, Tag)
from users.models import Follow
from users.serializers import CustomUserSerializer

from .mixins import SubscriptionValidationMixin
from .validators import NonEmptyCharField

User = get_user_model()


class IngredientsSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Отвечает за преобразование объектов модели Ingredient в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeSerializer(ss.Serializer):
    ingredient_name = NonEmptyCharField(
        max_length=INGREDIENT_MAX_LENGTH,
        required=True,
    )
    measurement_unit = NonEmptyCharField(
        max_length=UNIT_MAX_LENGTH,
        required=True,
    )
    amount = ss.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=INGRIGIENTS_MIN_VALUE,
                message=(
                    'Количество ингредиентов в рецепте не может быть '
                    f'меньше {INGRIGIENTS_MIN_VALUE}'
                )
            )
        ],
        required=True
    )

    def create(self, validated_data):
        try:
            ingredient_name = validated_data.pop('ingredient_name')
            measurement_unit = validated_data.pop('measurement_unit')
            ingredient, _ = Ingredient.objects.select_for_update(
            ).get_or_create(
                name=ingredient_name,
                measurement_unit=measurement_unit
            )

            validated_data['ingredient'] = ingredient
            return IngredientRecipe.objects.create(**validated_data)
        except IntegrityError as e:
            raise ss.ValidationError(
                f'Ошибка при создании ингредиента: {str(e)}.'
            )

    def update(self, instance, validated_data):
        try:
            new_amount = validated_data.get('amount')
            if new_amount is not None:
                instance.amount = new_amount

            ingredient_name = validated_data.get('ingredient_name')
            measurement_unit = validated_data.get('measurement_unit')

            if ingredient_name or measurement_unit:
                ingredient = instance.ingredient
                if ingredient_name:
                    ingredient.name = ingredient_name
                if measurement_unit:
                    ingredient.measurement_unit = measurement_unit
                ingredient.save()

            instance.save()
            return instance
        except IntegrityError:
            raise ss.ValidationError(
                'Произошла ошибка при обновлении ингредиента.'
            )
        except Exception as e:
            raise ss.ValidationError(
                f'Непредвиденная ошибка: {str(e)}'
            )


class TagsSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с тегами.

    Отвечает за преобразование объектов модели Tags в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class BaseRecipeSerializer(ss.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipesGetSerializer(BaseRecipeSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsSerializer(many=True)
    is_favorited = ss.SerializerMethodField()
    is_in_shopping_cart = ss.SerializerMethodField()

    class Meta:
        fields = BaseRecipeSerializer.Meta.fields + (
            'author',
            'text',
            'ingredients',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return recipe.favorite_recipe.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return recipe.shopping_recipe.filter(user=request.user).exists()
        return False


class RecipesSerializer(BaseRecipeSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = ss.SlugRelatedField(
        slug_field='id',
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    cooking_time = ss.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=('Время приготовления не может быть менее '
                         f'{MIN_COOKING_TIME} минуты.')
            ),
        ],
    )

    class Meta:
        model = Recipe
        fields = BaseRecipeSerializer.Meta.fields + (
            'text',
            'ingredients',
            'tags',
        )
        extra_kwargs = {'image': {'required': True}}

    def create(self, validated_data):
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                raise PermissionDenied('Пользователь не авторизован')

            author = request.user
            ingredients = validated_data.pop('ingredients')
            tags = validated_data.pop('tags')
            recipe = Recipe.objects.create(author=author, **validated_data)
            self.save_ingredients(ingredients, recipe)
            recipe.tags.set(tags)
            return recipe
        except IntegrityError as e:
            raise ss.ValidationError(f'Ошибка при создании рецепта: {str(e)}')

    def update(self, instance, validated_data):
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                raise PermissionDenied('Пользователь не авторизован.')
            current_user = request.user
            if instance.author != current_user:
                raise PermissionDenied('Нет прав на изменение рецепта.')
            ingredients = validated_data.pop('ingredients')
            tags = validated_data.pop('tags')
            if ingredients:
                instance.ingredients.clear()
                self.save_ingredients(ingredients, instance)
            if tags:
                instance.tags.set(tags)
            return super().update(instance, validated_data)
        except Exception as e:
            raise ss.ValidationError(f'Ошибка при обновлении: {str(e)}')

    def save_ingredients(self, ingredients, recipe):
        try:
            ingredient_notations = {
                ingredient.get('id'): ingredient.get('amount')
                for ingredient in ingredients
            }
            existing_ingredient_ids = set(
                IngredientRecipe.objects.filter(recipe=recipe)
                .values_list('ingredient_id', flat=True)
            )
            ingredients_to_delete = (
                existing_ingredient_ids - set(ingredient_notations.keys())
            )
            if ingredients_to_delete:
                IngredientRecipe.objects.filter(
                    recipe=recipe,
                    ingredient_id__in=ingredients_to_delete
                ).delete()
            bulk_update_data = [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient_id=ingredient_id,
                    amount=amount
                )
                for ingredient_id, amount in ingredient_notations.items()
            ]
            IngredientRecipe.objects.bulk_create(
                [
                    obj for obj in bulk_update_data
                    if not IngredientRecipe.objects.filter(
                        recipe=recipe,
                        ingredient_id=obj.ingredient_id
                    ).exists()
                ],
                ignore_conflicts=True
            )

            for obj in bulk_update_data:
                IngredientRecipe.objects.filter(
                    recipe=recipe,
                    ingredient_id=obj.ingredient_id
                ).update(amount=obj.amount)

        except IntegrityError as e:
            raise ss.ValidationError(
                f'Ошибка при сохранении ингредиентов: {str(e)}'
            )
        except Exception as e:
            raise ss.ValidationError(
                f'Произошла непредвиденная ошибка: {str(e)}'
            )


class ShoppingAddSerializer(ss.ModelSerializer):
    class Meta:
        model = Shopping
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Shopping.objects.all(),
                fields=('user', 'recipe'),
            ),
        ]

    def to_representation(self, instance):
        return BaseRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    def create(self, validated_data):
        try:
            return Shopping.objects.create(**validated_data)
        except Exception as e:
            raise ss.ValidationError(str(e))


class FavoriteSerializer(ss.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.select_related('recipe'),
                fields=('user', 'recipe')
            ),
        ]

    def to_representation(self, instance):
        return BaseRecipeSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data


class SubscribeSerializer(SubscriptionValidationMixin, ss.ModelSerializer):
    user = ss.PrimaryKeyRelatedField(
        read_only=True,
        default=ss.CurrentUserDefault(),
        help_text='Текущий пользователь, создающий подписку.'
    )
    author = ss.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text='Пользователь, на которого подписываемся.'
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('author', 'user'),
                message='Вы уже подписаны на этого пользователя.'
            ),
        ]

    def validate(self, data):
        self._validate_context()
        self._validate_user()
        self._validate_author()
        data['author'] = self._get_author()
        return data

    def create(self, validated_data):
        return super().create(validated_data)


class SubscriptionsSerializer(CustomUserSerializer):
    recipes = ss.SerializerMethodField(
        method_name='get_recipes',
        read_only=True
    )
    recipes_count = ss.SerializerMethodField(
        method_name='get_recipes_count',
        read_only=True
    )

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
        )

    def get_recipes_count(self, user):
        return user.recipes.count()

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')

        recipes = user.recipes.all()

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    raise ValueError
                recipes = recipes[:recipes_limit]
            except (ValueError, TypeError):
                raise ValidationError({'recipes_limit': 'Неверное значение'})

        serializer = BaseRecipeSerializer(recipes, many=True)
        return serializer.data
