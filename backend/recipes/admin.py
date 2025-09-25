from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from foodgram_backend.settings import ADMIN_EMPTY_VALUE

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe, Shopping,
                     Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления ингредиентами

    Предоставляет интерфейс для создания, редактирования и просмотра
    ингредиентов. Включает настройки отображения, поиска и фильтрации.

    Атрибуты:
    - list_display: поля, отображаемые в списке ингредиентов
        (название и единица измерения)
    - search_fields: поля для поиска (по названию)
    - list_filter: доступные фильтры (по единице измерения)
    - empty_value_display: значение для пустых полей
        (используется системное значение)
    - ordering: порядок сортировки (по названию в алфавитном порядке)
    - fieldsets: группировка полей формы
    """
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)
    empty_value_display = ADMIN_EMPTY_VALUE
    fieldsets = (
        (None, {
            'fields': ('name', 'measurement_unit')
        }),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления тегами рецептов

    Позволяет создавать, редактировать и управлять тегами для категоризации
    рецептов.

    Атрибуты:
    - list_display: поля для отображения (название и slug)
    - search_fields: поиск по названию тега
    - readonly_fields: поля только для чтения (slug)
    - prepopulated_fields: автоматическое заполнение slug на основе названия
    - empty_value_display: значение для пустых полей
    - fieldsets: структура формы
    """
    list_display = ('name', 'slug')
    search_fields = ('name',)
    readonly_fields = ('slug',)
    prepopulated_fields = {'slug': ('name',)}
    empty_value_display = ADMIN_EMPTY_VALUE
    fieldsets = (
        (None, {
            'fields': ('name', 'slug')
        }),
    )


class IngredientRecipeInline(admin.TabularInline):
    """
    Inline-форма для управления ингредиентами в рецепте

    Позволяет добавлять и редактировать ингредиенты прямо в форме рецепта.

    Атрибуты:
    - model: связанная модель IngredientRecipe
    - extra: количество дополнительных форм по умолчанию
    - autocomplete_fields: поля с автодополнением
    """
    model = IngredientRecipe
    extra = 1
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления рецептами

    Основной интерфейс для работы с рецептами, включающий:
    - Управление ингредиентами
    - Работу с тегами
    - Редактирование основной информации

    Атрибуты:
    - list_display: поля для отображения в списке
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - readonly_fields: поля только для чтения
    - filter_horizontal: множественный выбор тегов
    - inlines: встроенные формы для ингредиентов
    - ordering: сортировка по дате публикации
    - empty_value_display: значение для пустых полей
    - fieldsets: структура формы
    """
    list_display = ('name', 'author', 'pub_date', 'cooking_time')
    search_fields = ('name', 'text', 'author__username')
    list_filter = ('pub_date', 'tags')
    readonly_fields = ('pub_date',)
    filter_horizontal = ('tags',)
    inlines = [IngredientRecipeInline]
    ordering = ('-pub_date',)
    empty_value_display = ADMIN_EMPTY_VALUE
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'author', 'image', 'text', 'cooking_time')
        }),
        (_('Теги'), {
            'fields': ('tags',)
        }),
    )


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления избранными рецептами

    Позволяет просматривать и управлять списком избранных рецептов
    пользователей.

    Атрибуты:
    - list_display: поля для отображения (пользователь и рецепт)
    - search_fields: поиск по пользователю и названию рецепта
    - list_filter: фильтрация по пользователю
    - readonly_fields: поля только для чтения (пользователь и рецепт)
    - empty_value_display: значение для пустых полей
        (используется системное значение)
    """
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    readonly_fields = ('user', 'recipe')
    empty_value_display = ADMIN_EMPTY_VALUE


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления списком покупок

    Позволяет управлять списками покупок пользователей.

    Атрибуты:
    - list_display: поля для отображения (пользователь и рецепт)
    - search_fields: поиск по пользователю и названию рецепта
    - list_filter: фильтрация по пользователю
    - readonly_fields: поля только для чтения (пользователь и рецепт)
    - empty_value_display: значение для пустых полей
        (используется системное значение)
    """
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    readonly_fields = ('user', 'recipe')
    empty_value_display = ADMIN_EMPTY_VALUE
