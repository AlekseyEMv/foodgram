import logging

from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from foodgram_backend.settings import MIN_COOKING_TIME
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            Shopping, Tag)
from rest_framework import serializers as ss
from rest_framework.exceptions import PermissionDenied
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN
from users.models import Follow
from .validators import validate_image_format, validate_username_characters
from .mixins import SubscriptionValidationMixin

User = get_user_model()

logger = logging.getLogger(__name__)


class CustomUserSerializer(UserSerializer):
    is_subscribed = ss.SerializerMethodField(
        help_text='Флаг подписки текущего пользователя на данного пользователя'
    )
    avatar = ss.SerializerMethodField(
        help_text='Аватар текущего пользователя.'
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            },
            'username': {
                'required': True,
                'validators': [
                    UniqueValidator(queryset=User.objects.all()),
                    validate_username_characters
                ]
            },
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.following.filter(user=request.user).exists()

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else ''


class AvatarSerializer(ss.ModelSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True,
        max_length=AVATAR_MAX_LENGTH,
        validators=[validate_image_format],
        help_text="Аватар пользователя в формате base64"
    )

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {
                'required': False,
                'allow_null': True
            }
        }


class CustomUserCreateSerializer(UserSerializer):
    password = ss.CharField(
        write_only=True,
        required=True,
        min_length=MIN_PASSWORD_LEN,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            },
            'username': {
                'required': True,
                'validators': [
                    UniqueValidator(queryset=User.objects.all()),
                    validate_username_characters
                ]
            },
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = True
        for field in ['email', 'username', 'first_name', 'last_name']:
            self.fields[field].required = True

    def create(self, validated_data):
        return self.create_user(validated_data)

    def create_user(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class IngredientsSerializer(ss.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeGetSerializer(ss.Serializer):
    id = ss.IntegerField(source='ingredient.id', read_only=True)
    name = ss.CharField(source='ingredient.name', read_only=True)
    measurement_unit = ss.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = ss.IntegerField(read_only=True)

    def to_representation(self, instance):
        try:
            if not isinstance(instance, IngredientRecipe):
                raise ValueError('Ожидался объект IngredientRecipe')
            return super().to_representation(instance)

        except Exception as e:
            raise ss.ValidationError({
                'error': str(e),
                'instance': instance,
                'type': type(instance).__name__
            })


class IngredientRecipeSerializer(ss.Serializer):
    id = ss.IntegerField(write_only=True)
    name = ss.CharField(read_only=True)
    measurement_unit = ss.CharField(read_only=True)
    amount = ss.IntegerField()

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError(
                'Количество должно быть положительным числом.'
            )
        return value

    def get_ingredient(self, ingredient_id):
        try:
            return Ingredient.objects.get(id=ingredient_id)
        except ObjectDoesNotExist:
            raise ValidationError(
                f'Ингредиент с ID {ingredient_id} не найден.'
            )

    def validate_recipe_context(self):
        recipe = self.context.get('recipe')
        if not recipe:
            raise ValidationError('Рецепт не передан в контексте.')
        return recipe

    def validate_ingredient_uniqueness(
        self, ingredient, recipe, instance=None
    ):
        if IngredientRecipe.objects.filter(
                ingredient=ingredient,
                recipe=recipe
        ).exclude(id=instance.id if instance else None).exists():
            raise ValidationError(
                'Этот ингредиент уже используется в рецепте.'
            )

    def create(self, validated_data):
        try:
            recipe = self.validate_recipe_context()
            ingredient_id = validated_data.pop('id')
            ingredient = self.get_ingredient(ingredient_id)

            return IngredientRecipe.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=validated_data['amount']
            )
        except Exception as e:
            raise ValidationError(f'Ошибка создания: {str(e)}')

    def update(self, instance, validated_data):
        try:
            recipe = self.validate_recipe_context()
            new_amount = validated_data.get('amount')
            instance.amount = new_amount

            if 'id' in validated_data:
                ingredient_id = validated_data['id']
                ingredient = self.get_ingredient(ingredient_id)
                self.validate_ingredient_uniqueness(
                    ingredient, recipe, instance
                )
                instance.ingredient = ingredient

            instance.save()
            return instance
        except Exception as e:
            raise ValidationError(f'Ошибка обновления: {str(e)}')

    def to_representation(self, instance):
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }


class TagsReadSerializer(ss.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class TagsWriteSerializer(TagsReadSerializer):
    id = ss.IntegerField(write_only=True)
    name = ss.CharField(read_only=True)
    slug = ss.CharField(read_only=True)

    def validate_name(self, value):
        if not value:
            raise ss.ValidationError('Название тега не может быть пустым.')
        return value

    def validate_id(self, value):
        try:
            tag = Tag.objects.get(id=value)
            self.tag_instance = tag
            return value
        except Tag.DoesNotExist:
            raise ValidationError(f'Тег с ID {value} не найден')

    def to_internal_value(self, data):
        if not isinstance(data, int):
            raise ValidationError('Ожидался ID тега')
        return {'id': data}

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'slug': instance.slug
        }



