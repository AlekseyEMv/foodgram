from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN
from .models import Follow


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для работы с пользовательскими данными.

    Предоставляет полный набор полей для работы с пользователем,
    включая информацию о подписке текущего пользователя на
    данного пользователя.

    Атрибут:
        is_subscribed: Флаг подписки текущего пользователя
    """
    is_subscribed = ss.SerializerMethodField(
        help_text='Флаг подписки текущего пользователя на данного пользователя'
    )

    class Meta:
        """
        Настройки сериализатора.

        Определяет модель и поля для сериализации.
        """
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'password',
            'is_subscribed',
        )
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            },
            'username': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            },
            'password': {
                'write_only': True,
                'min_length': MIN_PASSWORD_LEN,
                'style': {'input_type': 'password'}
            },
        }

    def get_is_subscribed(self, obj):
        """
        Метод для получения статуса подписки.

        Аргумент:
            obj: Объект пользователя

        Возвращает:
            True если текущий пользователь подписан, иначе False
        """
        request = self.context.get('request')
        if not request:
            return False
        current_user = request.user
        return (
            current_user.follower.filter(author=obj).exists()
            if current_user.is_authenticated
            else False
        )

    def create(self, validated_data):
        """
        Метод для создания нового пользователя.

        Аргумент:
            validated_data: Валидированные данные для создания пользователя

        Возвращает:
            User: Созданный объект пользователя

        Возбуждает:
            ValidationError: При ошибке создания пользователя
        """
        try:
            return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise ValidationError({'detail': 'Ошибка создания пользователя'})
        except Exception as e:
            raise ValidationError({'detail': str(e)})


class AvatarSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с аватаром пользователя.

    Позволяет обновлять аватар пользователя в формате base64.

    Атрибут:
        avatar: Поле для загрузки аватара.
    """
    avatar = Base64ImageField(
        required=False,
        allow_null=True,
        max_length=AVATAR_MAX_LENGTH,  # 1MB
        help_text="Аватар пользователя в формате base64"
    )

    class Meta:
        """
        Настройки сериализатора.

        Определяет модель и поля для сериализации.
        """
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {
                'required': False,
                'allow_null': True
            }
        }


class SubscribeSerializer(ss.ModelSerializer):
    user = ss.PrimaryKeyRelatedField(
        read_only=True,
        default=ss.CurrentUserDefault(),
        help_text='Текущий пользователь, создающий подписку'
    )

    class Meta:
        model = Follow
        fields = ('user',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('author', 'user'),
                message='Вы уже подписаны на этого пользователя.'
            ),
        ]

    def create(self, validated_data):
        author_id = self.context['view'].kwargs.get('pk')
        try:
            author = User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise ss.ValidationError('Пользователь не найден')
        validated_data['author'] = author
        return super().create(validated_data)

    def validate(self, data):
        current_user = self.context['request'].user
        author_id = self.context['view'].kwargs.get('pk')
        try:
            target_user = User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise ss.ValidationError('Пользователь не найден')
        if not current_user.is_authenticated:
            raise ss.ValidationError('Авторизация требуется для подписки')
        if current_user == target_user:
            raise ss.ValidationError(
                'Операция подписки на собственный аккаунт не допускается'
            )
        if not target_user.is_active:
            raise ss.ValidationError(
                'Невозможно подписаться на неактивного пользователя'
            )
        return data


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