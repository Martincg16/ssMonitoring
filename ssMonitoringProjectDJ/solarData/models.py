from django.db import models

class Departamento(models.Model):
    nombre_departamento = models.CharField(max_length=100, verbose_name='nombre del departamento', unique=True)

    def __str__(self):
        return self.nombre_departamento

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'

class Ciudad(models.Model):
    nombre_ciudad = models.CharField(max_length=100, verbose_name='nombre de la ciudad')
    id_departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, verbose_name='departamento')

    def __str__(self):
        return f'{self.nombre_ciudad} - {self.id_departamento.nombre_departamento}'

    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        unique_together = ('nombre_ciudad', 'id_departamento')

class MarcasInversores(models.Model):
    marca = models.CharField(max_length=100, verbose_name= 'marca de inversor', null=True, blank=True)
    informacion_granular = models.BooleanField(default=True, verbose_name= 'tiene información de granular')

    def __str__(self):
        return self.marca

    class Meta:
        verbose_name = 'Marca de Inversor'

class Proyecto(models.Model):
    dealname = models.CharField(max_length=255, verbose_name= 'nombre del proyecto')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, verbose_name= 'ciudad', default=1125)
    energia_prometida_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía prometida en el mes', null=True, blank=True)
    energia_minima_mes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía mínima prometida en el mes', null=True, blank=True)
    fecha_entrada_en_operacion = models.DateField(verbose_name= 'fecha de entrada en operación')
    restriccion_de_autoconsumo = models.BooleanField(default=False, verbose_name= 'tiene restricción de autoconsumo')
    identificador_planta = models.CharField(max_length=100, verbose_name= 'identificador de marca', null=True, blank=True)
    marca_inversor = models.ForeignKey(MarcasInversores, on_delete=models.CASCADE, verbose_name= 'marca de inversor', null=True, blank=True)
    capacidad_instalada_ac = models.DecimalField(max_digits=10, decimal_places=3, verbose_name= 'capacidad instalada AC', null=True, blank=True)
    capacidad_instalada_dc = models.DecimalField(max_digits=10, decimal_places=3, verbose_name= 'capacidad instalada DC', null=True, blank=True)

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
        return f'p:{self.id_proyecto} - {self.fecha_generacion_dia} - {self.energia_generada_dia}'

class Inversor(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    identificador_inversor = models.CharField(max_length=100, verbose_name= 'serial del inversor', default="")
    huawei_devTypeId = models.CharField(max_length=5, verbose_name= 'huawei devTypeId', null=True, blank=True)
    capacidad_inversor = models.DecimalField(max_digits=5, decimal_places=2, verbose_name= 'capacidad del inversor (kW)', null=True, blank=True)

    def __str__(self):
        return f'{self.identificador_inversor} - p:{self.id_proyecto}'

class GeneracionInversorDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    energia_generada_inversor_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía por inversor generada en el día')
    fecha_generacion_inversor_dia = models.DateField(verbose_name= 'fecha de generación por inversor')

    class Meta:
        unique_together = ('id_proyecto', 'id_inversor', 'fecha_generacion_inversor_dia')

    def __str__(self):
        return f'p:{self.id_proyecto} - i:{self.id_inversor} - {self.energia_generada_inversor_dia}'

class Granular(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    serial_granular = models.CharField(max_length=100, verbose_name= 'serial del granular', default="")
    tipo_granular = models.CharField(max_length=100, verbose_name= 'tipo de granular', default="")

    class Meta:
        unique_together = ('id_proyecto', 'id_inversor', 'serial_granular')

    def __str__(self):
        return f'p:{self.id_proyecto} - i:{self.id_inversor} - g:{self.serial_granular}'

class GeneracionGranularDiaria(models.Model):
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, verbose_name= 'nombre del proyecto')
    id_inversor = models.ForeignKey(Inversor, on_delete=models.CASCADE)
    id_granular = models.ForeignKey(Granular, on_delete=models.CASCADE, default="")
    energia_generada_granular_dia = models.DecimalField(max_digits=10, decimal_places=2, verbose_name= 'energía por mppt generada en el día')
    fecha_generacion_granular_dia = models.DateField(verbose_name= 'fecha de generación por mppt')

    def __str__(self):
        return f'p:{self.id_proyecto} - i:{self.id_inversor} - g:{self.id_granular} - {self.energia_generada_granular_dia}'
