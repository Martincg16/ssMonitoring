from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Proyecto
from .serializers import ProyectoSerializer


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Solar Projects (Proyectos)
    Provides a web interface to view, create, update, and delete solar projects
    """
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # Add ordering to show most recent projects first
    ordering = ['-fecha_entrada_en_operacion']
    
    # Add search functionality
    search_fields = ['dealname', 'id_ciudad__nombre_ciudad']
    
    # Add filtering capabilities
    filterset_fields = ['marca_inversor', 'id_ciudad', 'restriccion_de_autoconsumo'] 