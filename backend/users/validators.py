from re import fullmatch
from django.core.exceptions import ValidationError

from foodgram_backend.settings import FORBIDDEN_USERNAMES, USERNAME_REGEX


def validate_username_not_me(value):
    """
    Проверяет, что указанное имя пользователя не входит в список запрещенных.

    Параметры:
    value: Имя пользователя для проверки

    Исключения:
    ValidationError: Если имя пользователя содержится в списке запрещенных.
    """
    if value in FORBIDDEN_USERNAMES:
        raise ValidationError(
            (f'Cлово {value} нельзя использовать'
             ' в качестве имени пользователя.')
        )


def validate_username_characters(value):
    """Проверяет, соответствует ли ник допустимому формату символов.

    Args:
        value: Строка с ником пользователя для валидации.

    Raises:
        ValidationError: Если имя пользователя содержит недопустимые символы.

    Notes:
        Разрешенные символы:
        - Буквы (A-Z, a-z)
        - Цифры (0-9)
        - Специальные символы: @ . + - _

    Example:
        >>> validate_username_characters("user_123")
        None  # Валидация пройдена

        >>> validate_username_char_exists("user@name")
        None  # Валидация пройдена

        >>> validate_username_characters("user name")
        ValidationError: Ник пользователя может состоять из букв, цифр,
        а также символов @.+-_
    """
    if fullmatch(USERNAME_REGEX, value) is None:
        raise ValidationError(
            ('Ник пользователя может состоять из букв, цифр, '
             'а также символов @.+-_')
        )
