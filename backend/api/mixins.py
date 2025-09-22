from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


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
