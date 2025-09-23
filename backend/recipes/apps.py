from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """
    Конфигурация приложения для работы с рецептами

    Это класс конфигурации определяет основные параметры приложения recipes.
    Он отвечает за настройку автоматического поля первичного ключа
    и регистрацию приложения в Django.

    Атрибуты:
        default_auto_field:
            Тип поля для автоматического создания первичного ключа.
            Используется BigAutoField для поддержки больших чисел.
        name:
            Имя приложения в Django проекте.
            Указывает на расположение приложения в структуре проекта.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
