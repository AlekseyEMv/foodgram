from django.core.validators import RegexValidator
from rest_framework import serializers as ss
from io import BytesIO
from re import fullmatch

from django.core.exceptions import ValidationError
from PIL import Image

from foodgram_backend.settings import FORBIDDEN_USERNAMES, USERNAME_REGEX


class NonEmptyCharField(ss.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^\S+$',
            message='Поле не может быть пустым или содержать только пробелы.'
        )
    ]


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
