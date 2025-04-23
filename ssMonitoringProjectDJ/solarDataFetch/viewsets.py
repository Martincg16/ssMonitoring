from rest_framework import viewsets

from .serializers import ProyectoSerializer
from .models import Proyecto

class ProyectoViewSet(viewsets.ModelViewSet):
    serializer_class = ProyectoSerializer
    queryset = Proyecto.objects.all()
