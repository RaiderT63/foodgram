from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
]
