from django.db import models
from general.models import Unidad, Subrubro, Proveedor, TipoMaterial, CategoriaMaterial


class Material(models.Model):
    MONEDA_CHOICES = [
        ('ARS', 'Pesos Argentinos (ARS)'),
        ('USD', 'Dólares Estadounidenses (USD)'),
    ]

    nombre = models.CharField(max_length=200, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiales')
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.PROTECT, related_name='materiales')
    categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.PROTECT, related_name='materiales')
    unidad_de_venta = models.ForeignKey(Unidad, on_delete=models.PROTECT, related_name='materiales_vendidos')
    cantidad_por_unidad_venta = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='ARS')

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class ManoDeObra(models.Model):
    EQUIPO_CHOICES = [
        ('Naty', 'Equipo Naty'),
        ('Diego', 'Equipo Diego'),
    ]

    descripcion_puesto = models.CharField(max_length=200)
    equipo = models.CharField(max_length=50, choices=EQUIPO_CHOICES)
    unidad_de_analisis = models.ForeignKey(Unidad, on_delete=models.PROTECT, related_name='mano_de_obra_unidades')
    precio_por_unidad = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "Mano de Obra"
        verbose_name_plural = "Mano de Obra"
        ordering = ['descripcion_puesto']
        unique_together = ('descripcion_puesto', 'equipo') # Un puesto por equipo

    def __str__(self):
        return f"{self.descripcion_puesto} ({self.equipo})"

class Subcontrato(models.Model):
    MONEDA_CHOICES = [
        ('ARS', 'Pesos Argentinos (ARS)'),
        ('USD', 'Dólares Estadounidenses (USD)'),
    ]

    descripcion = models.CharField(max_length=255, unique=True)
    proveedor = models.CharField(max_length=100, blank=True, null=True)
    unidad_de_analisis = models.ForeignKey(Unidad, on_delete=models.PROTECT, related_name='subcontratos_unidades')
    precio_por_unidad = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='ARS')

    class Meta:
        verbose_name = "Subcontrato"
        verbose_name_plural = "Subcontratos"
        ordering = ['descripcion']

    def __str__(self):
        return self.descripcion