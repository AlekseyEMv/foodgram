import os
from re import fullmatch

from django.conf import settings as stgs
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from foodgram_backend.messages import Warnings as Warn


def validate_required_field(value, field_name):
    """
    Валидатор обязательных полей.

    Проверяет, что переданное значение не является пустым.

    Параметры:
    - value: значение поля для проверки
    - field_name: название поля (используется для формирования сообщения об
        ошибке)

    Вызывает:
    - ValidationError если значение пустое
    """
    if not value:
        raise ValidationError(
            getattr(Warn, f'{field_name.upper()}_REQUIRED')
        )


def validate_ids_not_null_unique_collection(
    values, values_model, values_prefix
):
    """
    Валидатор уникальности и существования ID в коллекции.

    Проверяет:
    - Наличие значений
    - Уникальность ID в коллекции
    - Существование ID в базе данных

    Параметры:
    - values: коллекция значений для проверки
    - values_model: модель для проверки существования ID
    - values_prefix: префикс для формирования сообщений об ошибках

    Возвращает:
    - Проверенную коллекцию значений

    Вызывает:
    - ValidationError при обнаружении ошибок
    """
    ID_FIELD = 'id'
    validate_required_field(values, values_prefix)
    value_ids = [value[ID_FIELD] for value in values]
    unique_value_ids = set(value_ids)
    if len(value_ids) != len(set(value_ids)):
        raise ValidationError(
            getattr(Warn, f'{values_prefix.upper()}_DUPLICATE_ERROR')
        )
    existing_ids = set(
        values_model.objects.filter(id__in=value_ids)
        .values_list(ID_FIELD, flat=True)
    )
    missing_ids = unique_value_ids - existing_ids
    if missing_ids:
        raise ValidationError(
            getattr(Warn, f'{values_prefix.upper()}_NOT_FOUND')
        )
    return values


def validate_unique_email(value, model):
    """
    Валидатор уникальности email.

    Проверяет, что email не существует в базе данных.

    Параметры:
    - value: email для проверки
    - model: модель для проверки уникальности

    Вызывает:
    - ValidationError если email уже существует
    """
    if model.objects.filter(email=value).exists():
        raise ValidationError(Warn.EMAIL_EXISTS)


def validate_unique_username(value, model):
    """
    Валидатор уникальности username.

    Проверяет, что username не существует в базе данных.

    Параметры:
    - value: username для проверки
    - model: модель для проверки уникальности

    Вызывает:
    - ValidationError если username уже существует
    """
    if model.objects.filter(username=value).exists():
        raise ValidationError(Warn.USERNAME_EXISTS)


def validate_all_required_fields(email, username, first_name, last_name):
    """
    Комплексный валидатор обязательных полей пользователя.

    Проверяет наличие всех обязательных полей при регистрации.

    Параметры:
    - email: email пользователя
    - username: имя пользователя
    - first_name: имя
    - last_name: фамилия

    Вызывает:
    - ValidationError если какое-либо поле пустое
    """
    validate_required_field(email, 'email')
    validate_required_field(username, 'username')
    validate_required_field(first_name, 'first_name')
    validate_required_field(last_name, 'last_name')


def validate_superuser_flag(extra_fields):
    """
    Валидатор проверки флага суперпользователя.

    Проверяет, что при создании суперпользователя установлен флаг
    is_superuser=True.

    Параметры:
    - extra_fields: словарь дополнительных полей при создании пользователя

    Вызывает:
    - ValidationError если флаг is_superuser не установлен
    """
    if not extra_fields.get('is_superuser'):
        raise ValidationError(
            f'{Warn.FLAG_SET_REQUIRED} "is_superuser=True".'
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
        raise ValidationError(_(Warn.FILE_SIZE_EXCEEDS_LIMIT))
    ext = os.path.splitext(value.name)[1][1:].upper()  # [1:] убирает точку

    if ext not in stgs.ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            _('Допустимые форматы: {formats}').format(
                formats=', '.join(stgs.ALLOWED_IMAGE_FORMATS)
            )
        )


