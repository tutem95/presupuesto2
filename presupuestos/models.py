from decimal import Decimal

from django.db import models

from general.models import Company, CotizacionDolar, Obra, TipoDolar
from recursos.models import Lote, Tarea


class Presupuesto(models.Model):
    """
    Presupuesto armado: obra, fecha, instancia.
    Usa un lote para las tareas y precios, y tipo_dolar/fecha_dolar para USD.
    """
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="presupuestos",
    )
    fecha = models.DateField()
    instancia = models.CharField(max_length=80)
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name="presupuestos",
    )
    tipo_dolar = models.ForeignKey(
        TipoDolar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presupuestos",
    )
    fecha_dolar = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="presupuestos",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["obra__nombre", "-fecha", "instancia"]
        unique_together = ("company", "obra", "instancia")

    def __str__(self):
        return f"{self.obra.nombre} - {self.instancia} ({self.fecha})"

    def get_cotizacion_usd(self):
        """Cotización ARS/USD para este presupuesto."""
        if not self.tipo_dolar_id or not self.fecha_dolar:
            return None
        try:
            c = CotizacionDolar.objects.get(
                company=self.company,
                fecha=self.fecha_dolar,
                tipo=self.tipo_dolar,
            )
            return c.valor
        except CotizacionDolar.DoesNotExist:
            return None

    def total_usd(self):
        """Total del presupuesto en USD."""
        total = Decimal("0")
        for item in self.items.all():
            t = item.total_general_usd()
            if t is None:
                return None
            total += t
        return total


class PresupuestoItem(models.Model):
    """Item del presupuesto: tarea con cantidad."""
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name="items",
    )
    tarea = models.ForeignKey(
        Tarea,
        on_delete=models.CASCADE,
        related_name="presupuesto_items",
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "Item de Presupuesto"
        verbose_name_plural = "Items de Presupuesto"
        unique_together = ("presupuesto", "tarea")

    def __str__(self):
        return f"{self.presupuesto} - {self.tarea.nombre} x {self.cantidad}"

    def total_materiales_mezcla(self):
        return self.cantidad * self.tarea.costo_materiales_mezcla()

    def total_mo_subcontratos(self):
        return self.cantidad * self.tarea.costo_mo_subcontratos()

    def total_general(self):
        return self.total_materiales_mezcla() + self.total_mo_subcontratos()

    def total_materiales_mezcla_usd(self):
        cotiz = self.presupuesto.get_cotizacion_usd()
        return self.tarea.costo_materiales_mezcla_usd_usando_cotizacion(cotiz, self.cantidad)

    def total_mo_subcontratos_usd(self):
        cotiz = self.presupuesto.get_cotizacion_usd()
        return self.tarea.costo_mo_subcontratos_usd_usando_cotizacion(cotiz, self.cantidad)

    def total_general_usd(self):
        mat = self.total_materiales_mezcla_usd()
        mo = self.total_mo_subcontratos_usd()
        if mat is None or mo is None:
            return None
        return mat + mo
