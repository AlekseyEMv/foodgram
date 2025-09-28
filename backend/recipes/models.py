from functools import partial

from django.conf import settings as stgs
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models as ms
from django.urls import reverse

from api.validators import validate_picture_format, validate_value_interval

from .utils import generate_unique_slug

# Валидатор для изображений рецептов с заданным максимальным размером.
validate_recipe_image = partial(
    validate_picture_format, max_file_size=stgs.MAX_FILE_SIZE
)

# Валидатор для проверки количества ингридиентов в заданном интервале
validate_amount_interval = partial(
    validate_value_interval,
    min_value=stgs.MIN_AMOUNT_VALUE,
    max_value=stgs.MAX_AMOUNT_VALUE
)

# Валидатор для проверки времени приготовления в заданном интервале
validate_coocking_time_interval = partial(
    validate_value_interval,
    min_value=stgs.MIN_COOKING_TIME,
    max_value=stgs.MAX_COOKING_TIME
)


User = get_user_model()


class Ingredient(ms.Model):
    """
    Модель ингредиента

    Представляет собой базовый элемент для рецептов, содержащий название
    и единицу измерения.
    """
    name = ms.CharField(
        max_length=stgs.INGREDIENT_MAX_LENGTH,
        verbose_name='Название',
        help_text='Название ингредиента'
    )
    measurement_unit = ms.CharField(
        max_length=stgs.UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
        help_text='Единицы измерения (грамм, литр, штука и т.д.)'
    )

    class Meta:
        """
        Мета-информация модели

        Определяет название в админке и порядок сортировки.
        """
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        """
        Строковое представление объекта

        Возвращает название ингредиента с единицей измерения.
        """
        return f'{self.name} ({self.measurement_unit})'


class Tag(ms.Model):
    """
    Модель тега для категоризации рецептов

    Представляет собой сущность, используемую для тегирования и категоризации
    рецептов в системе. Каждый тег имеет уникальное имя и автоматически
    генерируемый slug.

    Основные характеристики:
    - Уникальность имени и slug
    - Автоматическая генерация slug на основе имени
    - Возможность категоризации рецептов
    """
    name = ms.CharField(
        max_length=stgs.TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Имя',
        help_text='Название тега'
    )
    slug = ms.SlugField(
        max_length=stgs.TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Автоматически генерируемый идетификатор на основе названия'
    )

    class Meta:
        """
        Мета-информация модели

        Определяет настройки отображения и поведения модели:
        - Название в админ-панели
        - Порядок сортировки
        - Уникальные ограничения
        """
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        """
        Строковое представление объекта

        Возвращает название тега для удобного отображения
        в интерфейсе администратора и других представлениях.

        Возвращает:
        - Название тега
        """
        return self.name

    def save(self, *args, **kwargs):
        """
        Метод сохранения объекта

        Переопределенный метод для автоматической генерации slug
        при создании или обновлении тега.

        Если slug не был установлен вручную, генерируется уникальный
        slug на основе имени тега.
        """
        if not self.slug:
            self.slug = generate_unique_slug(self.name, Tag)
        super().save(*args, **kwargs)