def validate_image(value, max_file_size):
    """
    Основной валидатор изображения.

    Обёртка для проверки изображения, обрабатывающая все возможные ошибки.

    Параметры:
    - value: загруженный файл изображения
    - max_file_size: максимально допустимый размер файла

    Вызывает:
    - ValidationError с конкретным сообщением об ошибке
    """
    if not value:
        raise ValidationError(Warn.IMAGE_REQUIRED)

    try:
        validate_picture_format(value, max_file_size)
    except ValidationError as e:
        raise ValidationError(str(e))
    except Exception:
        raise ValidationError(Warn.IMAGE_PROCESSING_ERROR)


def validate_value_is_numeric(value):
    """
    Проверяет, является ли переданное значение числовым.

    Параметры:
    - value: любое значение, которое нужно проверить на числовой тип.

    Вызывает:
    - TypeError если значение не является числом (int или float)
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f'{Warn.VALUE_MUST_BE_NUMERIC} {value}')


def validate_value_interval(value, min_value, max_value, inclusive=True):
    """
    Проверяет, находится ли значение в заданном числовом интервале.

    Параметры:
    - value: Значение для проверки
    - min_value: Нижняя граница интервала
    - max_value: Верхняя граница интервала
    - inclusive: Oпционально
        Если True (по умолчанию), границы включены в интервал
        Если False, границы исключены из интервала

    Вызывает:
    - TypeError если value, min_value или max_value не являются
        числами (int или float)
    - ValueError если min_value больше max_value
    - ValidationError если значение выходит за пределы допустимого интервала
    """
    validate_value_is_numeric(value)
    validate_value_is_numeric(min_value)
    validate_value_is_numeric(max_value)

    if min_value > max_value:
        raise ValueError(Warn.VALUE_MIN_MAX_ORDER_ERROR)

    if inclusive:
        if value < min_value or value > max_value:
            raise ValidationError(
                _(
                    f'{Warn.VALUE_MUST_BE_IN_RANGE} от {min_value} '
                    f'до {max_value}'
                )
            )
    else:
        if value <= min_value or value >= max_value:
            raise ValidationError(
                _(
                    f'{Warn.VALUE_MUST_BE_IN_RANGE} {min_value} и {max_value}'
                )
            )


def validate_model_class_instance(instance, model_class):
    """
    Валидатор проверки типа экземпляра модели.

    Проверяет, что переданный экземпляр является объектом указанного класса
    модели.

    Параметры:
    - instance: проверяемый экземпляр объекта
    - model_class: ожидаемый класс модели

    Возвращает:
    - None при успешной проверке

    Вызывает:
    - ValidationError если тип экземпляра не соответствует ожидаемому
    """
    if not isinstance(instance, model_class):
        raise ValidationError({
            'error': f'Ожидался объект {model_class}',
            'instance': instance,
            'type': type(instance).__name__
        })


def validate_username_not_me(value):
    """
    Валидатор запрещённых имён пользователей.

    Проверяет, что указанное имя пользователя не входит в список
    запрещённых слов.

    Параметры:
    - value: проверяемое имя пользователя

    Вызывает:
    - ValidationError если имя пользователя находится в списке запрещённых
    """
    if value in stgs.FORBIDDEN_USERNAMES:
        raise ValidationError(
            (f'Cлово {value} нельзя использовать'
             ' в качестве имени пользователя.')
        )


def validate_username_characters(value):
    """
    Валидатор допустимых символов в имени пользователя.

    Проверяет, что имя пользователя содержит только разрешённые символы.

    Разрешённые символы:
    - Буквы (латиница)
    - Цифры
    - Специальные символы: @ . + - _

    Параметры:
    - value: проверяемое имя пользователя

    Вызывает:
    - ValidationError если обнаружены недопустимые символы
    """
    if fullmatch(stgs.USERNAME_REGEX, value) is None:
        raise ValidationError(Warn.USER_NICKNAME_RULES)
