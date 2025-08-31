from django.contrib.auth.models import BaseUserManager
from django.core.validators import validate_email


class CreateUserManager(BaseUserManager):
    """
    Менеджер для создания и управления пользовательскими аккаунтами.

    Предоставляет методы для создания обычных и суперпользовательских аккаунтов
    с обязательной валидацией email, имени пользователя, имени и фамилии.
    """
    use_in_migrations = True  # Флаг для использования в миграциях

    def _create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        password,
        **extra_fields
    ):
        """
        Создает и сохраняет пользователя с указанными параметрами.

        Параметры:
        - email: адрес электронной почты
        - username: имя пользователя
        - first_name: имя
        - last_name: фамилия
        - password: пароль
        - extra_fields: дополнительные поля

        Возвращает:
        Созданный пользовательский объект

        Вызывает ValueError при:
        - отсутствии обязательных полей
        - некорректном email
        - существовании пользователя с таким email или username
        """
        if not email:
            raise ValueError('Укажите email.')
        if not username:
            raise ValueError('Укажите имя пользователя.')
        if not first_name:
            raise ValueError('Укажите своё имя.')
        if not last_name:
            raise ValueError('Укажите свою фамилию.')
        if not validate_email(email):
            raise ValueError('Некорректный email.')
        if self.model.objects.filter(email=email).exists():
            raise ValueError('Email уже используется.')
        if self.model.objects.filter(username=username).exists():
            raise ValueError('Имя пользователя уже занято.')

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(
            email=email, username=username, first_name=first_name,
            last_name=last_name, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        password,
        **extra_fields
    ):
        """
        Создает обычного пользователя.

        Параметры:
        - email: адрес электронной почты
        - username: имя пользователя
        - first_name: имя
        - last_name: фамилия
        - password: пароль
        - extra_fields: дополнительные поля

        Возвращает:
        Созданный пользовательский объект
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_active', True)
        return self._create_user(
            email, username, first_name, last_name, password, **extra_fields
        )

    def create_superuser(
        self,
        email,
        username,
        first_name,
        last_name,
        password,
        **extra_fields
    ):
        """
        Создает суперпользователя.

        Параметры:
        - email: адрес электронной почты
        - username: имя пользователя
        - first_name: имя
        - last_name: фамилия
        - password: пароль
        - extra_fields: дополнительные поля

        Возвращает:
        Созданный объект суперпользователя

        Вызывает ValueError если флаг is_superuser не установлен
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if not extra_fields.get('is_superuser'):
            raise ValueError('Установите флаг "is_superuser=True".')
        return self._create_user(
            email, username, first_name, last_name, password, **extra_fields
        )