class Recipe(ms.Model):
    """
    Модель рецепта

    Основная модель для хранения информации о рецептах.
    """
    author = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        verbose_name='Автор',
        help_text='Автор рецепта'
    )
    name = ms.CharField(
        max_length=stgs.RECIPE_MAX_LENGTH,
        verbose_name='Название',
        validators=[
            MinLengthValidator(
                stgs.RECIPE_MIN_LENGTH,
                'Название должно быть не менее '
                f'{stgs.RECIPE_MIN_LENGTH} символов.'
            )
        ],
        help_text='Название рецепта'
    )
    image = ms.ImageField(
        upload_to='recipes/images/',
        default='default.jpg',
        verbose_name='Картинка',
        validators=[validate_recipe_image],
        help_text='Размер изображения рецепта (максимум MAX_FILE_SIZE МБ)'
    )
    text = ms.TextField(
        verbose_name='Описание',
        help_text='Подробное описание процесса приготовления'
    )
    ingredients = ms.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        help_text='Ингредиенты для рецепта'
    )
    tags = ms.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Tеги для категоризации рецепта'
    )
    cooking_time = ms.PositiveSmallIntegerField(
        default=stgs.MIN_COOKING_TIME,
        validators=[validate_coocking_time_interval],
        verbose_name='Время приготовления (минуты)',
        help_text='Время приготовления рецепта в минутах'
    )
    pub_date = ms.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Автоматически заполняемая дата публикации рецепта'
    )

    class Meta:
        """
        Мета-информация модели

        Определяет название в админке, порядок сортировки и связанные имена
        """
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        """
        Строковое представление объекта

        Возвращает название рецепта с ограничением по длине
        """
        return self.name[:stgs.ADMIN_MAX_LENGTH]

    def get_absolute_url(self):
        """
        Возвращает абсолютный URL для детализации рецепта
        """
        return reverse('api:recipes-detail', kwargs={'pk': self.pk})


class IngredientRecipe(ms.Model):
    """
    Модель связи между ингредиентами и рецептами

    Хранит информацию о количестве ингредиентов в рецепте
    """
    ingredient = ms.ForeignKey(
        Ingredient,
        on_delete=ms.CASCADE,
        related_name='recipe_set',
        verbose_name='Ингредиент',
        help_text='Ингредиент для рецепта'
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='ingredientrecipe_set',
        verbose_name='Рецепт',
        help_text='Рецепт, к которому относится ингредиент'
    )
    amount = ms.PositiveSmallIntegerField(
        default=stgs.MIN_AMOUNT_VALUE,
        validators=[validate_amount_interval],
        verbose_name='Количество',
        help_text=(
            'Количество ингредиента в рецепте, которое '
            'сравнивается с минимальным значением'
        )
    )

    class Meta:
        """
        Мета-информация модели

        Определяет уникальность связи между ингредиентом и рецептом
        """
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
        """
        Строковое представление объекта

        Возвращает название рецепта и ингредиента
        """
        return f'({self.recipe}) {self.ingredient}'


class UsingRecipe(ms.Model):
    """
    Абстрактная базовая модель для связей пользователей с рецептами

    Представляет собой основу для моделей избранного и списка покупок.
    Обеспечивает уникальную связь между пользователем и рецептом.
    """
    user = ms.ForeignKey(
        User,
        on_delete=ms.CASCADE,
        related_name='%(class)s_user_set',
        verbose_name='Пользователь',
        help_text='Пользователь, создавший связь с рецептом'
    )
    recipe = ms.ForeignKey(
        Recipe,
        on_delete=ms.CASCADE,
        related_name='%(class)s_recipe_set',
        verbose_name='Рецепт',
        help_text='Рецепт, связанный с пользователем'
    )

    class Meta:
        """
        Мета-информация абстрактной модели

        Определяет уникальность связи между пользователем и рецептом
        """
        abstract = True
        constraints = [
            ms.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]


class Favorite(UsingRecipe):
    """
    Модель избранного рецепта

    Хранит информацию о рецептах, добавленных пользователем в избранное
    """
    class Meta(UsingRecipe.Meta):
        """
        Мета-информация избранного рецепта

        Определяет название в админке
        """
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        """
        Возвращает строковое представление избранного рецепта

        Хранит информацию о избранных рецептах
        """
        return (
            f'Пользователь {self.user.get_full_name()} добавил '
            f'в избранное рецепт: {self.recipe.name}'
        )


class Shopping(UsingRecipe):
    """
    Модель списка покупок

    Хранит информацию о рецептах, добавленных пользователем в список покупок
    """
    class Meta(UsingRecipe.Meta):
        """
        Мета-информация списка покупок

        Определяет название в админке
        """
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        """
        Строковое представление объекта

        Возвращает информацию о связи пользователя с рецептом
        """
        return (
            f'Пользователь {self.user.username} добавил рецепт '
            f'{self.recipe.name} в {self._meta.verbose_name}'
        )
