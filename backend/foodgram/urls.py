from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from api.views import CategoryViewSet, IngredientViewSet

router = DefaultRouter()
router.register('tags', CategoryViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include('users.urls')),
    path('api/recipes/', include('recipes.urls')),
    path('api/', include(router.urls)),
    path('', RedirectView.as_view(url='/api/', permanent=True)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
