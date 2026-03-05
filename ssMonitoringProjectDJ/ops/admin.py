from django.contrib import admin

from .models import TipoHito, HitoProyecto


@admin.register(TipoHito)
class TipoHitoAdmin(admin.ModelAdmin):
    list_display = ('secuencia', 'nombre', 'fase', 'tiene_fecha_reportada')
    list_filter = ('fase',)
    ordering = ('secuencia',)


@admin.register(HitoProyecto)
class HitoProyectoAdmin(admin.ModelAdmin):
    list_display = ('pid', 'id_tipo_hito', 'fecha_programada', 'fecha_real', 'fecha_reportada')
    list_filter = ('id_tipo_hito__fase', 'id_tipo_hito')
    search_fields = ('pid__dealname',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
