from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticated
)


class IsRecipeAuthorOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsProfileOwnerOrReadOnly(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user
