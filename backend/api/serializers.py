
from functools import partial

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import (MaxLengthValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import (AVATAR_MAX_SIZE, MAX_FILE_SIZE,
                                       MIN_COOKING_TIME, MIN_PASSWORD_LEN,
                                       RECIPE_MAX_LENGTH, RECIPE_MIN_LENGTH)
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            Shopping, Tag)
from users.models import Follow

from .validators import (validate_ids_not_null_unique_collection,
                         validate_image, validate_model_class_instance,
                         validate_picture_format, validate_positive_amount,
                         validate_username_characters,
                         validate_username_not_me)

User = get_user_model()


validate_avatar_picture = partial(
    validate_picture_format, max_file_size=AVATAR_MAX_SIZE
)

validate_recipe_picture = partial(
    validate_image, max_file_size=MAX_FILE_SIZE
)

validate_ingredient_recipe_instance = partial(
    validate_model_class_instance, model_class=IngredientRecipe
)


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для пользовательских данных.

    Включает:
    - Базовые поля пользователя
    - Флаг подписки
    - Информацию об аватаре
    """
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
        """
        Возвращает статус подписки текущего пользователя.

        Возвращает:
        bool: True если подписан на данного пользователя, иначе False.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.following.filter(user=request.user).exists()

    def get_avatar(self, obj):
        """
        Возвращает URL аватара пользователя

        Возвращает:
        str: URL аватара или пустая строка
        """
        return obj.avatar.url if obj.avatar else ''


class AvatarSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с аватаром пользователя.

    Предназначен для загрузки, обновления и удаления аватара пользователя
    в формате base64. Включает валидацию загружаемого изображения.
    """
    avatar = Base64ImageField(
        required=False,
        allow_null=True,
        validators=[validate_avatar_picture],
        help_text='Аватар пользователя в формате base64'
    )

    class Meta:
        """
        Мета-класс конфигурации сериализатора.

        Определяет основные параметры сериализатора:
        - Модель для работы
        - Поля, доступные для сериализации/десериализации
        """
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """
        Метод обновления аватара пользователя.

        Параметры:
        - instance: экземпляр модели User, который обновляется
        - validated_data: валидированные данные для обновления

        Возвращает:
        Обновленный экземпляр модели User
        """
        avatar = validated_data.get('avatar')
        if avatar is not None:
            if instance.avatar and instance.avatar != avatar:
                instance.avatar.delete(save=False)
            instance.avatar = avatar
            instance.save()
        return instance


class CustomUserCreateSerializer(UserSerializer):
    """
    Сериализатор для создания нового пользователя.

    Предназначен для обработки запросов на регистрацию новых пользователей.
    Включает валидацию и создание учетной записи с установкой пароля.
    """
    password = ss.CharField(
        write_only=True,
        required=True,
        min_length=MIN_PASSWORD_LEN,
        style={'input_type': 'password'},
        help_text='Пароль пользователя с ограничением на количество символов'
    )

    class Meta:
        """
        Мета-конфигурация сериализатора.

        Определяет параметры сериализации для модели пользователя:
        - Модель для работы
        - Доступные поля
        - Дополнительные настройки валидации
        """
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
                    validate_username_characters,
                    validate_username_not_me
                ]
            },
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Метод создания нового пользователя.

        Параметры:
        - validated_data: валидированные данные для создания пользователя

        Возвращает:
        - Созданный экземпляр пользователя
        """
        return self.create_user(validated_data)

    def create_user(self, validated_data):
        """
        Метод создания и сохранения пользователя.

        Выполняет:
        - Извлечение пароля
        - Создание пользователя
        - Хэширование и установку пароля
        - Сохранение в базе данных

        Параметры:
        - validated_data: валидированные данные пользователя

        Возвращает:
        Созданный и сохраненный экземпляр пользователя
        """
        password = validated_data.pop('password')
        with transaction.atomic():
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.save()
        return user


class IngredientsSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Предназначен для сериализации и десериализации объектов ингредиентов.
    """

    class Meta:
        """
        Мета-конфигурация сериализатора ингредиентов.

        Определяет параметры работы с моделью ингредиентов:
        - Модель для работы
        - Доступные поля
        """
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeGetSerializer(ss.Serializer):
    """
    Сериализатор для получения информации об ингредиентах в рецепте.

    Предназначен для преобразования объектов IngredientRecipe в JSON-формат.
    Предоставляет информацию об ингредиенте и его количестве в рецепте.
    """
    id = ss.IntegerField(
        source='ingredient.id',
        read_only=True,
        help_text='Уникальный идентификатор ингредиента'
    )
    name = ss.CharField(
        source='ingredient.name',
        read_only=True,
        help_text='Название ингредиента'
    )
    measurement_unit = ss.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
        help_text='Единица измерения ингредиента (грамм, литр и т.д.)'
    )
    amount = ss.IntegerField(
        read_only=True,
        help_text='Количество ингредиента, необходимое для рецепта'
    )

    def to_representation(self, instance):
        """
        Метод преобразования объекта в словарь представления.

        Выполняет:
        - Базовую валидацию типа переданного объекта
        - Преобразование объекта в словарь

        Параметры:
        - instance: объект IngredientRecipe для сериализации

        Возвращает:
        Словарь с данными об ингредиенте и его количестве

        Вызывает:
        - ValidationError при несоответствии типа объекта
        """
        try:
            validate_ingredient_recipe_instance(instance)
            return super().to_representation(instance)
        except ValidationError as e:
            raise e


class IngredientRecipeSerializer(ss.Serializer):
    """
    Сериализатор для работы с ингредиентами в рецепте.

    Отвечает за создание и обновление связей между ингредиентами и рецептами,
    а также за валидацию данных.
    """
    id = ss.IntegerField(
        write_only=True,
        help_text='Уникальный идентификатор ингредиента в базе данных'
    )
    name = ss.CharField(
        read_only=True,
        help_text='Название ингредиента. Поле доступно только для чтения'
    )
    measurement_unit = ss.CharField(
        read_only=True,
        help_text='Единица измерения ингредиента (грамм, миллилитр и т.д.). '
                  'Поле доступно только для чтения'
    )
    amount = ss.IntegerField(
        validators=[validate_positive_amount],
        help_text='Количество ингредиента, необходимое для рецепта. '
                  'Должно быть положительным целым числом'
    )

    def get_ingredient(self, ingredient_id):
        """
        Получает объект ингредиента по его ID.

        Параметры:
        - ingredient_id: ID ингредиента для поиска

        Возвращает:
        - Объект найденного ингредиента

        Вызывает:
        - ValidationError: если ингредиент не найден
        """
        try:
            return Ingredient.objects.get(id=ingredient_id)
        except ObjectDoesNotExist:
            raise ValidationError(Warnings.OBJECT_NOT_FOUND)

    def create(self, validated_data):
        """
        Создает новую связь между ингредиентом и рецептом.

        Параметры:
        - validated_data: валидированные данные для создания

        Возвращает:
        - Созданный объект связи

        Вызывает:
        - ValidationError: при ошибках создания или отсутствии контекста
            рецепта
        """
        try:
            recipe = self.context.get('recipe')
            if not recipe:
                raise ValidationError(Warnings.RECIPE_CONTEXT_MISSING)

            ingredient_id = validated_data.pop('id')
            ingredient = self.get_ingredient(ingredient_id)
            return IngredientRecipe.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=validated_data['amount']
            )
        except ObjectDoesNotExist:
            raise ValidationError(Warnings.OBJECT_NOT_FOUND)
        except Exception as e:
            raise ValidationError(f'Ошибка создания: {str(e)}')

    def update(self, instance, validated_data):
        """
        Обновляет существующую связь между ингредиентом и рецептом.

        Параметры:
        - instance: существующий объект связи
        - validated_data: валидированные данные для обновления

        Возвращает:
        - Обновленный объект связи

        Вызывает:
        - ValidationError: при ошибках обновления
        """
        try:
            new_amount = validated_data.get('amount')
            instance.amount = new_amount

            if 'id' in validated_data:
                ingredient_id = validated_data['id']
                ingredient = self.get_ingredient(ingredient_id)
                instance.ingredient = ingredient

            instance.save()
            return instance
        except ObjectDoesNotExist:
            raise ValidationError(Warnings.OBJECT_NOT_FOUND)
        except Exception as e:
            raise ValidationError(f'Ошибка обновления: {str(e)}')

    def to_representation(self, instance):
        """
        Преобразует объект связи в словарь для вывода.

        Параметры:
        - instance: объект связи для сериализации

        Возвращает:
        - Словарь с данными ингредиента и его количеством
        """
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }


class TagsReadSerializer(ss.ModelSerializer):
    """
    Сериализатор для чтения тегов.

    Предоставляет простой интерфейс для получения информации о тегах.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class TagsWriteSerializer(TagsReadSerializer):
    """
    Сериализатор для работы с тегами при создании и обновлении рецептов.

    Предназначен для проверки существования тегов по их ID и получения
    полной информации о теге при работе с рецептами.
    """
    id = ss.IntegerField(
        write_only=True,
        help_text='Уникальный идентификатор тега в базе данных. '
                  'Обязательное поле для указания существующего тега'
    )
    name = ss.CharField(
        read_only=True,
        help_text='Название тега. '
        'Заполняется автоматически из существующей записи'
    )
    slug = ss.CharField(
        read_only=True,
        help_text='Уникальная машиночитаемая метка тега. '
        'Заполняется автоматически'
    )

    def validate_id(self, value):
        """
        Валидация существования тега по ID.

        Проверяет, существует ли тег с указанным ID в базе данных.
        Если тег не найден, генерирует ошибку валидации.

        Параметр:
        - value: ID тега для проверки

        Возвращает:
        - Валидированный ID тега

        Возбуждает:
        - ValidationError: Если тег с указанным ID не найден
        """
        try:
            tag = Tag.objects.get(id=value)
            self.tag_instance = tag
            return value
        except Tag.DoesNotExist:
            raise ValidationError(f'Тег с ID {value} не найден')

    def to_internal_value(self, data):
        """
        Преобразование входных данных в внутренний формат.

        Проверяет, что входные данные являются целым числом (ID тега).

        Параметр:
        - data: Входные данные для валидации

        Возвращает:
        - Словарь с валидированным ID тега

        Возбуждает:
            ValidationError: Если входные данные не являются целым числом
        """
        if not isinstance(data, int):
            raise ValidationError(Warnings.TAG_ID_REQUIRED)
        return {'id': data}

    def to_representation(self, instance):
        """
        Преобразование объекта тега в формат вывода.

        Формирует словарь с информацией о теге для вывода в API.

        Параметр:
        - instance: Объект тега

        Возвращает:
        - Словарь с полями тега
        """
        return {
            'id': instance.id,
            'name': instance.name,
            'slug': instance.slug
        }


