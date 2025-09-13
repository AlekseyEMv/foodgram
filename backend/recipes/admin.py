from django.contrib import admin

from foodgram_backend.settings import ADMIN_EMPTY_VALUE

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe, Shopping,
                     Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
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
    list_display = ('id', 'ingredient', 'recipe', 'amount')
    search_fields = ('ingredient__name', 'recipe__name')
    list_filter = ('ingredient', 'recipe')
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('ingredient',)


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('id',)


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    empty_value_display = ADMIN_EMPTY_VALUE
    ordering = ('id',)
