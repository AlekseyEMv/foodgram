from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """
    Фильтр для поиска ингредиентов по названию.

    Позволяет выполнять поиск ингредиентов по началу названия
    (case-insensitive).
    """
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        help_text='Поиск ингредиентов по началу названия (регистронезависимый)'
    )

    class Meta:
        """
        Мета-класс конфигурации фильтра.

        Определяет модель и доступные поля для фильтрации.
        """
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для поиска рецептов.

    Предоставляет возможности фильтрации рецептов по различным критериям:
    - Теги
    - Автор
    - Наличие в избранном
    - Наличие в корзине покупок
    """
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
        help_text='Фильтрация рецептов по тегам (можно указать несколько)'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        help_text='Фильтрация рецептов по наличию в избранном (true/false)'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        help_text='Фильтрация рецептов по наличию в корзине (true/false)'
    )

    class Meta:
        """
        Мета-класс конфигурации фильтра.

        Определяет модель и доступные поля для фильтрации.
        """
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация рецептов по наличию в избранном.

        Параметры:
        - queryset: исходный набор запросов
        - name: имя фильтра
        - value: значение фильтра (True/False)

        Возвращает:
        - Отфильтрованный набор запросов
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorite_recipe_set__user=self.request.user
            ).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация рецептов по наличию в корзине покупок.

        Параметры:
        - queryset: исходный набор запросов
        - name: имя фильтра
        - value: значение фильтра (True/False)

        Возвращает:
        - Отфильтрованный набор запросов

        Обрабатывает исключения и логирует ошибки.
        """
        try:
            if value:
                if self.request.user.is_authenticated:
                    return queryset.filter(
                        shopping_recipe_set__user=self.request.user
                    ).distinct()
                return queryset.none()
            return queryset
        except Exception:
            return queryset

    def filter_queryset(self, queryset):
        """
        Основной метод фильтрации набора запросов.

        Добавляет предварительную загрузку связанных объектов для оптимизации.

        Параметры:
        - queryset: исходный набор запросов

        Возвращает:
        - Отфильтрованный и оптимизированный набор запросов
        """
        try:
            queryset = super().filter_queryset(queryset)
            return queryset.prefetch_related(
                'tags',
                'favorite_recipe_set',
                'shopping_recipe_set'
            )
        except Exception:
            raise

    def validate_tags(self, value):
        """
        Валидация тегов для фильтрации.

        Метод проверяет существование указанных тегов в базе данных и
        вызывает исключение ValidationError при обнаружении несуществующих
        тегов.

        Параметры:
        - value: список тегов (slug'ов) для проверки

        Возвращает:
        - Валидированный список тегов при успешном выполнении

        Вызывает:
        - ValidationError если обнаружены несуществующие теги
        """
        existing_slugs = Tag.objects.values_list('slug', flat=True)
        invalid_slugs = [slug for slug in value if slug not in existing_slugs]
        if invalid_slugs:
            raise ValidationError(
                f"Неверные теги: {', '.join(invalid_slugs)}"
            )
        return value