class BaseRecipeSerializer(ss.ModelSerializer):
    """
    Базовый сериализатор для работы с рецептами.

    Предоставляет основную функциональность для создания, обновления
    и получения информации о рецептах.
    """
    image = Base64ImageField(
        required=True,
        validators=[validate_recipe_picture],
        help_text='Изображение рецепта в формате base64. Обязательное поле.'
                  'Должен быть допустимый формат изображения (JPEG, PNG, GIF)'
    )
    name = ss.CharField(
        validators=[
            MinLengthValidator(
                RECIPE_MIN_LENGTH, message=Warnings.NAME_LEN_MIN_REQUIRED
            ),
            MaxLengthValidator(
                RECIPE_MAX_LENGTH, message=Warnings.NAME_LEN_MAX_REQUIRED
            )
        ],
        help_text='Название рецепта с ограничениями на длину символов'
    )
    cooking_time = ss.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME, message=Warnings.COOKING_TIME_MIN_REQUIRED
            )
        ],
        help_text='Время приготовления рецепта в минутах с '
                  'минимальным значением'
    )

    class Meta:
        """
        Мета-информация о сериализаторе.

        Определяет модель и поля, которые будут использоваться
        в сериализаторе.
        """
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipesGetSerializer(BaseRecipeSerializer):
    """
    Сериализатор для получения подробной информации о рецептах.

    Предоставляет расширенный набор полей для отображения рецептов,
    включая информацию об авторах, тегах, ингредиентах и статусах
    в избранном/списке покупок.
    """
    tags = TagsReadSerializer(
        many=True,
        read_only=True,
        help_text='Список тегов, связанных с рецептом'
    )
    author = CustomUserSerializer(
        read_only=True,
        help_text='Информация об авторе рецепта'
    )
    ingredients = IngredientRecipeGetSerializer(
        many=True,
        source='ingredientrecipe_set',
        help_text='Список ингредиентов, используемых в рецепте'
    )
    is_favorited = ss.SerializerMethodField(
        help_text=('Флаг, указывающий, добавлен ли рецепт в избранное '
                   'у текущего пользователя')
    )
    is_in_shopping_cart = ss.SerializerMethodField(
        help_text=('Флаг, указывающий, добавлен ли рецепт в список покупок '
                   'у текущего пользователя')
    )

    class Meta:
        """
        Мета-информация о сериализаторе.

        Определяет модель и набор полей для сериализации.
        """
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
        """
        Возвращает статус добавления рецепта в избранное.

        Параметр:
        - recipe: Объект рецепта

        Возвращает:
        - True, если рецепт в избранном, иначе False
        """
        return self._check_user_relation(
            recipe,
            'favorite_recipe_set'
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Возвращает статус добавления рецепта в список покупок.

        Параметр:
        - recipe: Объект рецепта

        Возвращает:
        - True, если рецепт в списке покупок, иначе False
        """
        return self._check_user_relation(
            obj,
            'shopping_recipe_set'
        )

    def _check_user_relation(self, obj, relation_name):
        """
        Проверяет наличие связи между рецептом и пользователем.

        Параметры:
        - obj: Объект рецепта
        - relation_name: Имя отношения для проверки

        Возвращает:
        - True, если связь существует, иначе False

        Проверяет, существует ли связь между рецептом и текущим
        авторизованным пользователем через указанное отношение.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, relation_name):
                return getattr(obj, relation_name).filter(
                    user=request.user
                ).exists()
        return False


