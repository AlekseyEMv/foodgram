from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_superuser
            or request.method in SAFE_METHODS
        )


class IsSuperUserOrAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and (
                request.method in SAFE_METHODS
                or request.user.is_superuser
                or obj.author == request.user
            )
        )


class AllowGET(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'GET'


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


class IsAuthenticatedAndActiveAndOwner(IsAuthenticatedAndActive):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.owner == request.user
        )
