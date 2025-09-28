from django.utils.text import slugify
from unidecode import unidecode


def generate_unique_slug(name, model_class):
    """
    Генерирует уникальный slug для модели на основе исходного названия.

    Функция принимает название и класс модели, создает slug, преобразуя
    Unicode-символы в ASCII, и проверяет его уникальность в базе данных.
    При обнаружении конфликта добавляет числовой суффикс до получения
    уникального значения.

    Параметры:
    - name: исходное название для генерации slug
    - model_class: модель Django, для которой генерируется slug

    Возвращает:
    - Уникальный slug
    """
    original_slug = slugify(unidecode(name))
    slug = original_slug
    num = 1

    while model_class.objects.filter(slug=slug).exists():
        slug = f'{original_slug}-{num}'
        num += 1

    return slug