class BaseRecipeSerializer(ss.ModelSerializer):
    image = Base64ImageField(validators=[validate_image_format],)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipesGetSerializer(BaseRecipeSerializer):
    tags = TagsReadSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeGetSerializer(
        many=True, source='ingredientrecipe_set'
    )
    is_favorited = ss.SerializerMethodField()
    is_in_shopping_cart = ss.SerializerMethodField()

    class Meta:
        model = Recipe
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
            if hasattr(recipe, 'favorite_recipe_set'):
                return recipe.favorite_recipe_set.filter(
                    user=request.user
                ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_recipe_set.filter(
                user=request.user
            ).exists()
        return False


class RecipesSerializer(BaseRecipeSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = TagsWriteSerializer(many=True, required=True)
    cooking_time = ss.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=(f'Время приготовления не может быть менее '
                         f'{MIN_COOKING_TIME} минуты.')
            ),
        ],
    )

    class Meta:
        model = Recipe
        fields = BaseRecipeSerializer.Meta.fields + (
            'text', 'ingredients', 'tags',
        )
        extra_kwargs = {'image': {'required': True}}

    def validate_collection(self, items, model, error_prefix):
        if not items:
            raise ValidationError(f'{error_prefix} не могут быть пустыми')

        item_ids = [item['id'] for item in items]

        if len(item_ids) != len(set(item_ids)):
            raise ValidationError(
                f'В рецепте не могут быть повторяющиеся {error_prefix.lower()}'
            )

        existing_ids = set(
            model.objects.filter(id__in=item_ids)
            .values_list('id', flat=True)
        )

        missing_items = set(item_ids) - existing_ids
        if missing_items:
            error_message_ids = ', '.join(map(str, missing_items))
            raise ValidationError(
                f'Не найдены {error_prefix.lower()} с ID: {error_message_ids}'
            )

        return items

    def validate_tags(self, tags):
        return self.validate_collection(
            items=tags,
            model=Tag,
            error_prefix='Теги'
        )

    def validate_ingredients(self, ingredients):
        return self.validate_collection(
            items=ingredients,
            model=Ingredient,
            error_prefix='Ингредиенты'
        )

    def validate_image(self, image):
        if not image:
            raise ValidationError('Изображение не может быть пустым.')
        return image

    def save_tags(self, tags_data, instance):
        if not tags_data:
            raise ValidationError('Теги не предоставлены')
        tag_ids = [tag['id'] for tag in tags_data]
        instance.tags.set(tag_ids)

    def save_ingredients(self, ingredients_data, recipe):
        try:
            if not ingredients_data:
                raise ValidationError('Ингредиенты не предоставлены')

            IngredientRecipe.objects.filter(recipe=recipe).delete()
            ingredient_recipes = [
                IngredientRecipe(
                    ingredient_id=ingredient_data['id'],
                    recipe=recipe,
                    amount=ingredient_data['amount']
                )
                for ingredient_data in ingredients_data
            ]

            IngredientRecipe.objects.bulk_create(ingredient_recipes)

        except Exception as e:
            raise ValidationError(f'Ошибка сохранения ингредиентов: {str(e)}')

    def create(self, validated_data):
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                raise PermissionDenied('Пользователь не авторизован')

            author = request.user

            tags_data = validated_data.pop('tags')
            ingredients_data = validated_data.pop('ingredients')

            recipe = Recipe.objects.create(
                author=author,
                **validated_data
            )

            self.save_ingredients(ingredients_data, recipe)
            self.save_tags(tags_data, recipe)

            return recipe

        except IntegrityError as e:
            raise ValidationError(f'Ошибка при создании: {str(e)}')
        except Exception as e:
            raise ValidationError(f'Произошла ошибка: {str(e)}')

    def update(self, instance, validated_data):
        try:
            instance.name = validated_data.get('name', instance.name)
            instance.image = validated_data.get('image', instance.image)
            instance.text = validated_data.get('text', instance.text)
            instance.cooking_time = validated_data.get(
                'cooking_time', instance.cooking_time
            )

            tags_data = validated_data.pop('tags', [])
            ingredients_data = validated_data.pop('ingredients', [])

            self.save_ingredients(ingredients_data, instance)
            self.save_tags(tags_data, instance)

            instance.save()

            return instance

        except IntegrityError as e:
            raise ValidationError(f'Ошибка при обновлении рецепта: {str(e)}')
        except Exception as e:
            raise ValidationError(f'Произошла ошибка: {str(e)}')


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
        try:
            logger.info(f"Сериализация рецепта {instance.recipe.id}")
            return BaseRecipeSerializer(
                instance.recipe, 
                context={'request': self.context.get('request')}
            ).data
        except Exception as e:
            logger.error(f"Ошибка при сериализации: {str(e)}")
            raise ValidationError("Ошибка при сериализации данных")

    def create(self, validated_data):
        try:
            logger.info(f"Создание записи в корзине покупок для рецепта {validated_data['recipe'].id}")
            
            # Создание записи
            instance = super().create(validated_data)
            logger.info(f"Запись успешно создана: {instance.id}")
            return instance
            
        except ValidationError as ve:
            logger.error(f"Ошибка валидации: {str(ve)}")
            raise
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при создании: {str(e)}")
            raise ValidationError("Произошла ошибка при создании записи")

    def validate(self, attrs):
        try:
            logger.debug("Валидация данных корзины покупок")
            
            # Базовая валидация
            validated_data = super().validate(attrs)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            raise


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


