from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from api.serializers import BaseRecipeSerializer
from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN
from .mixins import SubscriptionValidationMixin
from .models import Follow


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = ss.SerializerMethodField(
        help_text='Флаг подписки текущего пользователя на данного пользователя'
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
        try:
            return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise ValidationError({'detail': 'Ошибка создания пользователя.'})
        except Exception as e:
            raise ValidationError({'detail': str(e)})


class AvatarSerializer(ss.ModelSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True,
        max_length=AVATAR_MAX_LENGTH,
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
