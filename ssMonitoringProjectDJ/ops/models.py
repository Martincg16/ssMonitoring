from django.db import models

from solarData.models import Proyecto


class TipoHito(models.Model):
    FASE_CHOICES = [
        (1, 'Fase 1'),
        (2, 'Fase 2'),
        (3, 'Fase 3'),
    ]

    codigo = models.CharField(max_length=100, verbose_name= 'código', unique=True)
    nombre = models.CharField(max_length=200, verbose_name= 'nombre')
    fase = models.IntegerField(choices=FASE_CHOICES, verbose_name= 'fase')
    secuencia = models.IntegerField(verbose_name= 'secuencia')
    tiene_fecha_reportada = models.BooleanField(default=False, verbose_name= 'tiene fecha reportada')

    def __str__(self):
        return f'{self.secuencia}. {self.nombre}'

    class Meta:
        verbose_name = 'Tipo de Hito'
        verbose_name_plural = 'Tipos de Hito'
        ordering = ['secuencia']


class HitoProyecto(models.Model):
    pid = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'proyecto', related_name= 'hitos')
    id_tipo_hito = models.ForeignKey(TipoHito, on_delete=models.CASCADE, verbose_name= 'tipo de hito', related_name= 'hitos')
    fecha_programada = models.DateField(verbose_name= 'fecha programada', null=True, blank=True)
    fecha_real = models.DateField(verbose_name= 'fecha real', null=True, blank=True)
    fecha_reportada = models.DateField(verbose_name= 'fecha reportada', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name= 'fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name= 'fecha de actualización')

    def __str__(self):
        return f'{self.pid} - {self.id_tipo_hito}'

    class Meta:
        verbose_name = 'Hito de Proyecto'
        verbose_name_plural = 'Hitos de Proyecto'
        unique_together = ('pid', 'id_tipo_hito')
        ordering = ['pid', 'id_tipo_hito__secuencia']
