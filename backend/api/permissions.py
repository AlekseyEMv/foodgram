from rest_framework.permissions import SAFE_METHODS, BasePermission


class BaseAuthenticatedActivePermission(BasePermission):
    """
    Базовое разрешение, требующее аутентификации и активности пользователя.

    Предоставляет общие методы для проверки:
    - Аутентификации пользователя
    - Активности пользователя
    """
    def is_user_valid(self, request):
        """
        Проверяет, что пользователь аутентифицирован и активен.

        Параметры:
        - request: объект запроса

        Возвращает:
        - True если пользователь валиден
        - False в противном случае
        """
        if request.user.is_superuser:
            return True
        return (
            request.user.is_authenticated
            and request.user.is_active
        )

    def is_safe_method(self, request):
        """
        Проверяет, является ли метод безопасным (GET, HEAD, OPTIONS).

        Параметры:
        - request: объект запроса

        Возвращает:
        - True если метод безопасный
        - False в противном случае
        """
        return request.method in SAFE_METHODS


class IsAuthenticatedAndActive(BaseAuthenticatedActivePermission):
    """
    Разрешение, требующее аутентификации и активности пользователя.

    Позволяет доступ только аутентифицированным и активным пользователям.
    """

    def has_permission(self, request, view):
        return self.is_user_valid(request)


class IsAuthenticatedAndActiveOrReadOnly(BaseAuthenticatedActivePermission):
    """
    Разрешение на чтение для всех и запись только для аутентифицированных
    и активных пользователей.

    Предоставляет:
    - Полный доступ для аутентифицированных активных пользователей
    - Только чтение для остальных
    """

    def has_permission(self, request, view):
        return (
            self.is_safe_method(request)
            or self.is_user_valid(request)
        )


class IsAuthenticatedAndActiveAndAuthorOrCreateOrReadOnly(
    BaseAuthenticatedActivePermission
):
    """
    Разрешение для операций с объектами, требующее:
    - Аутентификации и активности для создания
    - Права владельца для изменения/удаления
    - Чтения для всех
    """

    def has_permission(self, request, view):
        if self.is_safe_method(request):
            return True

        if request.method == 'POST':
            return self.is_user_valid(request)

        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if self.is_safe_method(request):
            return True

        return (
            self.is_user_valid(request)
            and obj.author == request.user
        )
