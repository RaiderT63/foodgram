from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticated
)


class IsRecipeAuthorOrReadOnly(BasePermission):
    """
    Разрешение на чтение для всех,
    но изменение и удаление только для автора рецепта.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsProfileOwnerOrReadOnly(IsAuthenticated):
    """
    Разрешение на чтение для всех аутентифицированных пользователей,
    изменение и удаление только для владельца профиля.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user
