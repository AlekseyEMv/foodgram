from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from foodgram_backend.messages import Warnings as msg

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
                    {'detail': msg.RELATIONSHIP_NAME_ERROR},
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
                    {'detail': msg.OBJECT_NOT_FOUND},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except recipe_class.DoesNotExist:
            return Response(
                {'detail': msg.RECIPE_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'detail': msg.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValidationError as e:
            return Response(
                e.detail, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {'detail': msg.REQUEST_PROCESSING_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def handle_request(
        self, request, response_serializator_class, instance=None
    ):
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

        response_serializer = response_serializator_class(
            recipe, context={'request': request}
        )

        status_code = (
            status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        )
        return Response(response_serializer.data, status=status_code)
