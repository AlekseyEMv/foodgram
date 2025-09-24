from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers as ss
from django.core.validators import MinValueValidator
from io import BytesIO
from re import fullmatch

from django.core.exceptions import ValidationError
from PIL import Image

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import (ADMIN_MAX_LENGTH, INGREDIENT_MAX_LENGTH,
                                       INGRIGIENTS_MIN_VALUE, MIN_COOKING_TIME,
                                       FORBIDDEN_USERNAMES, USERNAME_REGEX,
                                       RECIPE_MAX_LENGTH, RECIPE_MIN_LENGTH,
                                       TAG_MAX_LENGTH, UNIT_MAX_LENGTH)


def validate_required_field(value, field_name):
    """
    Валидатор обязательных полей
    """
    if not value:
        raise ValidationError(
            getattr(Warnings, f'{field_name.upper()}_REQUIRED')
        )


def validate_ids_not_null_unique_collection(
    values, values_model, values_prefix
):
    ID_FIELD = 'id'
    validate_required_field(values, values_prefix)
    value_ids = [value[ID_FIELD] for value in values]
    unique_value_ids = set(value_ids)
    if len(value_ids) != len(set(value_ids)):
        raise ValidationError(
            getattr(Warnings, f'{values_prefix.upper()}_DUPLICATE_ERROR')
        )
    existing_ids = set(
        values_model.objects.filter(id__in=value_ids)
        .values_list(ID_FIELD, flat=True)
    )
    missing_ids = unique_value_ids - existing_ids
    if missing_ids:
        raise ValidationError(
            getattr(Warnings, f'{values_prefix.upper()}_NOT_FOUND')
        )
    return values


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


def validate_picture_format(value, max_file_size):
    """
    Валидатор для проверки формата изображения.

    Параметры:
    - value: загруженный файл изображения
    - max_file_size: допустимый размер изображения

    Вызывает:
    - ValidationError если размер изображения большой или формат изображения
    не поддерживается.
    """

    if value.size > max_file_size:
        raise ValidationError(_(Warnings.FILE_SIZE_EXCEEDS_LIMIT))
    ALLOWED_IMAGE_FORMATS = ('JPG', 'JPEG', 'PNG', 'GIF')

    try:
        position = value.tell()

        with Image.open(BytesIO(value.read())) as img:
            image_format = img.format.upper()
            if image_format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError(
                    _('Допустимые форматы: {formats}').format(
                        formats=', '.join(ALLOWED_IMAGE_FORMATS)
                    )
                )

            value.seek(position)

    except Image.UnidentifiedImageError:
        raise ValidationError(_(Warnings.FILE_FORMAT_DETECTION_ERROR))
    except Exception as e:
        raise ValidationError(
            _('Ошибка при проверке изображения: {error}').format(error=str(e))
        )


def validate_image(value, max_file_size):
    try:
        validate_picture_format(value, max_file_size)
    except Exception:
        raise ValidationError(Warnings.IMAGE_REQUIRED)


def validate_positive_amount(value):
    """
    Валидатор положительного количества ингредиента
    """
    if value <= 0:
        raise ValidationError('Количество должно быть положительным числом.')


def create_min_amount_validator(min_value):
    """
    Создает валидатор сравнения минимального значения с заданным числом.

    Параметры:
    - min_value: минимальное допустимое число

    Возвращает:
    - функцию-валидатор
    """
    if not isinstance(min_value, (int, float)) or min_value < 0:
        raise ValidationError(Warnings.POSITIVE_VALUE_REQUIRED)

    return MinValueValidator(
        limit_value=min_value,
        message=_(f'{Warnings.MIN_VALUE_REQUIRED} {min_value}')
    )


def validate_model_class_instance(instance, model_class):
    """
    Валидатор для проверки типа объекта IngredientRecipe
    """
    if not isinstance(instance, model_class):
        raise ValidationError({
            'error': f'Ожидался объект {model_class}',
            'instance': instance,
            'type': type(instance).__name__
        })


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
