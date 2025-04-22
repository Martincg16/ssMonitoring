from .serializers import ProyectoSerializer, GeneracionEnergiaDiariaSerializer, InversorSerializer, GeneracionInversorDiariaSerializer, MPPTSerializer, GeneracionMPPTDiariaSerializer
from .models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, MPPT, GeneracionMPPTDiaria

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView

class ListProyectos(ListAPIView, CreateAPIView):
    allowew_methods = ['GET', 'POST']
    serializer_class = ProyectoSerializer
    queryset = Proyecto.objects.all()

class DetailProyecto(RetrieveUpdateDestroyAPIView):
    serializer_class = ProyectoSerializer
    queryset = Proyecto.objects.all()
