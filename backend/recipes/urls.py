from django.urls import path
from api.views import RecipeViewSet


urlpatterns = [
    path(
        '<int:pk>/get-link/',
        RecipeViewSet.as_view({'get': 'get_short_link'}),
        name='recipe-short-link'
    ),
]
