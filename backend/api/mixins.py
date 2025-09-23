from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from foodgram_backend.messages import Warnings


User = get_user_model()


class RecipeActionMixin:
    """
    Mixin для обработки действий с рецептами.

    Предоставляет общую логику для добавление/удаление рецепта в избранное или
    корзину с отношениями между пользователем и рецептом.
    """
    def _handle_action(
        self,
        recipe_class,
        request,
        pk,
        relation_name,
        serializer_class,
        exists_message
    ):
        """
        Основная логика обработки действий с рецептом.

        Параметры:
        - recipe_class: Модель рецепта, с которой работаем
        - request: HTTP-запрос от клиента
        - pk: Первичный ключ рецепта
        - relation_name: Название отношения между рецептом и пользователем
        - serializer_class: Сериализатор для валидации и сохранения данных
        - exists_message: Сообщение об ошибке при попытке добавить существующий
        объект

        Возвращает:
        - Response с соответствующим статусом и данными
        """
        try:
            recipe = recipe_class.objects.get(id=pk)

            # Проверяем существование указанного отношения
            if not hasattr(recipe, relation_name):
                return Response(
                    {'detail': Warnings.RELATIONSHIP_NAME_ERROR},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            user = request.user
            relation = getattr(recipe, relation_name).filter(user=user)

            # Обработка POST-запроса (добавление)
            if request.method == 'POST':

                if relation.exists():
                    return Response(
                        {'detail': exists_message},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                serializer = serializer_class(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            # Обработка DELETE-запроса (удаление)
            if request.method == 'DELETE':
                if relation.exists():
                    relation.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(
                    {'detail': Warnings.OBJECT_NOT_FOUND},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except recipe_class.DoesNotExist:
            return Response(
                {'detail': Warnings.RECIPE_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'detail': Warnings.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValidationError as e:
            return Response(
                e.detail, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {'detail': Warnings.REQUEST_PROCESSING_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def handle_request(self, request, serializator_class, instance=None):
        """
        Основная функция обработки запросов для создания и обновления рецептов

        Метод отвечает за валидацию, сохранение и сериализацию данных рецепта.
        Поддерживает как создание новых записей, так и обновление существующих.

        Параметры:
            request: входящий HTTP-запрос с данными
            serializator_class: класс сериализатора для обработки данных
            instance: существующий экземпляр рецепта для обновления
                Если передан, происходит обновление, иначе - создание нового

        Процесс обработки:
            1. Проверка разрешений для запроса
            2. Если экземпляр передан - проверка разрешений на объект
            3. Создание сериализатора с данными запроса
            4. Валидация данных
            5. Сохранение рецепта
            6. Обновление данных из базы (если это обновление)
            7. Сериализация результата
            8. Возврат ответа с соответствующим статусом

        Возвращает:
            Response: объект ответа с сериализованными данными и HTTP-статусом
                HTTP_201_CREATED при создании нового рецепта
                HTTP_200_OK при обновлении существующего рецепта
        """
        self.check_permissions(request)

        if instance:
            self.check_object_permissions(request, instance)
            serializer = self.get_serializer(instance, data=request.data)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        if instance:
            recipe.refresh_from_db()

        response_serializer = serializator_class(
            recipe, context={'request': request}
        )

        status_code = (
            status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        )
        return Response(response_serializer.data, status=status_code)



class SubscriptionValidationMixin:
    def validate(self, attrs):
        # Получаем author из validated_data
        author = attrs.get('author')
        if not author:
            raise ValidationError('Автор не указан.')
            
        # Проверяем контекст запроса
        request = self.context.get('request')
        if not request:
            raise ValidationError('Контекст запроса отсутствует.')
            
        # Проверяем авторизацию текущего пользователя
        current_user = request.user
        if not current_user.is_authenticated:
            raise ValidationError('Авторизация требуется для подписки.')
            
        # Проверяем запрещенные условия
        if current_user == author:
            raise ValidationError('Операция подписки на собственный аккаунт не допускается.')
            
        if not author.is_active:
            raise ValidationError('Невозможно подписаться на неактивного пользователя.')
            
        return attrs



# class SubscriptionValidationMixin:
#     def _validate_context(self):
#         request = self.context.get('request')
#         if not request:
#             raise ValidationError('Контекст запроса отсутствует.')

#         view = self.context.get('view')
#         if not view:
#             raise ValidationError('Контекст view отсутствует.')

#     def _validate_user(self):
#         request = self.context.get('request')
#         if not request:
#             raise ValidationError('Запрос не найден в контексте')
            
#         current_user = request.user
#         if not current_user.is_authenticated:
#             raise ValidationError('Авторизация требуется для подписки.')

#     def _validate_author(self):
#         view = self.context.get('view')
#         author_id = view.kwargs.get('user_id')  # используем user_id вместо pk
#         if author_id is None:
#             raise ValidationError('ID пользователя не указан.')

#         try:
#             target_user = User.objects.get(id=author_id)
#         except User.DoesNotExist:
#             raise ValidationError('Пользователь не найден.')

#         current_user = self.context.get('request').user
#         if current_user == target_user:
#             raise ValidationError('Операция подписки на собственный аккаунт не допускается.')

#         if not target_user.is_active:
#             raise ValidationError('Невозможно подписаться на неактивного пользователя.')

#     def _get_author(self):
#         view = self.context.get('view')
#         author_id = view.kwargs.get('pk')
#         if author_id is None:
#             raise ValidationError('ID пользователя не указан.')

#         try:
#             return User.objects.get(id=author_id)
#         except User.DoesNotExist:
#             raise ValidationError('Пользователь не найден.')
