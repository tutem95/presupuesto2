from decimal import Decimal

from django.db import models

from general.models import CategoriaMaterial, Proveedor, Subrubro, TipoMaterial, Unidad


class Material(models.Model):
    MONEDA_CHOICES = [
        ("ARS", "Pesos Argentinos (ARS)"),
        ("USD", "Dólares Estadounidenses (USD)"),
    ]

    nombre = models.CharField(max_length=200, unique=True)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materiales",
    )
    tipo = models.ForeignKey(
        TipoMaterial, on_delete=models.PROTECT, related_name="materiales"
    )
    categoria = models.ForeignKey(
        CategoriaMaterial, on_delete=models.PROTECT, related_name="materiales"
    )
    unidad_de_venta = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="materiales_vendidos"
    )
    cantidad_por_unidad_venta = models.DecimalField(
        max_digits=10, decimal_places=4, default=1
    )
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default="ARS")

    def precio_por_unidad_analisis(self):
        """
        Precio analítico: precio de la unidad de venta dividido por la cantidad que contiene.
        """
        if (
            self.cantidad_por_unidad_venta is not None
            and self.cantidad_por_unidad_venta != 0
        ):
            return self.precio_unidad_venta / self.cantidad_por_unidad_venta
        return Decimal("0")

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @classmethod
    def actualizar_precios_por_porcentaje(cls, queryset, porcentaje):
        if not isinstance(porcentaje, Decimal):  # Asegúrate de que el porcentaje sea Decimal
            porcentaje = Decimal(str(porcentaje))

        factor = Decimal("1") + (porcentaje / Decimal("100"))

        # Usar F() expressions para evitar race conditions y hacer la actualización en una sola consulta SQL
        from django.db.models import F

        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)

        # Opcional: Podrías retornar el número de elementos actualizados
        return queryset.count()

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


class HojaPrecios(models.Model):
    """
    Representa una "hoja" de precios, similar a una pestaña de Excel.
    """

    nombre = models.CharField(max_length=100, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    origen = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copias",
        help_text="Hoja desde la que se creó esta copia, si aplica.",
    )

    class Meta:
        verbose_name = "Hoja de Precios"
        verbose_name_plural = "Hojas de Precios"
        ordering = ["-creado_en"]

    def __str__(self):
        return self.nombre


class HojaPrecioMaterial(models.Model):
    """
    Snapshot de precios de un material en una hoja dada.
    Permite consultar precios históricos sin afectar al Material actual.
    """

    hoja = models.ForeignKey(
        HojaPrecios, on_delete=models.CASCADE, related_name="detalles"
    )
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="hojas_precios"
    )
    cantidad_por_unidad_venta = models.DecimalField(max_digits=10, decimal_places=4)
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(
        max_length=3, choices=Material.MONEDA_CHOICES, default="ARS"
    )

    class Meta:
        verbose_name = "Precio de Material en Hoja"
        verbose_name_plural = "Precios de Material en Hoja"
        ordering = ["material__nombre"]

    def __str__(self):
        return f"{self.material.nombre} @ {self.hoja.nombre}"

    def precio_por_unidad_analisis(self):
        if (
            self.cantidad_por_unidad_venta is not None
            and self.cantidad_por_unidad_venta != 0
        ):
            return self.precio_unidad_venta / self.cantidad_por_unidad_venta
        return Decimal("0")