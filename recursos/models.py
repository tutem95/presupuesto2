from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from general.models import (
    CategoriaMaterial,
    Company,
    CotizacionDolar,
    Equipo,
    Proveedor,
    RefEquipo,
    Rubro,
    Subrubro,
    TipoDolar,
    TipoMaterial,
    Unidad,
)


class Material(models.Model):
    MONEDA_CHOICES = [
        ("ARS", "Pesos Argentinos (ARS)"),
        ("USD", "Dólares Estadounidenses (USD)"),
    ]

    nombre = models.CharField(max_length=200)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="materiales",
    )
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
        Precio analítico (UA): cantidad por unidad de venta × precio de venta.
        """
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["nombre"]
        unique_together = ("company", "nombre", "proveedor")

    def __str__(self):
        if self.proveedor_id:
            return f"{self.nombre} ({self.proveedor.nombre})"
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
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="mano_de_obra",
    )
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, related_name="mano_de_obra"
    )
    subrubro = models.ForeignKey(
        Subrubro, on_delete=models.PROTECT, related_name="mano_de_obra"
    )
    tarea = models.CharField(max_length=255)
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="mano_de_obra",
    )
    ref_equipo = models.ForeignKey(
        RefEquipo,
        on_delete=models.PROTECT,
        related_name="mano_de_obra",
    )
    cantidad_por_unidad_venta = models.DecimalField(
        max_digits=10, decimal_places=4, default=1
    )
    unidad_de_venta = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="mano_de_obra_unidades"
    )
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.rubro_id
            and self.subrubro_id
            and self.subrubro.rubro_id != self.rubro_id
        ):
            errors["subrubro"] = "El subrubro seleccionado no pertenece al rubro indicado."

        if (
            self.equipo_id
            and self.ref_equipo_id
            and self.ref_equipo.equipo_id != self.equipo_id
        ):
            errors["ref_equipo"] = "La referencia de equipo no pertenece al equipo indicado."

        if self.company_id:
            company_id = self.company_id
            if self.rubro_id and self.rubro.company_id != company_id:
                errors["rubro"] = "El rubro no pertenece a la empresa seleccionada."
            if self.subrubro_id and self.subrubro.company_id != company_id:
                errors["subrubro"] = "El subrubro no pertenece a la empresa seleccionada."
            if self.equipo_id and self.equipo.company_id != company_id:
                errors["equipo"] = "El equipo no pertenece a la empresa seleccionada."
            if self.ref_equipo_id and self.ref_equipo.company_id != company_id:
                errors["ref_equipo"] = (
                    "La referencia de equipo no pertenece a la empresa seleccionada."
                )
            if self.unidad_de_venta_id and self.unidad_de_venta.company_id != company_id:
                errors["unidad_de_venta"] = (
                    "La unidad de venta no pertenece a la empresa seleccionada."
                )

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Mano de Obra"
        verbose_name_plural = "Mano de Obra"
        ordering = ["rubro__nombre", "subrubro__nombre", "tarea"]
        unique_together = ("company", "rubro", "subrubro", "tarea", "equipo", "ref_equipo")

    def __str__(self):
        return f"{self.tarea} ({self.subrubro.nombre} · {self.equipo.nombre} / {self.ref_equipo.nombre})"

    def precio_por_unidad_analisis(self):
        """UA = cantidad por unidad de venta × precio de venta."""
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")

    @classmethod
    def actualizar_precios_por_porcentaje(cls, queryset, porcentaje):
        if not isinstance(porcentaje, Decimal):
            porcentaje = Decimal(str(porcentaje))
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        from django.db.models import F
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
        return queryset.count()

class Subcontrato(models.Model):
    MONEDA_CHOICES = [
        ("ARS", "Pesos Argentinos (ARS)"),
        ("USD", "Dólares Estadounidenses (USD)"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="subcontratos",
    )
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, related_name="subcontratos"
    )
    subrubro = models.ForeignKey(
        Subrubro, on_delete=models.PROTECT, related_name="subcontratos"
    )
    tarea = models.CharField(max_length=255)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcontratos",
    )
    cantidad_por_unidad_venta = models.DecimalField(
        max_digits=10, decimal_places=4, default=1
    )
    unidad_de_venta = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="subcontratos_venta"
    )
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default="ARS")

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.rubro_id
            and self.subrubro_id
            and self.subrubro.rubro_id != self.rubro_id
        ):
            errors["subrubro"] = "El subrubro seleccionado no pertenece al rubro indicado."

        if self.company_id:
            company_id = self.company_id
            if self.rubro_id and self.rubro.company_id != company_id:
                errors["rubro"] = "El rubro no pertenece a la empresa seleccionada."
            if self.subrubro_id and self.subrubro.company_id != company_id:
                errors["subrubro"] = "El subrubro no pertenece a la empresa seleccionada."
            if self.proveedor_id and self.proveedor.company_id != company_id:
                errors["proveedor"] = "El proveedor no pertenece a la empresa seleccionada."
            if self.unidad_de_venta_id and self.unidad_de_venta.company_id != company_id:
                errors["unidad_de_venta"] = (
                    "La unidad de venta no pertenece a la empresa seleccionada."
                )

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Subcontrato"
        verbose_name_plural = "Subcontratos"
        ordering = ["rubro__nombre", "subrubro__nombre", "tarea"]
        unique_together = ("company", "rubro", "subrubro", "tarea")

    def __str__(self):
        return f"{self.tarea} ({self.subrubro.nombre})"

    def precio_por_unidad_analisis(self):
        """UA = cantidad por unidad de venta × precio de venta."""
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")

    @classmethod
    def actualizar_precios_por_porcentaje(cls, queryset, porcentaje):
        if not isinstance(porcentaje, Decimal):
            porcentaje = Decimal(str(porcentaje))
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        from django.db.models import F
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
        return queryset.count()


class HojaPrecios(models.Model):
    """
    Representa una "hoja" de precios, similar a una pestaña de Excel.
    """

    nombre = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hojas_precios",
    )
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
        unique_together = ("company", "nombre")

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
        """UA = cantidad por unidad de venta × precio de venta."""
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")


class Mezcla(models.Model):
    """
    Mezcla de materiales. Vinculada a una hoja de precios de materiales.
    El costo se calcula sumando (cantidad × precio) de cada material.
    """
    nombre = models.CharField(max_length=200)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="mezclas",
    )
    unidad_de_mezcla = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="mezclas"
    )
    hoja = models.ForeignKey(
        HojaPrecios,
        on_delete=models.CASCADE,
        related_name="mezclas",
        null=True,
        blank=True,
        help_text="Hoja de materiales para precios. Si vacío, usa precios actuales.",
    )

    class Meta:
        verbose_name = "Mezcla"
        verbose_name_plural = "Mezclas"
        ordering = ["nombre"]
        unique_together = ("company", "nombre", "hoja")

    def __str__(self):
        hoja_nom = self.hoja.nombre if self.hoja else "Actuales"
        return f"{self.nombre} ({hoja_nom})"

    def precio_por_unidad_mezcla(self):
        """Suma de (cantidad × precio) de cada material en la mezcla."""
        total = Decimal("0")
        for det in self.detalles.select_related("material", "material__unidad_de_venta").all():
            total += det.costo_en_hoja()
        return total


class MezclaMaterial(models.Model):
    """Material que compone una mezcla, con su cantidad."""
    mezcla = models.ForeignKey(
        Mezcla, on_delete=models.CASCADE, related_name="detalles"
    )
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="mezclas"
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=4,
        help_text="Cantidad en unidad de venta del material (ej: bolsas, kg).",
    )

    class Meta:
        verbose_name = "Material en Mezcla"
        verbose_name_plural = "Materiales en Mezcla"
        ordering = ["material__nombre"]
        unique_together = ("mezcla", "material")

    def __str__(self):
        return f"{self.cantidad} {self.material.unidad_de_venta} de {self.material.nombre}"

    def costo_en_hoja(self):
        """Costo de este material en la mezcla según la hoja (o precios actuales)."""
        if self.mezcla.hoja:
            try:
                hp = HojaPrecioMaterial.objects.get(
                    hoja=self.mezcla.hoja, material=self.material
                )
                return self.cantidad * hp.precio_unidad_venta
            except HojaPrecioMaterial.DoesNotExist:
                return Decimal("0")
        return self.cantidad * self.material.precio_unidad_venta

    def precio_unidad_desde_hoja(self):
        """Precio unitario del material desde la hoja o actual."""
        if self.mezcla.hoja:
            try:
                hp = HojaPrecioMaterial.objects.get(
                    hoja=self.mezcla.hoja, material=self.material
                )
                return hp.precio_unidad_venta
            except HojaPrecioMaterial.DoesNotExist:
                return Decimal("0")
        return self.material.precio_unidad_venta


class HojaPreciosSubcontrato(models.Model):
    """Hoja de precios para subcontratos."""
    nombre = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hojas_precios_subcontrato",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    origen = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copias",
    )

    class Meta:
        verbose_name = "Hoja de Precios Subcontrato"
        verbose_name_plural = "Hojas de Precios Subcontrato"
        ordering = ["-creado_en"]
        unique_together = ("company", "nombre")

    def __str__(self):
        return self.nombre


class HojaPrecioSubcontrato(models.Model):
    """Snapshot de precios de un subcontrato en una hoja dada."""
    hoja = models.ForeignKey(
        HojaPreciosSubcontrato,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    subcontrato = models.ForeignKey(
        Subcontrato,
        on_delete=models.PROTECT,
        related_name="hojas_precios",
    )
    cantidad_por_unidad_venta = models.DecimalField(max_digits=10, decimal_places=4)
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(
        max_length=3, choices=Subcontrato.MONEDA_CHOICES, default="ARS"
    )

    class Meta:
        verbose_name = "Precio de Subcontrato en Hoja"
        verbose_name_plural = "Precios de Subcontrato en Hoja"
        ordering = ["subcontrato__rubro__nombre", "subcontrato__subrubro__nombre", "subcontrato__tarea"]

    def __str__(self):
        return f"{self.subcontrato.tarea} @ {self.hoja.nombre}"

    def precio_por_unidad_analisis(self):
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")


class HojaPreciosManoDeObra(models.Model):
    """Hoja de precios para mano de obra."""
    nombre = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hojas_precios_mano_de_obra",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    origen = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copias",
    )

    class Meta:
        verbose_name = "Hoja de Precios Mano de Obra"
        verbose_name_plural = "Hojas de Precios Mano de Obra"
        ordering = ["-creado_en"]
        unique_together = ("company", "nombre")

    def __str__(self):
        return self.nombre


class HojaPrecioManoDeObra(models.Model):
    """Snapshot de precios de mano de obra en una hoja dada."""
    hoja = models.ForeignKey(
        HojaPreciosManoDeObra,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    mano_de_obra = models.ForeignKey(
        ManoDeObra,
        on_delete=models.PROTECT,
        related_name="hojas_precios",
    )
    cantidad_por_unidad_venta = models.DecimalField(max_digits=10, decimal_places=4)
    precio_unidad_venta = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "Precio de Mano de Obra en Hoja"
        verbose_name_plural = "Precios de Mano de Obra en Hoja"
        ordering = [
            "mano_de_obra__rubro__nombre",
            "mano_de_obra__subrubro__nombre",
            "mano_de_obra__tarea",
        ]

    def __str__(self):
        return f"{self.mano_de_obra.tarea} @ {self.hoja.nombre}"

    def precio_por_unidad_analisis(self):
        if (
            self.cantidad_por_unidad_venta is not None
            and self.precio_unidad_venta is not None
        ):
            return self.cantidad_por_unidad_venta * self.precio_unidad_venta
        return Decimal("0")


class Lote(models.Model):
    """
    Lote/versión de precios: agrupa las hojas de materiales, mano de obra
    y subcontratos con la misma fecha. Al crear un lote se copian los precios
    actuales (o de otro lote) a las tres hojas.
    """
    nombre = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="lotes",
    )
    hoja_materiales = models.ForeignKey(
        HojaPrecios,
        on_delete=models.CASCADE,
        related_name="lotes",
    )
    hoja_mano_de_obra = models.ForeignKey(
        HojaPreciosManoDeObra,
        on_delete=models.CASCADE,
        related_name="lotes",
    )
    hoja_subcontratos = models.ForeignKey(
        HojaPreciosSubcontrato,
        on_delete=models.CASCADE,
        related_name="lotes",
    )
    tipo_dolar = models.ForeignKey(
        TipoDolar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lotes",
        help_text="Tipo de dólar para ver precios en USD.",
    )
    fecha_dolar = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de cotización para convertir ARS a USD.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ["-creado_en"]
        unique_together = ("company", "nombre")

    def __str__(self):
        return self.nombre

    def get_cotizacion_usd(self):
        """Cotización ARS/USD para este lote. None si no está configurado."""
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


class Tarea(models.Model):
    """
    Maestro Tareas: tareas de obra definidas por rubro/subrubro.
    Cada tarea pertenece a un lote y está compuesta por recursos.
    """
    nombre = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="tareas",
    )
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, related_name="tareas"
    )
    subrubro = models.ForeignKey(
        Subrubro, on_delete=models.PROTECT, related_name="tareas"
    )
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name="tareas",
    )

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.rubro_id
            and self.subrubro_id
            and self.subrubro.rubro_id != self.rubro_id
        ):
            errors["subrubro"] = "El subrubro seleccionado no pertenece al rubro indicado."

        if self.company_id:
            company_id = self.company_id
            if self.rubro_id and self.rubro.company_id != company_id:
                errors["rubro"] = "El rubro no pertenece a la empresa seleccionada."
            if self.subrubro_id and self.subrubro.company_id != company_id:
                errors["subrubro"] = "El subrubro no pertenece a la empresa seleccionada."
            if self.lote_id and self.lote.company_id != company_id:
                errors["lote"] = "El lote no pertenece a la empresa seleccionada."

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Maestro Tareas"
        ordering = ["rubro__nombre", "subrubro__nombre", "nombre"]
        unique_together = ("company", "lote", "nombre")

    def __str__(self):
        return self.nombre

    def precio_total(self):
        total = Decimal("0")
        for rec in self.recursos.select_related(
            "material", "mano_de_obra", "subcontrato", "mezcla"
        ).all():
            total += rec.costo_total()
        return total

    def precio_total_usd(self):
        """Total en USD (ARS convertidos). None si el lote no tiene cotización."""
        total = Decimal("0")
        for rec in self.recursos.all():
            c = rec.costo_total_usd()
            if c is None:
                return None
            total += c
        return total

    def costo_materiales_mezcla(self):
        """Costo de materiales y mezclas (precio unitario de la tarea)."""
        total = Decimal("0")
        for rec in self.recursos.all():
            if rec.get_tipo() in ("material", "mezcla"):
                total += rec.costo_total()
        return total

    def costo_mo_subcontratos(self):
        """Costo de mano de obra y subcontratos (precio unitario de la tarea)."""
        total = Decimal("0")
        for rec in self.recursos.all():
            if rec.get_tipo() in ("mano_de_obra", "subcontrato"):
                total += rec.costo_total()
        return total

    def costo_materiales_mezcla_usd_usando_cotizacion(self, cotizacion, cantidad=Decimal("1")):
        """Costo materiales/mezcla en USD, usando cotización externa. cantidad multiplica."""
        total_usd = Decimal("0")
        for rec in self.recursos.all():
            if rec.get_tipo() in ("material", "mezcla"):
                c = rec.costo_total_usd_con_cotizacion(cotizacion)
                if c is None:
                    return None
                total_usd += c
        return total_usd * cantidad

    def costo_mo_subcontratos_usd_usando_cotizacion(self, cotizacion, cantidad=Decimal("1")):
        """Costo MO/subcontratos en USD, usando cotización externa. cantidad multiplica."""
        total_usd = Decimal("0")
        for rec in self.recursos.all():
            if rec.get_tipo() in ("mano_de_obra", "subcontrato"):
                c = rec.costo_total_usd_con_cotizacion(cotizacion)
                if c is None:
                    return None
                total_usd += c
        return total_usd * cantidad

    def get_unidad(self):
        """Unidad de medida: del primer recurso que tenga unidad."""
        for rec in self.recursos.select_related(
            "material__unidad_de_venta",
            "mano_de_obra__unidad_de_venta",
            "subcontrato__unidad_de_venta",
            "mezcla__unidad_de_mezcla",
        ):
            if rec.material_id:
                return rec.material.unidad_de_venta.nombre if rec.material.unidad_de_venta_id else None
            if rec.mano_de_obra_id:
                return rec.mano_de_obra.unidad_de_venta.nombre if rec.mano_de_obra.unidad_de_venta_id else None
            if rec.subcontrato_id:
                return rec.subcontrato.unidad_de_venta.nombre if rec.subcontrato.unidad_de_venta_id else None
            if rec.mezcla_id:
                return rec.mezcla.unidad_de_mezcla.nombre if rec.mezcla.unidad_de_mezcla_id else None
        return "-"


class TareaRecurso(models.Model):
    """Recurso que compone una tarea: material, mano de obra, subcontrato o mezcla."""
    tarea = models.ForeignKey(
        Tarea, on_delete=models.CASCADE, related_name="recursos"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="tarea_recursos",
        null=True,
        blank=True,
    )
    mano_de_obra = models.ForeignKey(
        ManoDeObra,
        on_delete=models.PROTECT,
        related_name="tarea_recursos",
        null=True,
        blank=True,
    )
    subcontrato = models.ForeignKey(
        Subcontrato,
        on_delete=models.PROTECT,
        related_name="tarea_recursos",
        null=True,
        blank=True,
    )
    mezcla = models.ForeignKey(
        Mezcla,
        on_delete=models.PROTECT,
        related_name="tarea_recursos",
        null=True,
        blank=True,
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "Recurso en Tarea"
        verbose_name_plural = "Recursos en Tarea"
        constraints = [
            models.CheckConstraint(
                name="tarea_recurso_exactly_one_resource",
                condition=(
                    (
                        models.Q(material__isnull=False)
                        & models.Q(mano_de_obra__isnull=True)
                        & models.Q(subcontrato__isnull=True)
                        & models.Q(mezcla__isnull=True)
                    )
                    | (
                        models.Q(material__isnull=True)
                        & models.Q(mano_de_obra__isnull=False)
                        & models.Q(subcontrato__isnull=True)
                        & models.Q(mezcla__isnull=True)
                    )
                    | (
                        models.Q(material__isnull=True)
                        & models.Q(mano_de_obra__isnull=True)
                        & models.Q(subcontrato__isnull=False)
                        & models.Q(mezcla__isnull=True)
                    )
                    | (
                        models.Q(material__isnull=True)
                        & models.Q(mano_de_obra__isnull=True)
                        & models.Q(subcontrato__isnull=True)
                        & models.Q(mezcla__isnull=False)
                    )
                ),
            ),
            models.CheckConstraint(
                name="tarea_recurso_cantidad_gt_zero",
                condition=models.Q(cantidad__gt=0),
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        selected_resources = sum(
            bool(resource_id)
            for resource_id in (
                self.material_id,
                self.mano_de_obra_id,
                self.subcontrato_id,
                self.mezcla_id,
            )
        )
        if selected_resources != 1:
            errors["__all__"] = (
                "Debés seleccionar exactamente un recurso: material, mano de obra, "
                "subcontrato o mezcla."
            )

        if self.cantidad is not None and self.cantidad <= 0:
            errors["cantidad"] = "La cantidad debe ser mayor que cero."

        if self.tarea_id:
            company_id = self.tarea.company_id
            if self.material_id and self.material.company_id != company_id:
                errors["material"] = "El material no pertenece a la empresa de la tarea."
            if self.mano_de_obra_id and self.mano_de_obra.company_id != company_id:
                errors["mano_de_obra"] = (
                    "La mano de obra no pertenece a la empresa de la tarea."
                )
            if self.subcontrato_id and self.subcontrato.company_id != company_id:
                errors["subcontrato"] = (
                    "El subcontrato no pertenece a la empresa de la tarea."
                )
            if self.mezcla_id and self.mezcla.company_id != company_id:
                errors["mezcla"] = "La mezcla no pertenece a la empresa de la tarea."

        if errors:
            raise ValidationError(errors)

    def get_recurso(self):
        if self.material_id:
            return self.material
        if self.mano_de_obra_id:
            return self.mano_de_obra
        if self.subcontrato_id:
            return self.subcontrato
        if self.mezcla_id:
            return self.mezcla
        return None

    def get_tipo(self):
        if self.material_id:
            return "material"
        if self.mano_de_obra_id:
            return "mano_de_obra"
        if self.subcontrato_id:
            return "subcontrato"
        if self.mezcla_id:
            return "mezcla"
        return None

    def precio_unitario(self):
        """Precio por unidad del recurso según el lote."""
        total = self.costo_total()
        if total and self.cantidad:
            return total / self.cantidad
        return Decimal("0")

    def precio_unitario_usd(self):
        """UA en USD: precio unitario convertido a dólares."""
        total_usd = self.costo_total_usd()
        if total_usd is not None and self.cantidad and self.cantidad > 0:
            return total_usd / self.cantidad
        return None

    def _get_hoja_precio_material(self, lote):
        try:
            return HojaPrecioMaterial.objects.get(
                hoja=lote.hoja_materiales, material=self.material
            )
        except HojaPrecioMaterial.DoesNotExist:
            return None

    def _get_moneda(self, lote):
        """Moneda del recurso: ARS o USD."""
        if self.material_id:
            hp = self._get_hoja_precio_material(lote)
            return (hp.moneda if hp else "ARS") or "ARS"
        if self.mano_de_obra_id:
            return "ARS"
        if self.subcontrato_id:
            try:
                hp = HojaPrecioSubcontrato.objects.get(
                    hoja=lote.hoja_subcontratos, subcontrato=self.subcontrato
                )
                return hp.moneda or "ARS"
            except HojaPrecioSubcontrato.DoesNotExist:
                return "ARS"
        if self.mezcla_id:
            return "ARS"
        return "ARS"

    def costo_total(self):
        lote = self.tarea.lote
        if self.material_id:
            hp = self._get_hoja_precio_material(lote)
            return (self.cantidad * hp.precio_unidad_venta) if hp else Decimal("0")
        if self.mano_de_obra_id:
            try:
                hp = HojaPrecioManoDeObra.objects.get(
                    hoja=lote.hoja_mano_de_obra, mano_de_obra=self.mano_de_obra
                )
                return self.cantidad * hp.precio_unidad_venta
            except HojaPrecioManoDeObra.DoesNotExist:
                return Decimal("0")
        if self.subcontrato_id:
            try:
                hp = HojaPrecioSubcontrato.objects.get(
                    hoja=lote.hoja_subcontratos, subcontrato=self.subcontrato
                )
                return self.cantidad * hp.precio_unidad_venta
            except HojaPrecioSubcontrato.DoesNotExist:
                return Decimal("0")
        if self.mezcla_id:
            if self.mezcla.hoja_id == lote.hoja_materiales_id:
                return self.cantidad * self.mezcla.precio_por_unidad_mezcla()
            return Decimal("0")
        return Decimal("0")

    def costo_total_usd(self):
        """Costo en USD: ARS se convierte según cotización del lote, USD queda igual."""
        total = self.costo_total()
        if total == 0:
            return Decimal("0")
        lote = self.tarea.lote
        moneda = self._get_moneda(lote)
        if moneda == "USD":
            return total
        cotiz = lote.get_cotizacion_usd()
        if cotiz and cotiz > 0:
            return total / cotiz
        return None

    def costo_total_usd_con_cotizacion(self, cotizacion):
        """Costo en USD usando cotización externa (para presupuestos)."""
        total = self.costo_total()
        if total == 0:
            return Decimal("0")
        lote = self.tarea.lote
        moneda = self._get_moneda(lote)
        if moneda == "USD":
            return total
        if cotizacion and cotizacion > 0:
            return total / cotizacion
        return None