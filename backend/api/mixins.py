from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class SubscriptionValidationMixin:
    def _validate_context(self):
        request = self.context.get('request')
        if not request:
            raise ValidationError('Контекст запроса отсутствует.')

        view = self.context.get('view')
        if not view:
            raise ValidationError('Контекст view отсутствует.')

    def _validate_user(self):
        request = self.context.get('request')
        current_user = request.user
        if not current_user.is_authenticated:
            raise ValidationError('Авторизация требуется для подписки.')

    def _validate_author(self):
        view = self.context.get('view')
        author_id = view.kwargs.get('pk')
        if author_id is None:
            raise ValidationError('ID пользователя не указан.')

        try:
            target_user = User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise ValidationError('Пользователь не найден.')

        current_user = self.context['request'].user
        if current_user == target_user:
            raise ValidationError(
                'Операция подписки на собственный аккаунт не допускается.'
            )

        if not target_user.is_active:
            raise ValidationError(
                'Невозможно подписаться на неактивного пользователя.'
            )

    def _get_author(self):
        view = self.context.get('view')
        author_id = view.kwargs.get('pk')
        if author_id is None:
            raise ValidationError('ID пользователя не указан.')

        try:
            return User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise ValidationError('Пользователь не найден.')
