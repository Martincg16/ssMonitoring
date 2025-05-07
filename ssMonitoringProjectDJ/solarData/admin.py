from django.contrib import admin

from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('dealname', 'ciudad', 'departamento', 'energia_prometida_mes', 'energia_minima_mes', 'fecha_entrada_en_operacion', 'restriccion_de_autoconsumo')
    search_fields = ('dealname', 'ciudad', 'departamento')

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
