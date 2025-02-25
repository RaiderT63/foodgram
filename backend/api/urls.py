from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'
router = DefaultRouter()
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
