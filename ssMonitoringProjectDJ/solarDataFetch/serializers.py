from rest_framework import serializers
from .models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, MPPT, GeneracionMPPTDiaria

class ProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proyecto
        fields = '__all__'

class GeneracionEnergiaDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneracionEnergiaDiaria
        fields = '__all__'

class InversorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inversor
        fields = '__all__'

class GeneracionInversorDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneracionInversorDiaria
        fields = '__all__'

class MPPTSerializer(serializers.ModelSerializer):
    class Meta:
        model = MPPT
        fields = '__all__'

class GeneracionMPPTDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneracionMPPTDiaria
        fields = '__all__'