# class SubscribeSerializer(SubscriptionValidationMixin, ss.ModelSerializer):
#     user = ss.PrimaryKeyRelatedField(
#         read_only=True,  # Поле только для чтения
#         required=False,
#         help_text='Текущий пользователь, создающий подписку.'
#     )
    
#     author = ss.PrimaryKeyRelatedField(
#         queryset=User.objects.all(),
#         help_text='Пользователь, на которого подписываемся.'
#     )

#     class Meta:
#         model = Follow
#         fields = ('id', 'user', 'author', 'sub_date')
#         read_only_fields = ('id', 'sub_date', 'user')  # Добавляем user в read_only
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Follow.objects.all(),
#                 fields=('author', 'user'),
#                 message='Вы уже подписаны на этого пользователя.'
#             )
#         ]

#     def create(self, validated_data):
#         # Явно указываем user при создании подписки
#         request = self.context.get('request')
#         user = request.user
#         author = validated_data.get('author')
#         return Follow.objects.create(user=user, author=author)
    
#     def to_representation(self, instance):
#         # Этот метод нужен, чтобы правильно отображать данные
#         return super().to_representation(instance)
class SubscribeSerializer(SubscriptionValidationMixin, ss.ModelSerializer):
    user = ss.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        help_text='Текущий пользователь, создающий подписку.'
    )
    
    author = ss.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text='Пользователь, на которого подписываемся.'
    )

    class Meta:
        model = Follow
        fields = ('id', 'user', 'author', 'sub_date')
        read_only_fields = ('id', 'sub_date', 'user')
        

    def validate(self, attrs):
        user = self.context['request'].user
        author = attrs['author']
        if user == author:
            raise ss.ValidationError(Warnings.SELF_SUBSCRIBE_FORBIDDEN)
        
        if Follow.objects.filter(user=user, author=author).exists():
            raise ss.ValidationError(Warnings.SUBSCRIPTION_ALREADY_EXISTS)
        
        return attrs
        # attrs['user'] = user
        
        # Добавляем проверку уникальности
        # if Follow.objects.filter(user=user, author=attrs['author']).exists():
        #     raise ss.ValidationError({
        #         'user': 'Вы уже подписаны на этого пользователя.'
        #     })
        
        # return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']
        return Follow.objects.create(user=user, author=author)





class SetPasswordSerializer(ss.Serializer):
    current_password = ss.CharField(required=True)
    new_password = ss.CharField(required=True, min_length=8)

    def validate_current_password(self, value):
        try:
            request = self.context.get('request')
            if not request:
                logger.error("Контекст запроса отсутствует")
                raise ValueError("Контекст запроса не найден")

            user = request.user
            if not user:
                logger.error("Пользователь не определен в запросе")
                raise ValueError("Пользователь не определен")

            logger.info(f"Проверка текущего пароля для пользователя {user.id}")
            
            # Проверяем пароль
            if not user.check_password(value):
                logger.warning(f"Неверный текущий пароль для пользователя {user.id}")
                raise ss.ValidationError("Неверный текущий пароль")
            
            return value
        
        except Exception as e:
            logger.error(f"Ошибка проверки текущего пароля: {str(e)}")
            raise

    def validate_new_password(self, value):
        try:
            logger.info("Валидация нового пароля")
            
            # Проверяем длину пароля
            if len(value) < 8:
                logger.warning("Новый пароль слишком короткий")
                raise ss.ValidationError("Пароль должен быть не менее 8 символов")
            
            # Можно добавить дополнительные проверки пароля
            # Например, проверка на наличие специальных символов
            
            return value
        
        except Exception as e:
            logger.error(f"Ошибка валидации нового пароля: {str(e)}")
            raise

    def validate(self, data):
        try:
            logger.info("Общая валидация данных")
            
            # Здесь можно добавить дополнительные проверки
            if data['current_password'] == data['new_password']:
                logger.warning("Новый пароль совпадает со старым")
                raise ss.ValidationError("Новый пароль не может совпадать со старым")
            
            return data
        
        except Exception as e:
            logger.error(f"Ошибка общей валидации: {str(e)}")
            raise