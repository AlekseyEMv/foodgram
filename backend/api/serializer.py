from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers as ss


from recipes.models import (
    Ingredient,
    IngredientRecipe,
    FavoriteRecipe,
    Follow,
    Recipe,
    ShoppingRecipe,
    Tag
)

User = get_user_model()


class IngredientSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Отвечает за преобразование объектов модели Ingredient в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipesGetSerializer(ss.ModelSerializer):
    """
    """


class TagSerializer(ss.ModelSerializer):
    """
    Сериализатор для работы с тегами.

    Отвечает за преобразование объектов модели Tags в JSON формат
    и обратно при необходимости. Определяет структуру данных,
    которые будут передаваться через API.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для работы с пользовательскими данными.

    Предоставляет полную информацию о пользователе, включая:
    - основные данные профиля
    - информацию о подписке текущего пользователя на данного пользователя

    Атрибуты:
        is_subscribed:
            Поле, указывающее на наличие подписки текущего пользователя
            на данного пользователя
    """
    is_subscribed = ss.SerializerMethodField(
        help_text='Флаг подписки текущего пользователя на данного пользователя'
    )

    class Meta:
        """
        Настройки сериализатора.

        Определяет модель и поля для сериализации.
        """
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
        read_only_fields = ('id', 'email')

    def get_is_subscribed(self, obj):
        """
        Метод для определения статуса подписки.

        Проверяет, подписан ли текущий аутентифицированный пользователь
        на пользователя, данные которого сериализуются.

        Аргументы:
            obj: экземпляр пользователя, для которого проверяется подписка

        Возвращает:
            bool: True, если текущий пользователь подписан, иначе False
        """
        current_user = self.context['request'].user
        return (
            current_user.follower.filter(author=obj).exists()
            if current_user.is_authenticated
            else False
        )
