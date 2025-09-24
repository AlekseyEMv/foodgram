import io

from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework import viewsets as vs
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from foodgram_backend.messages import Warnings
from foodgram_backend.settings import PDF_FILENAME_NAME
from recipes.models import Ingredient, Recipe, Shopping, Tag
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .mixins import RecipeActionMixin
from .pagination import CustomPagination
from .permissions import (IsAuthenticatedAndActive,
                          IsAuthenticatedAndActiveAndAuthorOrCreateOrReadOnly,
                          IsAuthenticatedAndActiveOrReadOnly)
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, FavoriteSerializer,
                          IngredientsSerializer, RecipesGetSerializer,
                          RecipesSerializer, SetPasswordSerializer,
                          ShoppingAddSerializer, SubscribeSerializer,
                          SubscriptionsSerializer, TagsReadSerializer)

User = get_user_model()


class ShoppingPDFView(APIView):
    """
    API-представление для генерации PDF-файла со списком покупок

    Класс предоставляет эндпоинт для создания PDF-документа,
    содержащего список рецептов, добавленных пользователем в список покупок.
    """
    permission_classes = (IsAuthenticatedAndActive,)

    def get(self, request):
        """
        Получение PDF-файла со списком покупок

        Метод обрабатывает GET-запрос и возвращает PDF-файл со списком
        рецептов из корзины пользователя.

        Параметры:
        - request: объект запроса

        Возвращаемые значения:
        - 204 NO CONTENT: если список покупок пуст
        - 500 INTERNAL SERVER ERROR: при ошибке генерации PDF
        - FileResponse: PDF-файл со списком покупок
        """
        shoppings = Shopping.objects.filter(user=request.user)
        recipes = [s.recipe for s in shoppings]

        if not recipes:
            return Response(
                {'detail': Warnings.SHOPPING_LIST_EMPTY},
                status=status.HTTP_204_NO_CONTENT
            )

        try:
            pdf_buffer = self.generate_pdf(recipes)
            return self.create_pdf_response(pdf_buffer)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def generate_pdf(self, recipes):
        """
        Генерация PDF-документа

        Метод создает PDF-файл с перечнем рецептов из списка покупок.

        Параметры:
        - recipes: список рецептов для включения в PDF

        Возвращаемое значение:
        - BytesIO: буфер с сгенерированным PDF
        """
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        _, height = letter

        pdf.setFont('Helvetica-Bold', 16)
        pdf.drawString(100, height - 50, 'Список покупок')

        y = height - 100
        for recipe in recipes:
            pdf.setFont('Helvetica', 12)
            pdf.drawString(50, y, f'• {recipe.name}')
            pdf.drawString(150, y, f'Время: {recipe.cooking_time} мин')
            y -= 20
            if y < 50:
                pdf.showPage()
                y = height - 50

        pdf.save()
        buffer.seek(0)
        return buffer

    def create_pdf_response(self, buffer):
        """
        Создание HTTP-ответа с PDF-файлом

        Метод формирует ответ с PDF-документом для скачивания.

        Параметры:
        - buffer: буфер с PDF-содержимым

        Возвращаемое значение:
        - FileResponse: HTTP-ответ с PDF-файлом
        """
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=PDF_FILENAME_NAME,
            content_type='application/pdf'
        )


class IngredientsViewSet(vs.ReadOnlyModelViewSet):
    """
    ViewSet для работы с ингредиентами

    Предоставляет REST API для получения ингредиентов.
    Поддерживает фильтрацию и поиск по названию ингредиента.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagsViewSet(vs.ReadOnlyModelViewSet):
    """
    ViewSet для работы с тегами

    Предоставляет REST API для списка всех тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagsReadSerializer
    pagination_class = None


