from rest_framework.permissions import (
    IsAdminUser, IsAuthenticatedOrReadOnly, SAFE_METHODS
)


class IsSuperUser(IsAdminUser):
    """
    Класс разрешений на доступ только суперпользователям (администраторам).

    Метод has_permission проверяет, является ли текущий пользователь
    администратором.

    Возвращает:
    - True, если пользователь является администратором
    - False в противном случае
    """
    def has_permission(self, request, view):
        return request.user.is_admin()


class IsSuperUserOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Класс разрешений, который позволяет:
    - Полный доступ суперпользователям (администраторам)
    - Только чтение (safe methods) для остальных пользователей.

    Метод has_permission проверяет:
    1. Является ли пользователь аутентифицированным И администратором
    2. Или является ли текущий метод запроса безопасным (GET, HEAD, OPTIONS)

    Возвращает:
    - True, если пользователь админ или запрос на чтение
    - False в противном случае
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.is_admin()
            or request.method in SAFE_METHODS
        )


class IsSuperUserOrStafOrAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Класс для детальной проверки прав доступа к объекту.
    Предоставляет полный доступ:
    - суперпользователям
    - модераторам
    - автору объекта
    Всем остальным пользователям доступен только чтение.
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверка разрешения на доступ к конкретному объекту.
        Параметры:
        request (HttpRequest): объект запроса,
        view (APIView): представление, для которого проверяется разрешение,
        obj: объект, к которому требуется доступ.
        Возвращает:
        bool: True, если выполняется хотя бы одно из условий:
            - запрос на чтение
            - пользователь модератор
            - пользователь администратор
            - пользователь является автором объекта.
        """
        return (
            request.method in SAFE_METHODS
            or request.user.is_moderator()
            or request.user.is_admin()
            or request.user == obj.author
        )