class RecipesSerializer(BaseRecipeSerializer):
    """
    Сериализатор для создания и обновления рецептов.

    Предоставляет функционал для работы с рецептами, включая:
    - Валидацию данных
    - Сохранение тегов и ингредиентов
    - Создание и обновление рецептов
    """
    ingredients = IngredientRecipeSerializer(
        many=True,
        required=True,
        help_text='Список ингредиентов для рецепта. Каждый ингредиент должен '
                  'содержать ID и количество.'
    )
    tags = TagsWriteSerializer(
        many=True,
        required=True,
        help_text='Список тегов, связанных с рецептом. Каждый тег должен '
                  'содержать валидный ID.'
    )

    class Meta:
        """
        Мета-информация о сериализаторе.

        Определяет модель и поля для работы с рецептом.
        """
        model = Recipe
        fields = BaseRecipeSerializer.Meta.fields + (
            'text', 'ingredients', 'tags',
        )

    def validate_tags(self, tags):
        """
        Валидация тегов рецепта.

        Проверяет:
        - Наличие тегов
        - Уникальность ID тегов
        - Существование тегов в базе данных

        Параметр:
        - tags: Список тегов для проверки

        Возвращает:
        - Валидированный список тегов
        """
        return validate_ids_not_null_unique_collection(
            values=tags,
            values_model=Tag,
            values_prefix='tags'
        )

    def validate_ingredients(self, ingredients):
        """
        Валидация ингредиентов рецепта.

        Проверяет:
        - Положительное значение количества для каждого ингредиента
        - Уникальность ID ингредиентов
        - Существование ингредиентов в базе данных

        Параметр:
        - ingredients: Список ингредиентов для проверки

        Возвращает:
        - Валидированный список ингредиентов
        """
        for ingredient in ingredients:
            validate_positive_amount(ingredient['amount'])
        return validate_ids_not_null_unique_collection(
            values=ingredients,
            values_model=Ingredient,
            values_prefix='ingredients'
        )

    @transaction.atomic()
    def save_tags(self, tags_data, instance):
        """
        Сохранение тегов для рецепта.

        Создает связь между рецептом и тегами.

        Параметры:
        - tags_data: Данные тегов для сохранения
        - instance: Экземпляр рецепта
        """
        tag_ids = [tag['id'] for tag in tags_data]
        instance.tags.set(tag_ids)

    @transaction.atomic()
    def save_ingredients(self, ingredients_data, instance):
        """
        Сохранение ингредиентов для рецепта.

        Удаляет старые связи и создает новые записи ингредиентов.

        Параметры:
        - ingredients_data: Данные ингредиентов для сохранения
        - instance: Экземпляр рецепта
        """
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredient_recipes = [
            IngredientRecipe(
                ingredient_id=ingredient_data['id'],
                recipe=instance,
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]

        IngredientRecipe.objects.bulk_create(ingredient_recipes)

    def create(self, validated_data):
        """
        Создание нового рецепта.

        Создает рецепт с указанными тегами и ингредиентами.

        Параметр:
        - validated_data: Валидированные данные для создания

        Возвращает:
        - Созданный экземпляр рецепта
        """
        request = self.context.get('request')
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

    def update(self, instance, validated_data):
        """
        Обновление существующего рецепта.

        Обновляет поля рецепта и связанные теги/ингредиенты.

        Параметры:
        - instance: Экземпляр рецепта для обновления
        - validated_data: Валидированные данные для обновления

        Возвращает:
        - Обновленный экземпляр рецепта
        """
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


class BaseRelationSerializer(ss.ModelSerializer):
    """
    Абстрактный сериализатор для работы пользователя с рецептом.

    Предоставляет общую логику для сериализации связей между пользователем и
    рецептом, включая валидацию уникальности и преобразование данных.
    """
    class Meta:
        """
        Мета-информация для базового сериализатора.

        Определяет общие настройки для всех производных сериализаторов:
        - абстрактная модель
        - базовые поля
        - валидатор уникальности
        """
        abstract = True
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=None,
                fields=('user', 'recipe')
            ),
        ]

    def to_representation(self, instance):
        """
        Преобразование экземпляра в словарь.

        Возвращает сериализованные данные рецепта с учетом контекста запроса.

        Параметр:
        - instance: экземпляр модели отношения

        Возвращает:
        - Словарь с данными рецепта
        """
        return BaseRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingAddSerializer(BaseRelationSerializer):
    """
    Сериализатор для добавления рецептов в список покупок.

    Отвечает за создание и валидацию связей между пользователем и рецептом
    в контексте списка покупок.
    """
    class Meta(BaseRelationSerializer.Meta):
        """
        Мета-информация для сериализатора списка покупок.

        Определяет конкретную модель и настройки валидации.
        """
        model = Shopping
        validators = [
            UniqueTogetherValidator(
                queryset=Shopping.objects.all(),
                fields=('user', 'recipe'),
                message=Warnings.RECIPE_IN_SHOPPING_CART_EXISTS
            ),
        ]


