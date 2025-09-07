from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator

from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN


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
