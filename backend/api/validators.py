from io import BytesIO
from re import fullmatch

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from PIL import Image

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import FORBIDDEN_USERNAMES, USERNAME_REGEX


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
            getattr(Warnings, f'{field_name.upper()}_REQUIRED')
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
    Валидатор уникальности email.

    Проверяет, что email не существует в базе данных.

    Параметры:
    - value: email для проверки
    - model: модель для проверки уникальности

    Вызывает:
    - ValidationError если email уже существует
    """
    if model.objects.filter(email=value).exists():
        raise ValidationError(Warnings.EMAIL_EXISTS)


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
        raise ValidationError(Warnings.USERNAME_EXISTS)


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
    """
    Основной валидатор изображения.

    Обёртка для проверки изображения, обрабатывающая все возможные ошибки.

    Параметры:
    - value: загруженный файл изображения
    - max_file_size: максимально допустимый размер файла

    Вызывает:
    - ValidationError если изображение не прошло проверку
    """
    try:
        validate_picture_format(value, max_file_size)
    except Exception:
        raise ValidationError(Warnings.IMAGE_REQUIRED)


def validate_positive_amount(value):
    """
    Валидатор проверки положительного значения количества.

    Проверяет, что переданное значение является положительным числом.

    Параметры:
    - value: числовое значение количества

    Вызывает:
    - ValidationError если значение меньше или равно нулю
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
    if value in FORBIDDEN_USERNAMES:
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
    if fullmatch(USERNAME_REGEX, value) is None:
        raise ValidationError(
            ('Ник пользователя может состоять из букв, цифр, '
             'а также символов @.+-_')
        )
