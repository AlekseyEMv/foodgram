import io
import logging

from django.http import Http404

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework import viewsets as vs
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Ingredient, Recipe, Shopping, Tag
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import (IsAuthenticatedAndActive,
                          IsAuthenticatedAndActiveOrReadOnly)
from .serializers import (AvatarSerializer, BaseRecipeSerializer,
                          CustomUserCreateSerializer, CustomUserSerializer,
                          FavoriteSerializer, IngredientsSerializer,
                          RecipesGetSerializer, RecipesSerializer,
                          SetPasswordSerializer, ShoppingAddSerializer,
                          SubscribeSerializer, SubscriptionsSerializer,
                          TagsReadSerializer)

User = get_user_model()

logger = logging.getLogger(__name__)


class ShoppingPDFView(APIView):
    permission_classes = (IsAuthenticatedAndActive,)

    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    {'detail': 'Пользователь не авторизован'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            shoppings = Shopping.objects.filter(user=request.user)
            recipes = [s.recipe for s in shoppings]

            if not recipes:
                return Response(
                    {'detail': 'Список покупок пуст'},
                    status=status.HTTP_204_NO_CONTENT
                )

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
            response = FileResponse(
                buffer, as_attachment=True, filename='shopping_list.pdf'
            )
            response['Content-Type'] = 'application/pdf'
            return response

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IngredientsViewSet(vs.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagsViewSet(vs.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsReadSerializer
    pagination_class = None


class RecipesViewSet(vs.ModelViewSet):

    queryset = Recipe.objects.prefetch_related(
        'ingredientrecipe_set__ingredient',
        'ingredientrecipe_set',
        'favorite_recipe_set',
        'shopping_recipe_set'
    )
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedAndActiveOrReadOnly),
    filter_backends = (DjangoFilterBackend, SearchFilter,)
    filterset_class = RecipeFilter
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipesGetSerializer
        return RecipesSerializer

    def handle_request(self, request, instance=None):
        try:
            if instance:
                if instance.author != request.user:
                    raise PermissionDenied(
                        'Пользователь не является автором рецепта'
                    )

                serializer = self.get_serializer(
                    instance, data=request.data, partial=False
                )
            else:
                serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            recipe = serializer.save()

            if instance:
                recipe.refresh_from_db()

            response_serializer = RecipesGetSerializer(
                recipe, context={'request': request}
            )

            status_code = (
                status.HTTP_200_OK if instance else status.HTTP_201_CREATED
            )
            return Response(response_serializer.data, status=status_code)

        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'errors': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        return self.handle_request(request)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {'detail': 'Пользователь не является автором рецепта'},
                status=status.HTTP_403_FORBIDDEN
            )
        return self.handle_request(request, instance)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Проверяем, является ли пользователь автором
        if not instance.author == request.user:
            return Response(
                {'detail': 'У вас нет прав на удаление этого рецепта'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticatedAndActive,),
    )
    def shopping_cart(self, request, pk):
        try:
            recipe = Recipe.objects.get(id=pk)
            user = request.user
            shopping_cart = recipe.shopping_recipe_set.filter(user=user)

            if request.method == 'POST':
                if shopping_cart.exists():
                    return Response(
                        {'detail': 'Рецепт уже добавлен в корзину'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                serializer = ShoppingAddSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

                recipe_serializer = BaseRecipeSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    recipe_serializer.data, status=status.HTTP_201_CREATED
                )

            if shopping_cart.exists():
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(status=status.HTTP_400_BAD_REQUEST)

        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:
            return Response(
                {'detail': 'Произошла ошибка при обработке запроса'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticatedAndActive,),
    )
    def favorite(self, request, pk):
        try:
            recipe = Recipe.objects.get(id=pk)
            user = request.user
            favorite = recipe.favorite_recipe_set.filter(user=user)

            if request.method == 'POST':
                if favorite.exists():
                    return Response(
                        {'detail': 'Рецепт уже добавлен в избранное'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                serializer = FavoriteSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(status=status.HTTP_400_BAD_REQUEST)

        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {'detail': 'Произошла ошибка при обработке запроса'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=True,
        methods=['GET'],
        url_name='get_link',
        url_path='get-link'
    )
    def get_link(self, request, pk):
        try:
            recipe = self.get_object()
            if not recipe:
                return Response(status=status.HTTP_404_NOT_FOUND)

            link = request.build_absolute_uri(recipe.get_absolute_url())
            return Response({'short-link': link}, status=status.HTTP_200_OK)

        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST
            )



class UserProfileViewSet(vs.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = (SearchFilter,)
    search_fields = ('username', 'email')

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ('subscriptions', 'me', 'avatar', 'subscribe'):
            return [IsAuthenticatedAndActive()]
        elif self.action in ('list', 'create', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        response_data = serializer.data
        if not response_data.get('avatar'):
            response_data['avatar'] = ''
        return Response(data=response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            if request.data:
                serializer = AvatarSerializer(
                    request.user,
                    data=request.data,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                response_data = {
                    'avatar': (
                        request.user.avatar.url
                        if request.user.avatar else None
                    )
                }
                return Response(response_data)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
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
        try:
            logger.error("Начало обработки запроса на подписку")
            
            # Получаем автора по user_id
            try:
                author = get_object_or_404(User, pk=pk)
            except Http404:
                logger.error(f"Пользователь с ID {pk} не найден")
                return Response(
                    {'detail': 'Пользователь не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
            logger.error(f"Получен автор: {author.pk}")
            logger.error(f"Текущий пользователь: {request.user.pk}")
            logger.error(f"Входящие данные: {request.data}")
                        
            if request.method == 'POST':
                logger.error("Обработка POST запроса")
                if author == request.user:
                    return Response(
                        {'detail': 'Попытка подписаться на самого себя.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Формируем полные данные для подписки
                subscription_data = {
                    'author': author.pk
                }
                logger.error(f"Данные для подписки: {subscription_data}")
                
                serializer = SubscribeSerializer(
                    data=subscription_data,                    
                    context={'request': request, 'view': self}
                )
                logger.error("Инициализирован сериализатор")
                
                if serializer.is_valid():
                    logger.error("Данные валидны, сохраняем подписку")
                    serializer.save()
                    
                    # Возвращаем данные подписчика
                    user_serializer = SubscriptionsSerializer(
                        author,
                        context={'request': request}
                    )
                    logger.error("Сериализуем данные автора")
                    return Response(
                        user_serializer.data, 
                        status=status.HTTP_201_CREATED
                    )
                else:
                    logger.error(f"Ошибки валидации: {serializer.errors}")
                logger.error("Данные не прошли валидацию")
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            elif request.method == 'DELETE':
                logger.error("Обработка DELETE запроса")
                try:
                    subscription = Follow.objects.get(
                        user=request.user,
                        author=author
                    )
                    logger.error(f"Найденная подписка: {subscription.pk}")
                    if subscription.user != request.user:
                        logger.error("Попытка удаления чужой подписки")
                        return Response(
                            {'detail': 'Нет прав на удаление подписки'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    subscription.delete()
                    logger.error("Подписка успешно удалена")
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except Follow.DoesNotExist:
                    logger.error("Подписка не существует")
                    return Response(
                        {'detail': 'Подписка не существует'},
                        status=status.HTTP_400_BAD_REQUEST  # Изменено на 400
                    )              
            
            logger.error("Неизвестный метод запроса")
            return Response(
                {'detail': 'Неверный метод запроса'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        except Exception as e:
            logger.error(f"Произошла критическая ошибка: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Произошла внутренняя ошибка сервера'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            logger.error("Завершение обработки запроса на подписку")



class SetPasswordView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        try:
            user = request.user
            logger.error(f"Попытка смены пароля для пользователя {user.id}")
            
            # Логируем входящие данные
            logger.error(f"Входящие данные: {request.data}")
            
            serializer = SetPasswordSerializer(
                user, 
                data=request.data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                logger.error(f"Данные валидны для пользователя {user.id}")
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
