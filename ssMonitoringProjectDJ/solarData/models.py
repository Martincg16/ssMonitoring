from django.db import models

class MarcasInversores(models.Model):
    marca = models.CharField(max_length=100, verbose_name= 'marca de inversor', null=True, blank=True)

    def __str__(self):
        return self.marca

    class Meta:
        verbose_name = 'Marca de Inversor'

class Proyecto(models.Model):
    dealname = models.CharField(max_length=255, verbose_name= 'nombre del proyecto')
    ciudad = models.CharField(max_length=100, verbose_name= 'ciudad')
    departamento = models.CharField(max_length=100, verbose_name= 'departamento')
    energia_prometida_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía prometida en el mes', null=True, blank=True)
    energia_minima_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía mínima prometida en el mes', null=True, blank=True)
    fecha_entrada_en_operacion = models.DateField(verbose_name= 'fecha de entrada en operación')
    restriccion_de_autoconsumo = models.BooleanField(default=False, verbose_name= 'tiene restricción de autoconsumo')
    identificador_planta = models.CharField(max_length=100, verbose_name= 'identificador de marca', null=True, blank=True)
    marca_inversor = models.ForeignKey(MarcasInversores, on_delete=models.CASCADE, verbose_name= 'marca de inversor', null=True, blank=True)

    def __str__(self):
        return self.dealname

    class Meta:
        verbose_name = 'Proyecto'

class GeneracionEnergiaDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    energia_generada_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía generada en el día')
    fecha_generacion_dia = models.DateField(verbose_name= 'fecha de generación')

    class Meta:
        unique_together = ('id_proyecto', 'fecha_generacion_dia')

    def __str__(self):
        return f'p{self.id_proyecto}: {self.energia_generada_dia}'

class Inversor(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    identificador_inversor = models.CharField(max_length=100, verbose_name= 'serial del inversor', default="")
    huawei_devTypeId = models.CharField(max_length=5, verbose_name= 'huawei devTypeId', null=True, blank=True)

class GeneracionInversorDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    energia_generada_inversor_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía por inversor generada en el día')
    fecha_generacion_inversor_dia = models.DateField(verbose_name= 'fecha de generación por inversor')

    class Meta:
        unique_together = ('id_proyecto', 'id_inversor', 'fecha_generacion_inversor_dia')

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
