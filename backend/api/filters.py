from django_filters import rest_framework as filters
import logging
from django.core.exceptions import ValidationError
from recipes.models import Ingredient, Recipe, Tag

logger = logging.getLogger(__name__)


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        help_text="Фильтрация рецептов по наличию в корзине (true/false)"
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorite_recipe_set__user=self.request.user
            ).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        try:
            if value:
                if self.request.user.is_authenticated:
                    return queryset.filter(
                        shopping_recipe_set__user=self.request.user
                    ).distinct()
                return queryset.none()
            return queryset
        except Exception as e:
            logger.error(f"Ошибка фильтрации корзины: {str(e)}")
            return queryset

    def filter_queryset(self, queryset):
        try:
            queryset = super().filter_queryset(queryset)
            return queryset.prefetch_related(
                'tags',
                'favorite_recipe_set',
                'shopping_recipe_set'
            )
        except Exception as e:
            logger.error(f"Ошибка в filter_queryset: {str(e)}")
            raise

    def validate_tags(self, value):
        existing_slugs = Tag.objects.values_list('slug', flat=True)
        invalid_slugs = [slug for slug in value if slug not in existing_slugs]
        if invalid_slugs:
            raise ValidationError(
                f"Неверные теги: {', '.join(invalid_slugs)}"
            )
        return value