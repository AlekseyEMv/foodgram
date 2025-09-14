from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss
from rest_framework.validators import UniqueValidator

from foodgram_backend.settings import AVATAR_MAX_LENGTH, MIN_PASSWORD_LEN

from .validators import validate_image_format, validate_username_characters

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
