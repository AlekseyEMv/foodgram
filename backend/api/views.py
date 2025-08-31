from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend
# from djoser.views import UserViewSet
from rest_framework import status, viewsets as vs
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import PageNumberPagination
# from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import IngredientSerializer, TagSerializer
from .permissions import IsAuthenticatedAndActive, IsSuperUser
from recipes.models import Ingredient, Tag
from users.models import Follow
from users.serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    SubscribeSerializer,
    SubscriptionsSerializer
)

User = get_user_model()


class IngredientsViewSet(vs.ReadOnlyModelViewSet):
    """
    Представление для работы с ингредиентами.

    Предоставляет доступ только для чтения для получения списка всех
    ингредиентов и для получения конкретного ингридиента по идентификатору.
    Поддерживает поиск по частичному вхождению в начале названия ингредиента.

    Attributes:
        queryset: Набор запросов на получения всех ингредиентов из базы данных.
        serializer_class: Класс сериализатора для преобразования объектов в
            JSON формат.
        filter_backends: Кортеж с бэкендами фильтрации.
        search_fields: Поля для поиска, поддерживает поиск по началу строки.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('i^name',)


class RecipesViewSet(vs.ModelViewSet):
    """
    """


class TagsViewSet(vs.ReadOnlyModelViewSet):
    """
    Представление для работы с тегами.

    Предоставляет доступ только для чтения для получения списка всех
    тегов и для получения конкретного тега по идентификатору.

    Attributes:
        queryset: Набор запросов на получения всех тегов из базы данных.
        serializer_class: Класс сериализатора для преобразования объектов в
            JSON формат.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CustomUsersViewSet(vs.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedAndActive, IsSuperUser)
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter,)
    search_fields = ['username', 'email']

    @action(
        detail=True,
        methods=['get'],
        url_path='me',
        permission_classes=(IsAuthenticatedAndActive,),
    )
    def me(self, request):

        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        serializer_class=AvatarSerializer,
        permission_classes=(IsAuthenticatedAndActive,)
    )
    def avatar(self, request):

        if request.method == 'PUT':
            if request.data:
                serializer = self.get_serializer(
                    request.user,
                    data=request.data,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            self.request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        pagination_class=PageNumberPagination,
    )
    def subscriptions(self, request):

        queryset = User.objects.filter(following__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class SubscribeViewSet(CreateModelMixin,
                       DestroyModelMixin,
                       vs.GenericViewSet):
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
