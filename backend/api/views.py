import io
import os

from django.conf import settings as stgs
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import serializers as ss
from rest_framework import status
from rest_framework import viewsets as vs
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from foodgram_backend.messages import Warnings as Warn
from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.models import Follow
from users.serializers import (AvatarSerializer, CustomUserCreateSerializer,
                               CustomUserSerializer, SetPasswordSerializer,
                               SubscribeSerializer, SubscriptionsSerializer)

from .filters import IngredientFilter, RecipeFilter
from .mixins import RecipeActionMixin
from .pagination import CustomPagination
from .permissions import (IsAuthenticatedAndActive,
                          IsAuthenticatedAndActiveAndAuthorOrCreateOrReadOnly,
                          IsAuthenticatedAndActiveOrReadOnly)
from recipes.serializers import (FavoriteSerializer, IngredientsSerializer,
                                 RecipesGetSerializer, RecipesSerializer,
                                 ShoppingAddSerializer, TagsReadSerializer)

User = get_user_model()


class ShoppingPDFView(APIView):
    """
    API-представление для генерации PDF-файла со списком покупок

    Эндпоинт предоставляет возможность создания PDF-документа, содержащего
    агрегированный список ингредиентов из всех рецептов, добавленных
    пользователем в список покупок. Документ включает суммарное количество
    каждого ингредиента, необходимого для приготовления выбранных блюд.
    """
    permission_classes = (IsAuthenticatedAndActive,)

    def get(self, request):
        """
        Обработчик GET-запроса для генерации PDF-файла

        Метод получает список рецептов из корзины пользователя, агрегирует
        ингредиенты и их количество, генерирует PDF-документ и возвращает
        его в виде HTTP-ответа.

        Возвращает:
        - 200 OK: PDF-файл с списком покупок
        - 204 No Content: Список покупок пуст
        - 404 Not Found: Рецепты не найдены
        - 500 Internal Server Error: Внутренняя ошибка сервера
        """
        try:
            shopping_recipes = (
                request.user.shopping_user_set.all().values_list(
                    'recipe_id', flat=True
                )
            )

            ingredients_data = (
                IngredientRecipe.objects
                .select_related('ingredient')
                .filter(recipe_id__in=shopping_recipes)
                .values(
                    'ingredient__name',
                    'ingredient__measurement_unit'
                )
                .annotate(total_amount=Sum('amount'))
                .order_by('ingredient__name')
            )

            ingredients_list = [
                {
                    'name': ingredient['ingredient__name'],
                    'amount': ingredient['total_amount'],
                    'unit': ingredient['ingredient__measurement_unit'],
                }
                for ingredient in ingredients_data
            ]

            if not ingredients_list:
                return Response(
                    {'detail': Warn.SHOPPING_LIST_EMPTY},
                    status=status.HTTP_204_NO_CONTENT
                )

            pdf_buffer = self.generate_pdf(ingredients_list)
            return self.create_pdf_response(pdf_buffer)

        except IngredientRecipe.DoesNotExist:
            return Response(
                {'error': Warn.RECIPE_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def generate_pdf(self, ingredients):
        """
        Генерация PDF-документа со списком ингредиентов

        Метод создает PDF-документ с форматированным списком ингредиентов,
        включая их названия, количество и единицы измерения.

        Параметры:
        - ingredients: Список словарей с данными об ингредиентах
            - name: Название ингредиента
            - amount: Количество ингредиента
            - unit: Единица измерения

        Возвращает:
        - BytesIO: Буфер с сгенерированным PDF-документом
        """
        fonts_path = os.path.join(stgs.BASE_DIR, 'fonts')
        try:
            pdfmetrics.registerFont(
                TTFont(
                    'DejaVuSans', os.path.join(fonts_path, 'DejaVuSans.ttf')
                )
            )
        except Exception as e:
            raise ValidationError(
                f'{Warn.FONT_REGISTRATION_ERROR} {str(e)}'
            )

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        _, height = letter

        pdf.setFont('DejaVuSans', stgs.PDF_HEADER_FONT_SIZE)
        pdf.drawString(
            stgs.PDF_HEADER_MARGIN,
            height - stgs.PDF_PAGE_MARGIN,
            stgs.PDF_DOCUMENT_HEADER
        )

        y = height - stgs.PDF_HEADER_MARGIN
        pdf.setFont('DejaVuSans', stgs.PDF_TEXT_FONT_SIZE)

        for ingredient in ingredients:
            line = (
                f'- {ingredient["name"]}: '
                f'{ingredient["amount"]} {ingredient["unit"]}'
            )

            pdf.drawString(
                stgs.PDF_PAGE_MARGIN,
                y,
                line
            )
            y -= stgs.PDF_LINE_SPACING

            if y < stgs.PDF_PAGE_MARGIN:
                pdf.showPage()
                y = height - stgs.PDF_PAGE_MARGIN

        pdf.save()
        buffer.seek(0)
        return buffer

    def create_pdf_response(self, buffer):
        """
        Формирование HTTP-ответа с PDF-файлом

        Создает HTTP-ответ для скачивания сгенерированного PDF-файла.

        Параметры:
        - buffer: буфер с содержимым PDF-документа

        Возвращаемое значение:
        - FileResponse: HTTP-ответ с PDF-файлом для скачивания
        """
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=stgs.PDF_FILENAME_NAME,
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
            Warn.RECIPE_IN_SHOPPING_CART_EXISTS
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
            Warn.RECIPE_IN_FAVORITE_EXISTS
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
                try:
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    response_serializer = SubscriptionsSerializer(
                        author,
                        context={'request': request}
                    )
                    return Response(
                        response_serializer.data,
                        status=status.HTTP_201_CREATED
                    )
                except ss.ValidationError as e:
                    return Response(
                        e.detail,
                        status=status.HTTP_400_BAD_REQUEST
                    )

            elif request.method == 'DELETE':
                try:
                    subscription = Follow.objects.get(
                        user=request.user,
                        author=author
                    )
                    subscription.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except Follow.DoesNotExist:
                    return Response(
                        {'detail': Warn.SUBSCRIPTION_NOT_FOUND},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                {'detail': Warn.METHOD_NOT_ALLOWED},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        except Http404:
            return Response(
                {'detail': Warn.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:
            return Response(
                {'detail': Warn.REQUEST_PROCESSING_ERROR},
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

            try:
                serializer.is_valid(raise_exception=True)
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)

            except ss.ValidationError as e:
                return Response(
                    e.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
