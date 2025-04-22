from django.contrib import admin
from .models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, MPPT, GeneracionMPPTDiaria

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

@admin.register(MPPT)
class MPPTAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_proyecto', 'id_inversor')
    search_fields = ('id_proyecto__dealname',)

@admin.register(GeneracionMPPTDiaria)
class GeneracionMPPTDiariaAdmin(admin.ModelAdmin):
    list_display = ('id_proyecto', 'id_inversor', 'id_mppt', 'energia_generada_mppt_dia', 'fecha_generacion_mppt_dia')
    list_filter = ('fecha_generacion_mppt_dia',)
    search_fields = ('id_proyecto__dealname',)
