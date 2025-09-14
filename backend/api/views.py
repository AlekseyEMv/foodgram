from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework import viewsets as vs
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Ingredient, Recipe, Shopping, Tag
from users.models import Follow
from users.serializers import (AvatarSerializer, CustomUserCreateSerializer,
                               CustomUserSerializer)

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthenticatedAndActive
from .serializers import (FavoriteSerializer, IngredientsSerializer,
                          RecipesGetSerializer, RecipesSerializer,
                          ShoppingAddSerializer, SubscribeSerializer,
                          SubscriptionsSerializer, TagsSerializer)

User = get_user_model()


class IngredientsViewSet(vs.ReadOnlyModelViewSet):
    """Представление модели ингридиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('i^name',)


class ShoppingPDFView(APIView):
    permission_classes = (IsAuthenticatedAndActive,)

    def get(self, request):
        try:
            shoppings = Shopping.objects.filter(user=request.user)
            recipes = [s.recipe for s in shoppings]

            response = FileResponse(content_type='application/pdf')
            pdf = canvas.Canvas(response, pagesize=letter)
            width, height = letter

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(100, height - 50, "Список покупок")

            y = height - 100
            for recipe in recipes:
                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, y, f"• {recipe.name}")
                pdf.drawString(150, y, f"Время: {recipe.cooking_time} мин")
                y -= 20
                if y < 50:
                    pdf.showPage()
                    y = height - 50

            pdf.save()
            response[
                'Content-Disposition'
            ] = 'attachment; filename="shopping_list.pdf"'
            return response

        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipesViewSet(vs.ModelViewSet):

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedAndActive),
    filter_backends = (DjangoFilterBackend, SearchFilter,)
    filterset_class = RecipeFilter
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipesGetSerializer
        return RecipesSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticatedAndActive,),
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = get_object_or_404(User, id=request.user.id)
        shopping_cart = recipe.recipe_download.filter(user=user)
        if request.method == 'POST':
            serializer = ShoppingAddSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticatedAndActive,),
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = get_object_or_404(User, id=request.user.id)
        favorite = recipe.recipe_favorite.filter(user=user)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['GET'],
        url_name='get_link',
        url_path='get-link'
    )
    def get_link(self, request, pk):
        recipe = self.get_object()
        link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({'short-link': link}, status=status.HTTP_200_OK)


class TagsViewSet(vs.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer


class UserProfileViewSet(vs.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedAndActive,)
    pagination_class = CustomPagination
    filter_backends = (SearchFilter,)
    search_fields = ('username', 'email')

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ('subscriptions', 'me', 'avatar'):
            return [IsAuthenticatedAndActive()]
        elif self.action in ('list', 'create'):
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'])
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
                return Response(serializer.data)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            self.request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class SubscribeViewSet(CreateModelMixin, DestroyModelMixin, vs.GenericViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticatedAndActive,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        author_id = self.kwargs.get('pk')
        return get_object_or_404(
            Follow,
            user=self.request.user,
            author_id=author_id
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'detail': 'Успешная отписка'}, status=status.HTTP_204_NO_CONTENT
        )
