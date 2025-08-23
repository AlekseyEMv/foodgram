from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, viewsets as vs

from api.serializer import (
    CustomUserSerializer, IngredientSerializer, TagSerializer
)
from recipes.models import Ingredient, Tag


class IngredientsViewSet(vs.ReadOnlyModelViewSet):
    """
    Представление для работы с ингредиентами.

    Предоставляет доступ только для чтения для получения списка всех
    ингредиентов и для получения конкретного ингридиента по идентификатору.
    Поддерживает поиск по частичному вхождению в начале названия ингредиента.

    Attributes:
        queryset: Набор запросов на получения всех ингредиентов из базы данных.
        serializer_class: Класс сериализатора для преобразования объектов в
            JSON формат.
        filter_backends: Кортеж с бэкендами фильтрации.
        search_fields: Поля для поиска, поддерживает поиск по началу строки.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter)
    search_fields = ('i^name',)


class RecipesViewSet(vs.ModelViewSet):
    """
    """


class TagsViewSet(vs.ReadOnlyModelViewSet):
    """
    Представление для работы с тегами.

    Предоставляет доступ только для чтения для получения списка всех
    тегов и для получения конкретного тега по идентификатору.

    Attributes:
        queryset: Набор запросов на получения всех тегов из базы данных.
        serializer_class: Класс сериализатора для преобразования объектов в
            JSON формат.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CustomUserViewSet(UserViewSet):
    """
    """
