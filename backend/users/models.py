from django.contrib.auth.models import AbstractUser
from django.db import models as ms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import (
    DEFAULT_VALUE,
    EMAIL_MAX_LENGTH,
    USERNAME_MAX_LENGTH
)
from .managers import CreateUserManager
from api.validators import (
    validate_username_characters, validate_username_not_me
)


class User(AbstractUser):
    """
    Модель пользователя с расширенным функционалом.

    Представляет собой кастомную реализацию пользователя Django с email
    в качестве основного идентификатора.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = ms.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name=_('Почта'),
        error_messages={
            'unique': Warnings.USER_EMAIL_EXISTS
        },
        help_text='Уникальный email-адрес пользователя.'
    )

    username = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            validate_username_characters,
            validate_username_not_me
        ],
        verbose_name=_('Ник'),
        help_text='Уникальный никнейм пользователя'
    )

    first_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        default=DEFAULT_VALUE,
        verbose_name=_('Имя'),
        help_text='Имя пользователя'
    )

    last_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        default=DEFAULT_VALUE,
        verbose_name=_('Фамилия'),
        help_text='Фамилия пользователя'
    )

    avatar = ms.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        verbose_name=_('Аватар'),
        help_text='Аватар пользователя'
    )

    objects = CreateUserManager()   # Менеджер для создания пользователей
    default_objects = ms.Manager()  # Стандартный менеджер

    class Meta:
        """
        Мета-информация о модели подписки.

        Определяет настройки хранения и отображения данных.
        """
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ('id',)

    def clean(self):
        """
        Валидация данных перед сохранением.

        Проверяет обязательные поля first_name и last_name.
        """
        if not self.first_name or not self.last_name:
            raise ValidationError(_(Warnings.NAME_SURNAME_REQUIRED))

    def __str__(self):
        """
        Строковое представление объекта.

        Возвращает email пользователя.
        """
        return self.email


class Follow(ms.Model):
    """
    Модель подписки между пользователями.

    Представляет собой отношение многие-ко-многим между подписчиком и автором.
    Обеспечивает механизм отслеживания подписок пользователей друг на друга.
    """
    user = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='follower',
        verbose_name=_('Подписчик'),
        help_text='Пользователь, который подписывается на другого пользователя'
    )
    author = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='following',
        verbose_name=_('Автор'),
        help_text='Пользователь, на которого подписываются'
    )
    sub_date = ms.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата подписки'),
        help_text='Дата создания подписки'
    )

    class Meta:
        """
        Мета-информация о модели подписки.

        Определяет настройки хранения и отображения данных.
        """
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        constraints = [
            ms.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_followings'
            ),
        ]
        ordering = ['-sub_date']
        indexes = [
            # 'Индекс для быстрого поиска подписок'
            ms.Index(fields=['user', 'author']),
        ]

    def clean(self):
        """
        Валидация данных перед сохранением.

        Проверяет, что пользователь не может подписаться сам на себя.
        """
        if self.user == self.author:
            raise ValidationError(Warnings.SELF_SUBSCRIBE_FORBIDDEN)

    def save(self, *args, **kwargs):
        """
        Метод сохранения объекта.

        Выполняет полную валидацию перед сохранением в базу данных.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Строковое представление объекта.

        Возвращает читаемое представление подписки в формате:
        'Пользователь X подписан на пользователя Y'
        """
        return f'{self.user} подписан на {self.author}'
