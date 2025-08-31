from django.contrib import admin
from django.contrib.auth import get_user_model

from foodgram_backend.settings import ADMIN_EMPTY_VALUE

from .models import Follow

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Административная панель для управления пользователями.

    Настройки:
    - list_display: поля для отображения в списке пользователей
    - search_fields: поля для поиска
    - list_filter: поля для фильтрации
    - list_display_links: поля, по которым можно перейти к редактированию
    - empty_value_display: пояснение для необязательных полей
    - ordering: порядок сортировки
    """

    list_display = (
        'id',          # ID пользователя
        'email',       # Email пользователя
        'username',    # Никнейм пользователя
        'first_name',  # Имя пользователя
        'last_name',   # Фамилия пользователя
    )
    search_fields = (
        'email',
        'username',
    )
    list_filter = (        
        'username',
        'email'
    )
    list_display_links = (
        'username',
        'email',
    )
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('id',)
