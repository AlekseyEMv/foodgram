from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Административная панель для управления пользователями.

    Настройки:
    - list_display: поля для отображения в списке пользователей
    - search_fields: поля для поиска
    - list_display_links: поля, по которым можно перейти к редактированию
    - ordering: порядок сортировки
    """

    list_display = (
        'username',    # Никнейм пользователя
        'email',       # Email пользователя
        'first_name',  # Имя пользователя
        'last_name',   # Фамилия пользователя
    )
    search_fields = (
        'username',
        'email',
    )
    list_display_links = (
        'username',
        'email',
    )
    ordering = ('id',)
