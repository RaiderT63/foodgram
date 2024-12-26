from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import RecipeViewSet

router = DefaultRouter()
router.register('', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path(
        '<int:pk>/get-link/',
        RecipeViewSet.as_view({'get': 'get_short_link'}),
        name='recipe-short-link'
    ),
]
