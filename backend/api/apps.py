from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    Конфигурация приложения API

    Класс определяет основные параметры для приложения API в
    Django проекте. Наследуется от AppConfig.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
