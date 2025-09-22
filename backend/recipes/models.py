import logging

from django.contrib.auth import get_user_model
from django.core.validators import (FileExtensionValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import models as ms
from django.urls import reverse

from foodgram_backend.settings import (ADMIN_MAX_LENGTH, INGREDIENT_MAX_LENGTH,
                                       INGRIGIENTS_MIN_VALUE, MIN_COOKING_TIME,
                                       RECIPE_MAX_LENGTH, RECIPE_MIN_LENGTH,
                                       TAG_MAX_LENGTH, UNIT_MAX_LENGTH)

User = get_user_model()

logger = logging.getLogger(__name__)


class Ingredient(ms.Model):
    name = ms.CharField(
        max_length=INGREDIENT_MAX_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = ms.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(ms.Model):
    name = ms.CharField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Имя'
    )
    slug = ms.SlugField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(ms.Model):
    author = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        verbose_name='Автор'
    )
    name = ms.CharField(
        max_length=RECIPE_MAX_LENGTH,
        verbose_name='Название',
        validators=[
            MinLengthValidator(
                RECIPE_MIN_LENGTH,
                f'Название должно быть не менее {RECIPE_MIN_LENGTH} символов.'
            )
        ]
    )
    image = ms.ImageField(
        upload_to='recipes/images/',
        default='default.jpg',
        # blank=True,
        # null=True,
        verbose_name='Картинка',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
    )
    text = ms.TextField('Описание')
    ingredients = ms.ManyToManyField(
        Ingredient, through='IngredientRecipe'
    )
    tags = ms.ManyToManyField(
        Tag,
        blank=True,
        verbose_name='Теги'
    )
    cooking_time = ms.PositiveSmallIntegerField(
        default=MIN_COOKING_TIME,
        validators=[
            MinValueValidator(
                limit_value=MIN_COOKING_TIME,
                message=(
                    'Минимальное время приготовления рецепта не может быть '
                    f'меньше {MIN_COOKING_TIME}'
                )
            ),
        ],
        verbose_name='Время приготовления (минуты)'
    )
    pub_date = ms.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:ADMIN_MAX_LENGTH]

    def get_absolute_url(self):
        return reverse('api:recipes-detail', kwargs={'pk': self.pk})


class IngredientRecipe(ms.Model):
    ingredient = ms.ForeignKey(
        Ingredient,
        on_delete=ms.CASCADE,
        related_name='recipe_set',
        verbose_name='Ингридиент'
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='ingredientrecipe_set',
        verbose_name='Рецепт'
    )
    amount = ms.PositiveSmallIntegerField(
        default=INGRIGIENTS_MIN_VALUE,
        validators=[
            MinValueValidator(
                limit_value=INGRIGIENTS_MIN_VALUE,
                message=(
                    'Количество ингридиентов в рецепте не может быть '
                    f'меньше {INGRIGIENTS_MIN_VALUE}'
                )
            ),
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ('ingredient',)
        constraints = [
            ms.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'({self.recipe}) {self.ingredient}'


class UsingRecipe(ms.Model):
    user = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='%(class)s_user_set',  # Оставляем как есть
        verbose_name='Пользователь',
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='%(class)s_recipe_set',  # Оставляем как есть
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            ms.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]


class Favorite(UsingRecipe):
    class Meta(UsingRecipe.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class Shopping(UsingRecipe):
    class Meta(UsingRecipe.Meta):
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
