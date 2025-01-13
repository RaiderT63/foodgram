from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
# from django.views.generic import RedirectView

from api.views import RecipeViewSet, short_link_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<int:pk>/', short_link_view, name='short_link'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
