from django.db import models

# Create your models here.

class Proyecto(models.Model):
    dealname = models.CharField(max_length=255, verbose_name= 'nombre del proyecto')
    ciudad = models.CharField(max_length=100, verbose_name= 'ciudad')
    departamento = models.CharField(max_length=100, verbose_name= 'departamento')
    energia_prometida_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía prometida en el mes')
    energia_minima_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía mínima prometida en el mes')
    fecha_entrada_en_operacion = models.DateField(verbose_name= 'fecha de entrada en operación')
    restriccion_de_autoconsumo = models.BooleanField(default=False, verbose_name= 'tiene restricción de autoconsumo')

    def __str__(self):
        return self.dealname

    class Meta:
        verbose_name = 'Proyecto'

class GeneracionEnergiaDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    energia_generada_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía generada en el día')
    fecha_generacion_dia = models.DateField(verbose_name= 'fecha de generación')

    def __str__(self):
        return f'p{self.id_proyecto}: {self.energia_generada_dia}'
    
class Inversor(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    serial_inversor = models.CharField(max_length=100, verbose_name= 'serial del inversor', default="")

class GeneracionInversorDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    energia_generada_inversor_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía por inversor generada en el día')
    fecha_generacion_inversor_dia = models.DateField(verbose_name= 'fecha de generación por inversor')

    def __str__(self):
        return f'p{self.id_proyecto} - i{self.id_inversor}: {self.energia_generada_inversor_dia}'
    
class MPPT(models.Model):

    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    serial_mppt = models.CharField(max_length=100, verbose_name= 'serial del mppt', default="")

class GeneracionMPPTDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    id_mppt = models.ForeignKey(MPPT, on_delete=models.CASCADE)
    energia_generada_mppt_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía por mppt generada en el día')
    fecha_generacion_mppt_dia = models.DateField(verbose_name= 'fecha de generación por mppt')

    def __str__(self):
        return f'p{self.id_proyecto} - m{self.id_mppt}: {self.energia_generada_mppt_dia}'
