from django.contrib import admin

from solarData.models import Departamento, Ciudad, MarcasInversores, Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('dealname', 'get_ciudad', 'get_departamento', 'energia_prometida_mes', 'energia_minima_mes', 'fecha_entrada_en_operacion', 'restriccion_de_autoconsumo')
    search_fields = ('dealname', 'id_ciudad__nombre_ciudad', 'id_ciudad__id_departamento__nombre_departamento')

    def get_ciudad(self, obj):
        return obj.id_ciudad.nombre_ciudad if obj.id_ciudad else 'N/A'
    get_ciudad.short_description = 'Ciudad'

    def get_departamento(self, obj):
        return obj.id_ciudad.id_departamento.nombre_departamento if obj.id_ciudad else 'N/A'
    get_departamento.short_description = 'Departamento'

@admin.register(GeneracionEnergiaDiaria)
class GeneracionEnergiaDiariaAdmin(admin.ModelAdmin):
    list_display = ('id_proyecto', 'energia_generada_dia', 'fecha_generacion_dia')
    list_filter = ('fecha_generacion_dia',)
    search_fields = ('id_proyecto__dealname',)

@admin.register(Inversor)
class InversorAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_proyecto')
    search_fields = ('id_proyecto__dealname',)

@admin.register(GeneracionInversorDiaria)
class GeneracionInversorDiariaAdmin(admin.ModelAdmin):
    list_display = ('id_proyecto', 'id_inversor', 'energia_generada_inversor_dia', 'fecha_generacion_inversor_dia')
    list_filter = ('fecha_generacion_inversor_dia',)
    search_fields = ('id_proyecto__dealname',)

@admin.register(Granular)
class GranularAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_proyecto', 'id_inversor', 'serial_granular', 'tipo_granular')
    search_fields = ('id_proyecto__dealname',)

@admin.register(GeneracionGranularDiaria)
class GeneracionGranularDiariaAdmin(admin.ModelAdmin):
    list_display = ('id_proyecto', 'id_inversor', 'id_granular', 'energia_generada_granular_dia', 'fecha_generacion_granular_dia')
    list_filter = ('fecha_generacion_granular_dia',)
    search_fields = ('id_proyecto__dealname',)

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre_departamento',)
    search_fields = ('nombre_departamento',)

@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre_ciudad', 'id_departamento')
    list_filter = ('id_departamento',)
    search_fields = ('nombre_ciudad', 'id_departamento__nombre_departamento')

@admin.register(MarcasInversores)
class MarcasInversoresAdmin(admin.ModelAdmin):
    list_display = ('marca', 'informacion_granular')
    list_filter = ('informacion_granular',)
    search_fields = ('marca',)
