from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    CategoryViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

router = DefaultRouter()
router.register(
    r'categories',
    CategoryViewSet,
    basename='category'
)
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredient'
)
router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipe'
)

urlpatterns = [
    path('', include(router.urls)),
]
