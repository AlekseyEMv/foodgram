from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models as ms

from backend.users.validators import (
    validate_username_not_me, validate_username_characters
)
from foodgram_backend.settings import (
    EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, USERNAME_ADMIN_LENGTH
)


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = ms.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Почта пользователя',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.'
        }
    )

    username = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username_characters, validate_username_not_me,],
        verbose_name='Ник пользователя',
    )

    first_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Имя пользователя'
    )

    last_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Фамилия пользователя'
    )

    avatar = ms.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар пользователя'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username[:USERNAME_ADMIN_LENGTH]