class FavoriteSerializer(BaseRelationSerializer):
    """
    Сериализатор для добавления рецептов в избранное.

    Отвечает за создание и валидацию связей между пользователем и рецептом
    в контексте избранного.
    """
    class Meta(BaseRelationSerializer.Meta):
        """
        Мета-информация для сериализатора избранного.

        Определяет конкретную модель и настройки валидации.
        """
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.select_related('recipe'),
                fields=('user', 'recipe'),
                message=Warnings.RECIPE_IN_FAVORITE_EXISTS
            ),
        ]


class SubscriptionsSerializer(CustomUserSerializer):
    """
    Сериализатор для информации о подписках пользователя.

    Включает базовую информацию о пользователе и дополнительные поля:
    - список рецептов
    - количество рецептов
    """
    recipes = ss.SerializerMethodField(
        method_name='get_recipes',
        read_only=True,
        help_text='Список рецептов пользователя с учетом ограничения'
    )
    recipes_count = ss.SerializerMethodField(
        method_name='get_recipes_count',
        read_only=True,
        help_text='Общее количество рецептов пользователя'
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
        """
        Возвращает количество рецептов пользователя.

        Параметр
        - user: экземпляр пользователя

        Возваращает
        - Количество рецептов
        """
        return user.recipes.count()

    def get_recipes(self, user):
        """
        Возвращает список рецептов пользователя с учетом ограничения.

        Параметр
        - user: экземпляр пользователя

        Возваращает
        - Сериализованные данные рецептов
        """
        request = self.context.get('request')
        if not request:
            return []

        try:
            recipes_limit = request.GET.get('recipes_limit')
            if recipes_limit:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    raise ValueError
            else:
                recipes_limit = None

            recipes = user.recipes.all()
            if recipes_limit:
                recipes = recipes[:recipes_limit]

            serializer = BaseRecipeSerializer(recipes, many=True)
            return serializer.data

        except (ValueError, TypeError):
            raise ValidationError({'recipes_limit': 'Неверное значение'})


class SubscribeSerializer(ss.ModelSerializer):
    """
    Сериализатор для создания и валидации подписок между пользователями.

    Позволяет пользователям подписываться на других пользователей системы.
    Выполняет полную валидацию данных перед созданием подписки.
    """
    user = ss.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        help_text='Идентификатор текущего пользователя, создающего подписку. '
                  'Поле доступно только для чтения и заполняется автоматически'
    )
    author = ss.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text='Пользователь, на которого создается подписка. '
                  'Должен быть активным пользователем системы.'
    )

    class Meta:
        """
        Мета-информация сериализатора.

        Определяет основные параметры сериализации:
        - Модель для работы
        - Доступные поля
        - Поля только для чтения
        """
        model = Follow
        fields = ('id', 'user', 'author', 'sub_date')
        read_only_fields = ('id', 'sub_date', 'user')

    def validate(self, attrs):
        """
        Валидация данных перед созданием подписки.

        Выполняет комплексную проверку всех условий для создания подписки:
        1. Наличие контекста запроса
        2. Аутентификация пользователя
        3. Существование целевого пользователя
        4. Запрет подписки на себя
        5. Проверка активности целевого пользователя
        6. Проверка уникальности подписки

        Параметры:
        - attrs: валидируемые данные

        Возвращает:
        - Валидированные данные

        Вызывает:
        - ValidationError при нарушении любого из условий
        """
        # Получаем контекст запроса
        request = self.context.get('request')
        if not request:
            raise ss.ValidationError(Warnings.REQUEST_CONTEXT_MISSING)

        # Проверяем авторизацию пользователя
        user = request.user
        if not user.is_authenticated:
            raise ss.ValidationError(Warnings.AUTHENTICATION_REQUIRED)

        # Получаем автора из валидируемых данных
        author = attrs.get('author')
        if not author:
            raise ss.ValidationError(Warnings.AUTHOR_REQUIRED)

        # Проверяем запрещенные условия
        if user == author:
            raise ss.ValidationError(Warnings.SELF_SUBSCRIBE_FORBIDDEN)

        if not author.is_active:
            raise ss.ValidationError(Warnings.INACTIVE_USER)

        # Проверяем существование подписки
        if Follow.objects.filter(user=user, author=author).exists():
            raise ss.ValidationError(Warnings.SUBSCRIPTION_ALREADY_EXISTS)

        return attrs

    def create(self, validated_data):
        """
        Создание новой подписки.

        Создает запись в таблице подписок между текущим пользователем
        и указанным автором.

        Параметры:
        - validated_data: валидированные данные для создания

        Возвращает:
        - Созданный объект подписки
        """
        user = self.context['request'].user
        author = validated_data['author']
        return Follow.objects.create(user=user, author=author)


