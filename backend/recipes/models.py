from django.db import models as ms
from django.contrib.auth import get_user_model
from django.core.validators import (
    FileExtensionValidator, MinLengthValidator, MinValueValidator
)
from django.urls import reverse

from foodgram_backend.settings import (
    ADMIN_MAX_LENGTH,
    INGREDIENT_MAX_LENGTH,
    INGRIGIENTS_MIN_VALUE,
    MIN_COOKING_TIME,
    RECIPE_MAX_LENGTH,
    RECIPE_MIN_LENGTH,
    TAG_MAX_LENGTH,
    UNIT_MAX_LENGTH
)

User = get_user_model()


class Ingredient(ms.Model):
    """Модель ингредиента с названием и единицей измерения.

    Атрибуты:
        name: Название ингредиента. Максимальная длина — 128 символов.
        measurement_unit: Единица измерения ингредиента.
            Максимальная длина — 64 символа.

    Класс Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
        ordering: Сортировка по умолчанию (по названию).

    Методы:
        __str__: Возвращает строковое представление в формате:
            «Название (Единица измерения)».

    Пример использования:
        >>> flour = Ingredient.objects.create(
        ...     name='Мука пшеничная',
        ...     measurement_unit='г'
        ... )
        >>> print(flour)
        Мука пшеничная (г)
    """
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
    """Модель тега с уникальными названием и идентификатором.

    Атрибуты:
        name: Уникальное название тега. Максимальная длина — 32 символа.
        slug: Уникальный идентификатор тега. Максимальная длина — 32 символа.

    Класс Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
        ordering: Сортировка по умолчанию (по названию).

    Методы:
        __str__: Возвращает строковое представление в формате: «Название».

    Пример использования:
    >>> breakfast = Tag.objects.create(name='Завтрак', slug='breakfast')
    >>> print(breakfast)
    Завтрак
    """
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
        blank=True,
        null=True,
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
        return reverse('recipe-detail', kwargs={'pk': self.pk})


class IngredientRecipe(ms.Model):
    """Модель связи ингредиента с рецептом, включая количество.

    Атрибуты:
        ingredient: Ссылка на модель Ingredient.
            Каскадное удаление при удалении ингредиента.
            related_name='ingredient' - позволяет обращаться ко всем рецептам
            ингредиента через ingredient.recipe.all().
        recipe: Ссылка на модель Recipe.
            Каскадное удаление при удалении рецепта.
            related_name='recipe' - позволяет обращаться ко всем ингредиентам
            рецепта через recipe.ingredient.all().
        amount: Количество ингредиента в рецепте. Минимальное значение — 1.

    Валидаторы:
        MinValueValidator - гарантирует, что количество не меньше 1.

    Класс Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
        ordering: Сортировка по умолчанию (по полю ingredient).
        constraints: Ограничение уникальности пары ingredient - recipe.

    Методы:
        __str__: Возвращает строковое представление
            в формате «(Рецепт) Ингредиент».

    Пример использования:
    >>> from recipes.models import Recipe, Ingredient
    >>> recipe = Recipe.objects.get(id=1)
    >>> flour = Ingredient.objects.get(name='Мука')
    >>> IngredientRecipe.objects.create(
    ...     recipe=recipe,
    ...     ingredient=flour,
    ...     amount=200
    ... )
    <IngredientRecipe: (Рецепт хлеба) Мука>

    Особенности:
        Гарантирует уникальность связки ингредиент-рецепт.
        При удалении рецепта или ингредиента автоматически удаляется связь.
    """
    ingredient = ms.ForeignKey(
        Ingredient,
        on_delete=ms.CASCADE,
        related_name='ingredient',
        verbose_name='Ингридиент'
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    amount = ms.PositiveSmallIntegerField(
        default=INGRIGIENTS_MIN_VALUE,
        validators=(
            MinValueValidator(
                limit_value=INGRIGIENTS_MIN_VALUE,
                message=(
                    'Количество ингридиентов в рецепте не может быть '
                    f'меньше {INGRIGIENTS_MIN_VALUE}'
                )
            ),
        ),
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
    """
    Абстрактная модель для связи пользователя и рецепта.

    Служит базой для конкретных реализаций (например, избранное
        или список покупок).

    Атрибуты:
        user: Ссылка на пользователя, который взаимодействует с рецептом.
        recipe: Ссылка на рецепт, связанный с пользователем.

    Meta:
        abstract: Указывает, что модель абстрактная (не создаёт таблицу в БД).
        constraints: Ограничение уникальности пары пользователь-рецепт.
    """
    user = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='%(class)s_user',
        verbose_name='Пользователь',
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='%(class)s_recipe',
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
    """
    Модель для хранения избранных рецептов пользователя.

    Наследует функциональность UsingRecipe, добавляя метаданные для админки.

    Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
    """
    class Meta(UsingRecipe.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class Shopping(UsingRecipe):
    """
    Модель для списка покупок, связанных с рецептами.

    Позволяет пользователю сохранять рецепты для дальнейшего использования.

    Meta:
        verbose_name: Название модели в единственном числе для админ-панели.
        verbose_name_plural: Название модели во множественном числе.
    """
    class Meta(UsingRecipe.Meta):
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"
