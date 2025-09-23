from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedAndActive(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_active
        )


class IsAuthenticatedAndActiveOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_active


class IsAuthenticatedAndActiveAndAuthorOrCreateOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Для безопасных методов (GET, HEAD, OPTIONS) разрешаем всем
        if request.method in SAFE_METHODS:
            return True
        
        # Для POST проверяем только авторизацию
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.is_active
        
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Для безопасных методов разрешаем доступ
        if request.method in SAFE_METHODS:
            return True
        
        # Для остальных методов проверяем права
        return (
            request.user.is_authenticated
            and request.user.is_active
            and obj.author == request.user
        )

        
        
class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsAuthenticatedAndActiveAndOwner(IsAuthenticatedAndActive):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.owner == request.user
        )
