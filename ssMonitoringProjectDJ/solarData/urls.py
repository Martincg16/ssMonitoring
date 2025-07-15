from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ProyectoViewSet

# Create a router and register the ProyectoViewSet
router = DefaultRouter()
router.register(r'proyectos', ProyectoViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('api/', include(router.urls)),
] 