class SetPasswordSerializer(ss.Serializer):
    """
    Сериализатор для смены пароля пользователя.

    Позволяет пользователю изменить пароль, проверив текущий и задав новый.
    """
    current_password = ss.CharField(
        required=True,
        help_text='Текущий пароль пользователя'
    )
    new_password = ss.CharField(
        required=True,
        min_length=MIN_PASSWORD_LEN,
        help_text='Новый пароль пользователя (минимум 8 символов)'
    )

    def validate_current_password(self, value):
        """
        Валидация текущего пароля.

        Проверяет:
        - Наличие контекста запроса
        - Аутентификацию пользователя
        - Корректность текущего пароля
        """
        request = self.context.get('request')
        if not request:
            raise ss.ValidationError(Warnings.REQUEST_CONTEXT_MISSING)

        user = request.user
        if not user:
            raise ss.ValidationError(Warnings.USER_NOT_FOUND)

        if not user.check_password(value):
            raise ss.ValidationError(Warnings.PASSWORD_CURRENT_INVALID)

        return value

    def validate_new_password(self, value):
        """
        Валидация нового пароля.

        Проверяет минимальную длину пароля.
        """
        if len(value) < MIN_PASSWORD_LEN:
            raise ss.ValidationError(
                f'{Warnings.PASSWORD_TOO_SHORT_MESSAGE} '
                f'{MIN_PASSWORD_LEN} символов'
            )
        return value

    def validate(self, data):
        """
        Общая валидация данных.

        Проверяет, что новый пароль не совпадает со старым.
        """
        if data['current_password'] == data['new_password']:
            raise ss.ValidationError(Warnings.PASSWORD_CHANGE_REQUIRED)
        return data

    def save(self):
        """
        Метод для сохранения нового пароля.

        Должен быть реализован в зависимости от логики приложения.
        """
        request = self.context.get('request')
        user = request.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
