from django.contrib.auth.models import AbstractUser
from django.db import models as ms

from .validators import (
    validate_username_not_me, validate_username_characters
)
from foodgram_backend.settings import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH


class User(AbstractUser):
    """Кастомная модель пользователя с переопределёнными полями и валидацией.

    Наследуется от AbstractUser, заменяя стандартные поля и добавляя новые:
    - Авторизация по email вместо username
    - Дополнительные поля: аватар, обязательные имя/фамилия
    - Кастомные валидаторы для username

    Attributes:
        email (EmailField): Уникальное поле электронной почты.
            Максимальная длина — 254 символа.
        username (CharField): Уникальный никнейм.
            Максимальная длина — 150 символов.
        first_name (CharField): Обязательное поле с именем.
            Максимальная длина — 150 символов.
        last_name (CharField): Обязательное поле с фамилией.
            Максимальная длина — 150 символов.
        avatar (ImageField): Необязательное поле для загрузки аватара.
            Сохраняется в 'users/images/'.

    Meta:
        verbose_name (str): Человекочитаемое имя модели в единственном числе.
        verbose_name_plural (str): Человекочитаемое имя модели во
            множественном числе.
        ordering (tuple): Сортировка по умолчанию (по id).

    Constants:
        USERNAME_FIELD (str): Поле, используемое для аутентификации (email).
        REQUIRED_FIELDS (list): Обязательные поля при создании пользователя
            через createsuperuser.

    Validators:
        validate_username_characters: Проверяет допустимые символы в username.
        validate_username_not_me: Запрещает использование зарезервированных
            имён (например, 'me').

    Example:
        >>> user = User.objects.create_user(
        ...     email='test@example.com',
        ...     username='testuser',
        ...     first_name='Иван',
        ...     last_name='Петров'
        ... )
    """

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
        verbose_name='Имя'
    )

    last_name = ms.CharField(
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )

    avatar = ms.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email
