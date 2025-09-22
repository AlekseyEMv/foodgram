from django.contrib.auth.models import BaseUserManager

from foodgram.messages import Warnings


class CreateUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        password,
        **extra_fields
    ):
        if not email:
            raise ValueError(Warnings.EMAIL_REQUIRED)
        if not username:
            raise ValueError(Warnings.USERNAME_REQUIRED)
        if not first_name:
            raise ValueError('Укажите своё имя.')
        if not last_name:
            raise ValueError('Укажите свою фамилию.')
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
