from django.contrib.auth.models import AbstractUser
from django.db import models as ms

from foodgram_backend.settings import (DEFAULT_VALUE, EMAIL_MAX_LENGTH,
                                       USERNAME_MAX_LENGTH)

from .managers import CreateUserManager
from .validators import validate_username_characters, validate_username_not_me


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = ms.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Почта',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.'
        }
    )

    username = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username_characters, validate_username_not_me,],
        verbose_name='Ник',
    )

    first_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        default=DEFAULT_VALUE,
        verbose_name='Имя'
    )

    last_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        default=DEFAULT_VALUE,
        verbose_name='Фамилия'
    )

    avatar = ms.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар'
    )

    objects = CreateUserManager()
    default_objects = ms.Manager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email


class Follow(ms.Model):
    user = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    sub_date = ms.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            ms.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_followings'
            ),
        ]
        ordering = ['-sub_date']
        indexes = [
            ms.Index(fields=['user', 'author']),
        ]

    def save(self, *args, **kwargs):
        if self.user == self.author:
            raise ValueError('Невозможно подписаться на самого себя')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
