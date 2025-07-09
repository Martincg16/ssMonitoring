from rest_framework import serializers
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria

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

class GranularSerializer(serializers.ModelSerializer):
    class Meta:
        model = Granular
        fields = '__all__'

class GeneracionGranularDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneracionGranularDiaria
        fields = '__all__'
