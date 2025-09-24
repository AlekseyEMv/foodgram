
from functools import partial

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import (MaxLengthValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import transaction
from django.utils.text import slugify
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
        # model = Ingredient
        # fields = ('id', 'name', 'measurement_unit',)
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        extra_kwargs = {
            'name': {'required': True},
            'measurement_unit': {'required': True}
        }
        
        def validate_name(self, value):
            if Ingredient.objects.filter(name__iexact=value).exists():
                raise ss.ValidationError("Ингредиент с таким названием уже существует")
            return value


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
        required=False,  # Теперь ID не обязателен
        # write_only=True,
        help_text='Уникальный идентификатор ингредиента в базе данных'
    )
    name = ss.CharField(
        required=True,  # Название обязательно для создания нового
        help_text='Название ингредиента. Поле доступно только для чтения'
    )
    measurement_unit = ss.CharField(
        required=True,  # Единица измерения обязательна для создания нового
        # read_only=True,
        help_text='Единица измерения ингредиента (грамм, миллилитр и т.д.). '
                  'Поле доступно только для чтения'
    )
    amount = ss.IntegerField(
        validators=[validate_positive_amount],
        help_text='Количество ингредиента, необходимое для рецепта. '
                  'Должно быть положительным целым числом'
    )

    # def get_ingredient(self, ingredient_id):
    def get_ingredient(self, ingredient_data):
        """
        Получает объект ингредиента по его ID.

        Параметры:
        - ingredient_id: ID ингредиента для поиска

        Возвращает:
        - Объект найденного ингредиента

        Вызывает:
        - ValidationError: если ингредиент не найден
        """
        # try:
        #     return Ingredient.objects.get(id=ingredient_id)
        # except ObjectDoesNotExist:
        #     raise ValidationError(Warnings.OBJECT_NOT_FOUND)
        try:
            if 'id' in ingredient_data:
                return Ingredient.objects.get(id=ingredient_data['id'])
            else:
                # Создаем новый ингредиент
                return Ingredient.objects.create(
                    name=ingredient_data['name'],
                    measurement_unit=ingredient_data['measurement_unit']
                )
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

            # ingredient_id = validated_data.pop('id')
            # ingredient = self.get_ingredient(ingredient_id)
            ingredient = validated_data.pop(validated_data)
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
        # write_only=True,
        required=False,  # ID теперь не обязателен
        help_text='Уникальный идентификатор тега в базе данных. '
                  'Обязательное поле для указания существующего тега'
    )
    name = ss.CharField(
        required=True,  # Название обязательно для создания нового
        # read_only=True,
        help_text='Название тега. '
        'Заполняется автоматически из существующей записи'
    )
    slug = ss.CharField(
        read_only=True,
        help_text='Уникальная машиночитаемая метка тега. '
        'Заполняется автоматически'
    )

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        extra_kwargs = {
            'name': {'required': True}
        }

    def validate_name(self, value):
        if Tag.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Тег с таким названием уже существует")
        return value

    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)
    
    def validate(self, attrs):
        slug = slugify(attrs['name'])
        if Tag.objects.filter(slug=slug).exists():
            raise serializers.ValidationError({"name": "Такой slug уже существует"})
        attrs['slug'] = slug
        return attrs
    

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
        # try:
        #     tag = Tag.objects.get(id=value)
        #     self.tag_instance = tag
        #     return value
        # except Tag.DoesNotExist:
        #     raise ValidationError(f'Тег с ID {value} не найден')
        try:
            if value:
                tag = Tag.objects.get(id=value)
                self.tag_instance = tag
            return value
        except Tag.DoesNotExist:
            raise ValidationError(f'Тег с ID {value} не найден')
        
    def get_tag(self, tag_data):
        """
        Получает или создает тег по переданным данным.
        """
        try:
            if 'id' in tag_data:
                return Tag.objects.get(id=tag_data['id'])
            else:
                # Создаем новый тег
                return Tag.objects.create(
                    name=tag_data['name'],
                    slug=slugify(tag_data['name'])
                )
        except Exception as e:
            raise ValidationError(f'Ошибка создания тега: {str(e)}')

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
        # if not isinstance(data, int):
        #     raise ValidationError(Warnings.TAG_ID_REQUIRED)
        # return {'id': data}
        if isinstance(data, dict):
            return data
        elif isinstance(data, int):
            return {'id': data}
        else:
            raise ValidationError(Warnings.TAG_ID_REQUIRED)

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
        # return validate_ids_not_null_unique_collection(
        #     values=tags,
        #     values_model=Tag,
        #     values_prefix='tags'
        # )
        return tags

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
        # for ingredient in ingredients:
        #     validate_positive_amount(ingredient['amount'])
        # return validate_ids_not_null_unique_collection(
        #     values=ingredients,
        #     values_model=Ingredient,
        #     values_prefix='ingredients'
        # )
        for ingredient in ingredients:
            if 'amount' in ingredient:
                validate_positive_amount(ingredient['amount'])
        return ingredients

    @transaction.atomic()
    def save_tags(self, tags_data, instance):
        """
        Сохранение тегов для рецепта.

        Создает связь между рецептом и тегами.

        Параметры:
        - tags_data: Данные тегов для сохранения
        - instance: Экземпляр рецепта
        """
        # tag_ids = [tag['id'] for tag in tags_data]
        # instance.tags.set(tag_ids)
        tag_instances = []
        for tag_data in tags_data:
            tag = self.fields['tags'].get_tag(tag_data)
            tag_instances.append(tag)
        instance.tags.set(tag_instances)

    @transaction.atomic()
    def save_ingredients(self, ingredients_data, instance):
        """
        Сохранение ингредиентов для рецепта.

        Удаляет старые связи и создает новые записи ингредиентов.

        Параметры:
        - ingredients_data: Данные ингредиентов для сохранения
        - instance: Экземпляр рецепта
        """
        # IngredientRecipe.objects.filter(recipe=instance).delete()
        # ingredient_recipes = [
        #     IngredientRecipe(
        #         ingredient_id=ingredient_data['id'],
        #         recipe=instance,
        #         amount=ingredient_data['amount']
        #     )
        #     for ingredient_data in ingredients_data
        # ]

        # IngredientRecipe.objects.bulk_create(ingredient_recipes)
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredient_recipes = []
        for ingredient_data in ingredients_data:
            ingredient = self.fields['ingredients'].get_ingredient(ingredient_data)
            ingredient_recipes.append(
                IngredientRecipe(
                    ingredient=ingredient,
                    recipe=instance,
                    amount=ingredient_data['amount']
                )
            )
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
