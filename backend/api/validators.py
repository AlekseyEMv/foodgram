from django.core.validators import RegexValidator
from rest_framework import serializers as ss
from io import BytesIO
from re import fullmatch

from django.core.exceptions import ValidationError
from PIL import Image

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import FORBIDDEN_USERNAMES, USERNAME_REGEX


def validate_required_field(value, field_name):
    """
    Валидатор обязательных полей
    """
    if not value:
        raise ValidationError(getattr(Warnings, f'{field_name.upper()}_REQUIRED'))


def validate_unique_email(value, model):
    """
    Валидатор уникальности email
    """
    if model.objects.filter(email=value).exists():
        raise ValidationError(Warnings.EMAIL_EXISTS)


def validate_unique_username(value, model):
    """
    Валидатор уникальности username
    """
    if model.objects.filter(username=value).exists():
        raise ValidationError(Warnings.USERNAME_EXISTS)


def validate_all_required_fields(email, username, first_name, last_name):
    """
    Комплексный валидатор всех обязательных полей
    """
    validate_required_field(email, 'email')
    validate_required_field(username, 'username')
    validate_required_field(first_name, 'first_name')
    validate_required_field(last_name, 'last_name')


def validate_superuser_flag(extra_fields):
    """
    Валидатор флага суперпользователя
    """
    if not extra_fields.get('is_superuser'):
        raise ValidationError(
            f'{Warnings.FLAG_SET_REQUIRED} "is_superuser=True".'
        )


def validate_username_not_me(value):
    if value in FORBIDDEN_USERNAMES:
        raise ValidationError(
            (f'Cлово {value} нельзя использовать'
             ' в качестве имени пользователя.')
        )


def validate_username_characters(value):
    if fullmatch(USERNAME_REGEX, value) is None:
        raise ValidationError(
            ('Ник пользователя может состоять из букв, цифр, '
             'а также символов @.+-_')
        )


def validate_image_format(value):
    try:
        if value:
            image = Image.open(BytesIO(value.read()))
            if image.format not in ['JPEG', 'PNG', 'GIF']:
                raise ValidationError('Допустимые форматы: JPEG, PNG, GIF')
            return value
    except Exception as e:
        raise ValidationError(f'Ошибка при проверке изображения: {str(e)}')


class NonEmptyCharField(ss.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^\S+$',
            message='Поле не может быть пустым или содержать только пробелы.'
        )
    ]