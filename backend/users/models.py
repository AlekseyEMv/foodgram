from django.contrib.auth.models import AbstractUser
from django.db import models as ms

from .managers import CreateUserManager
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
        email: Уникальное поле электронной почты.
            Максимальная длина — 254 символа.
        username: Уникальный никнейм.
            Максимальная длина — 150 символов.
        first_name: Обязательное поле с именем.
            Максимальная длина — 150 символов.
        last_name: Обязательное поле с фамилией.
            Максимальная длина — 150 символов.
        avatar: Необязательное поле для загрузки аватара.
            Сохраняется в 'users/images/'.

    Meta:
        verbose_name: Человекочитаемое имя модели в единственном числе.
        verbose_name_plural: Человекочитаемое имя модели во
            множественном числе.
        ordering: Сортировка по умолчанию (по id).

    Constants:
        USERNAME_FIELD: Поле, используемое для аутентификации (email).
        REQUIRED_FIELDS: Обязательные поля при создании пользователя
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

    objects = CreateUserManager()
    default_objects = ms.Manager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email


class Follow(ms.Model):
    """Модель подписки пользователя на автора.

    Позволяет пользователям подписываться на других пользователей (авторов),
    фиксируя дату подписки.
    Гарантирует уникальность связи подписчик - автор.

    Атрибуты:
        user: Подписчик. Связь с моделью User через ForeignKey.
        author: Автор, на которого подписываются.
            Связь с моделью User через ForeignKey.
        sub_date: Дата и время подписки (автоматически заполняется
            при создании).

    Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
        constraints: Ограничения модели, включая уникальность пары
            пользователь - автор.

    Методы:
        __str__: Возвращает строковое представление
            в формате «Пользователь подписан на Автор».

    Пример использования:
        >>> follow = Follow.objects.create(user=user1, author=user2)
        >>> print(follow)
        "user1 подписан на user2"

    Особенности:
        Гарантирует уникальность связки подписчик - автор.
        При удалении пользователей автоматически удаляется связь.
    """
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
                name='unique_followings',
                violation_error_message='Пользователь уже подписан на этого автора'
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
