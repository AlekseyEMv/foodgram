from django.conf import settings as stgs
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Follow, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Административный интерфейс для управления пользователями

    Предоставляет расширенный интерфейс для работы с пользовательскими данными,
    включая регистрацию, редактирование и просмотр профилей.

    Атрибуты:
    - list_display: поля для отображения в списке пользователей
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - ordering: порядок сортировки
    - empty_value_display: значение для пустых полей
    - fieldsets: структура формы
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
    empty_value_display = stgs.ADMIN_EMPTY_VALUE
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('email', 'username', 'avatar')
        }),
        (_('Личные данные'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Права доступа'), {
            'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')
        }),
        (_('Даты'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления подписками

    Позволяет просматривать и управлять подписками между пользователями.

    Атрибуты:
    - list_display: поля для отображения в списке подписок
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - ordering: порядок сортировки
    - empty_value_display: значение для пустых полей
    - fieldsets: структура формы
    """
    list_display = ('user', 'author', 'sub_date')
    search_fields = ('user__email', 'author__email')
    list_filter = ('sub_date',)
    ordering = ('-sub_date',)
    empty_value_display = stgs.ADMIN_EMPTY_VALUE
    fieldsets = (
        (_('Участники подписки'), {
            'fields': ('user', 'author')
        }),
        (_('Даты'), {
            'fields': ('sub_date',)
        }),
    )
    readonly_fields = ('sub_date',)
