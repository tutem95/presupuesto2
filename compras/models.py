from django.db import models

from general.models import Company, Obra, Proveedor, Rubro, Subrubro


class Semana(models.Model):
    """
    Semana de pagos. La fecha identifica la semana (ej: lunes de esa semana).
    """
    fecha = models.DateField(help_text="Fecha de la semana (ej: lunes)")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="semanas_compras",
    )

    class Meta:
        verbose_name = "Semana"
        verbose_name_plural = "Semanas"
        ordering = ["-fecha"]
        unique_together = ("company", "fecha")

    def __str__(self):
        return self.fecha.strftime("%d/%m/%Y")

    def year(self):
        return self.fecha.year

    def month(self):
        return self.fecha.month


class Compra(models.Model):
    """
    Pago/compra: línea con obra, rubro, subrubro, item, proveedor, montos, etc.
    """
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
        ("parcial", "Parcial"),
        ("cancelado", "Cancelado"),
    ]

    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("cheque", "Cheque"),
        ("tarjeta", "Tarjeta"),
        ("otro", "Otro"),
    ]

    semana = models.ForeignKey(
        Semana,
        on_delete=models.CASCADE,
        related_name="compras",
    )
    obra = models.ForeignKey(
        Obra,
        on_delete=models.PROTECT,
        related_name="compras",
    )
    rubro = models.ForeignKey(
        Rubro,
        on_delete=models.PROTECT,
        related_name="compras",
    )
    subrubro = models.ForeignKey(
        Subrubro,
        on_delete=models.PROTECT,
        related_name="compras",
    )
    item = models.CharField(max_length=255, help_text="Descripción del ítem")
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="compras",
    )
    forma_pago = models.CharField(
        max_length=20,
        choices=FORMA_PAGO_CHOICES,
        default="transferencia",
    )
    monto_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    # Detalle (en fila expandida)
    numero_ppto_fc = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="Nº de PPTO/FC",
    )
    fecha_factura = models.DateField(null=True, blank=True)
    monto_sin_iva = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    iva_21 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    iva_105 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    perc_iibb = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="PERC. IIBB",
    )
    monto_a_pagar = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto a pagar $",
    )
    observaciones = models.TextField(blank=True)
    porcentaje_pago = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="% de pago",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente",
    )
    es_subcontrato = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["obra__nombre", "rubro__nombre", "subrubro__nombre"]

    def __str__(self):
        return f"{self.obra.nombre} - {self.item} ({self.proveedor.nombre})"
