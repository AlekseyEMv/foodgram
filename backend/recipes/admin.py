from django.contrib import admin

from foodgram_backend.settings import ADMIN_EMPTY_VALUE

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe, Shopping,
                     Tag)

"""
Административная панель для управления моделями приложения
"""


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления тегами рецептов

    Атрибуты:
    - list_display: поля, отображаемые в списке тегов
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - empty_value_display: значение для пустых полей
    - ordering: порядок сортировки
    """
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления ингредиентами

    Атрибуты:
    - list_display: поля, отображаемые в списке ингредиентов
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - empty_value_display: значение для пустых полей
    - ordering: порядок сортировки
    """
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления рецептами

    Атрибуты:
    - list_display: поля, отображаемые в списке рецептов
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - filter_horizontal: поля для множественного выбора
    - empty_value_display: значение для пустых полей
    - ordering: порядок сортировки (по дате публикации, от новых к старым)
    """
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'pub_date'
    )
    search_fields = ('name', 'text')
    list_filter = ('author', 'tags', 'pub_date')
    filter_horizontal = ('tags',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('-pub_date',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления связями ингредиентов и рецептов

    Атрибуты:
    - list_display: поля, отображаемые в списке связей
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - empty_value_display: значение для пустых полей
    - ordering: порядок сортировки
    """
    list_display = ('id', 'ingredient', 'recipe', 'amount')
    search_fields = ('ingredient__name', 'recipe__name')
    list_filter = ('ingredient', 'recipe')
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('ingredient',)


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления избранными рецептами

    Атрибуты:
    - list_display: поля, отображаемые в списке избранного
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - empty_value_display: значение для пустых полей
    - ordering: порядок сортировки
    """

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('id',)


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления списком покупок

    Атрибуты:
    - list_display: поля, отображаемые в списке покупок
    - search_fields: поля для поиска
    - list_filter: доступные фильтры
    - empty_value_display
    - ordering: порядок сортировки
    """
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('id',)
