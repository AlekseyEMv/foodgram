from functools import partial

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings as stgs
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator

from foodgram_backend.messages import Warnings as Warn
from .models import Follow

from api.validators import (validate_picture_format,
                            validate_username_characters,
                            validate_username_not_me)

User = get_user_model()


validate_avatar_picture = partial(
    validate_picture_format, max_file_size=stgs.AVATAR_MAX_SIZE
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
        min_length=stgs.MIN_PASSWORD_LEN,
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
        from recipes.serializers import BaseRecipeSerializer
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
            raise ss.ValidationError(Warn.REQUEST_CONTEXT_MISSING)

        # Проверяем авторизацию пользователя
        user = request.user
        if not user.is_authenticated:
            raise ss.ValidationError(Warn.AUTHENTICATION_REQUIRED)

        # Получаем автора из валидируемых данных
        author = attrs.get('author')
        if not author:
            raise ss.ValidationError(Warn.AUTHOR_REQUIRED)

        # Проверяем запрещенные условия
        if user == author:
            raise ss.ValidationError(Warn.SELF_SUBSCRIBE_FORBIDDEN)

        if not author.is_active:
            raise ss.ValidationError(Warn.INACTIVE_USER)

        # Проверяем существование подписки
        if Follow.objects.filter(user=user, author=author).exists():
            raise ss.ValidationError(Warn.SUBSCRIPTION_ALREADY_EXISTS)

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
        min_length=stgs.MIN_PASSWORD_LEN,
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
            raise ss.ValidationError(Warn.REQUEST_CONTEXT_MISSING)

        user = request.user
        if not user:
            raise ss.ValidationError(Warn.USER_NOT_FOUND)

        if not user.check_password(value):
            raise ss.ValidationError(Warn.PASSWORD_CURRENT_INVALID)

        return value

    def validate_new_password(self, value):
        """
        Валидация нового пароля.

        Проверяет минимальную длину пароля.
        """
        if len(value) < stgs.MIN_PASSWORD_LEN:
            raise ss.ValidationError(
                f'{Warn.PASSWORD_TOO_SHORT_MESSAGE} '
                f'{stgs.MIN_PASSWORD_LEN} символов'
            )
        return value

    def validate(self, data):
        """
        Общая валидация данных.

        Проверяет, что новый пароль не совпадает со старым.
        """
        if data['current_password'] == data['new_password']:
            raise ss.ValidationError(Warn.PASSWORD_CHANGE_REQUIRED)
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