class RecipesViewSet(vs.ModelViewSet, RecipeActionMixin):
    """
    API для работы с рецептами.

    Предоставляет возможности для создания, чтения, обновления и
    удаления рецептов.
    Включает дополнительные действия для работы с корзиной покупок и избранным.
    """
    # queryset для рецептов с предварительной загрузкой связанных объектов
    queryset = Recipe.objects.prefetch_related(
        'ingredientrecipe_set',
        'favorite_recipe_set',
        'shopping_recipe_set'
    )
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter,)
    filterset_class = RecipeFilter
    search_fields = ('name',)

    def get_permissions(self):
        """
        Получение соответствующих разрешений.

        Возвращает:
        - Список разрешений в зависимости от действия.
        """
        if self.action == 'create':
            return [IsAuthenticatedAndActiveOrReadOnly()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticatedAndActiveAndAuthorOrCreateOrReadOnly()]
        return [IsAuthenticatedAndActiveOrReadOnly()]

    def get_serializer_class(self):
        """
        Получение соответствующего сериализатора.

        Возвращает:
        - Класс сериализатора в зависимости от действия.
        """
        if self.action in ('list', 'retrieve'):
            return RecipesGetSerializer
        return RecipesSerializer

    def create(self, request, *args, **kwargs):
        """
        Создание нового рецепта.

        Параметр:
        - request: HTTP-запрос

        Возвращает:
        - Ответ с созданным рецептом
        """
        return self.handle_request(request, RecipesGetSerializer)

    def update(self, request, *args, **kwargs):
        """
        Обновление существующего рецепта.

        Параметр:
        - request: HTTP-запрос

        Возвращает:
        - Ответ с обновленным рецептом
        """
        instance = self.get_object()
        return self.handle_request(request, RecipesGetSerializer, instance)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def shopping_cart(self, request, pk):
        """
        Управление списком покупок для рецепта.

        Методы:
        - POST: Добавление в список покупок
        - DELETE: Удаление из списка покупок

        Параметр:
        - request: HTTP-запрос
        - pk: ID рецепта

        Возвращает:
        - Ответ с результатом операции
        """
        return self._handle_action(
            Recipe,
            request,
            pk,
            'shopping_recipe_set',
            ShoppingAddSerializer,
            Warnings.RECIPE_IN_SHOPPING_CART_EXISTS
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def favorite(self, request, pk):
        """
        Управление избранными рецептами.

        Методы:
        - POST: Добавление в избранное
        - DELETE: Удаление из избранного

        Параметр:
        - request: HTTP-запрос
        - pk: ID рецепта

        Возвращает:
        - Ответ с результатом операции
        """
        return self._handle_action(
            Recipe,
            request,
            pk,
            'favorite_recipe_set',
            FavoriteSerializer,
            Warnings.RECIPE_IN_FAVORITE_EXISTS
        )

    @action(
        detail=True, methods=['GET'], url_name='get_link', url_path='get-link'
    )
    def get_link(self, request, pk):
        """
        Получение прямой ссылки на рецепт.

        Метод API предоставляет возможность получить абсолютную ссылку
        на конкретный рецепт по его идентификатору.

        Параметры:
        - request: входящий HTTP-запрос
        - pk: уникальный идентификатор рецепта

        Возвращаемые данные:
        JSON-объект следующего формата:
        {
            "short-link": "https://example.com/api/recipes/1/"
        }
        """
        recipe = self.get_object()
        link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({'short-link': link}, status=status.HTTP_200_OK)


class UserProfileViewSet(vs.ModelViewSet):
    """
    API для управления профилями пользователей, подписками и аватарами

    Предоставляет следующие возможности:
    - Получение списка пользователей
    - Создание новых пользователей
    - Управление профилем текущего пользователя
    - Работа с подписками
    - Управление аватаром
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = (SearchFilter,)
    search_fields = ('username', 'email')

    def get_queryset(self):
        """
        Добавляем prefetch_related для оптимизации.
        """
        return User.objects.prefetch_related(
            'following',  # Предзагрузка связанных объектов Follow
            'follower'    # Если есть обратная связь
        )

    def get_serializer_class(self):
        """
        Определяет класс сериализатора в зависимости от действия

        Возвращает:
            CustomUserCreateSerializer - для создания пользователя
            CustomUserSerializer - для остальных операций
        """
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        """
        Определяет разрешения для различных действий

        Возвращает:
            IsAuthenticatedAndActive - для операций с подписками и профилем
            AllowAny - для получения списка и создания пользователей
        """
        if self.action in ('subscriptions', 'me', 'avatar', 'subscribe'):
            return [IsAuthenticatedAndActive()]
        elif self.action in ('list', 'create', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Получение информации о текущем пользователе

        Возвращает:
            JSON-объект с данными профиля пользователя
            Статус HTTP_200_OK
        """
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        response_data = serializer.data
        if not response_data.get('avatar'):
            response_data['avatar'] = ''
        return Response(data=response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        """
        Управление аватаром пользователя

        Методы:
            PUT - загрузка нового аватара
            DELETE - удаление текущего аватара

        Возвращает:
            При загрузке - URL нового аватара
            При удалении - статус HTTP_204_NO_CONTENT
        """
        if request.method == 'PUT':
            if request.data:
                serializer = AvatarSerializer(
                    request.user,
                    data=request.data,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(
                    {
                        'avatar': (
                            request.user.avatar.url
                            if request.user.avatar
                            else None
                        )
                    }
                )
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """
        Получение списка подписок текущего пользователя

        Возвращает:
            Список пользователей, на которых подписан текущий пользователь
            С пагинацией
            Статус HTTP_200_OK
        """
        queryset = User.objects.filter(following__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        url_name='subscribe'
    )
    def subscribe(self, request, pk=None):
        """
        Управление подпиской на пользователя

        Методы:
            POST - создание подписки
            DELETE - удаление подписки

        Параметры:
            pk - идентификатор пользователя, на которого подписываемся

        Возвращает:
            При создании - данные о подписчике
            При удалении - статус HTTP_201_CREATED
            """
        try:
            author = get_object_or_404(User, pk=pk)
            if request.method == 'POST':
                serializer = SubscribeSerializer(
                    data={'author': author.pk},
                    context={'request': request, 'view': self}
                )
                if serializer.is_valid():
                    serializer.save()
                    response_serializer = SubscriptionsSerializer(
                        author,
                        context={'request': request}
                    )
                    return Response(
                        response_serializer.data,
                        status=status.HTTP_201_CREATED
                    )
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            elif request.method == 'DELETE':
                try:
                    subscription = Follow.objects.get(
                        user=request.user,
                        author=author
                    )
                    if subscription.user != request.user:
                        return Response(
                            {'detail': Warnings.SUBSCRIPTION_DELETE_FORBIDDEN},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    subscription.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except Follow.DoesNotExist:
                    return Response(
                        {'detail': Warnings.SUBSCRIPTION_NOT_FOUND},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                {'detail': Warnings.METHOD_NOT_ALLOWED},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        except Http404:
            return Response(
                {'detail': Warnings.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:
            return Response(
                {'detail': Warnings.REQUEST_PROCESSING_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SetPasswordView(APIView):
    """
    API для смены пароля пользователя
    """
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        """
        Метод для смены пароля пользователя

        Возвращает:
        - 204 No Content при успешной смене пароля
        - 400 Bad Request при ошибках валидации
        - 500 Internal Server Error при критических ошибках
        """
        try:
            user = request.user

            serializer = SetPasswordSerializer(
                user,
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
