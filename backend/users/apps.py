from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Конфигурация приложения 'users' для Django проекта.

    Определяет основные параметры приложения, включая:
    - Тип автоматического поля для первичных ключей
    - Имя приложения
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
