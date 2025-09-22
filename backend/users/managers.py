from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from api.validators import (
    validate_all_required_fields,
    validate_unique_email,
    validate_unique_username,
    validate_superuser_flag
)


class CreateUserManager(BaseUserManager):
    """
    Менеджер для создания и управления пользователями.

    Предоставляет методы для создания обычных пользователей и
    суперпользователей, выполняет валидацию данных и обработку ошибок.
    """
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
        """
        Создает пользователя с указанными параметрами.

        Параметры:
        - email: адрес электронной почты пользователя
        - username: уникальное имя пользователя в системе
        - first_name: имя пользователя
        - last_name: фамилия пользователя
        - password: пароль пользователя
        - extra_fields: дополнительные поля для настройки пользователя

        Возвращает:
        - AbstractUser: созданный объект пользователя

        Вызывает:
        - IntegrityError: при нарушении целостности данных
        - ValidationError: при нарушении правил валидации
        """
        try:
            # Валидация обязательных полей
            validate_all_required_fields(
                email, username, first_name, last_name
            )

            # Валидация уникальности
            validate_unique_email(email, self.model)
            validate_unique_username(username, self.model)
            email = self.normalize_email(email)
            username = self.model.normalize_username(username)

            with transaction.atomic():
                user = self.model(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    **extra_fields
                )
                user.set_password(password)
                user.save(using=self._db)
                return user

        except IntegrityError as e:
            raise ValidationError(
                f'Ошибка целостности при создании пользователя: {e}'
            )
        except ValidationError as e:
            raise ValidationError(
                f'Ошибка валидации при создании пользователя: {e}'
            )
        except Exception as e:
            raise ValidationError(
                f'Непредвиденная ошибка при создании пользователя: {e}'
            )

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

        # Валидация флага суперпользователя
        validate_superuser_flag(extra_fields)

        return self._create_user(
            email, username, first_name, last_name, password, **extra_fields
        )
