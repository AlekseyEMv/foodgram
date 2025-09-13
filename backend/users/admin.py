from django.contrib import admin
from django.contrib.auth import get_user_model

from foodgram_backend.settings import ADMIN_EMPTY_VALUE

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
