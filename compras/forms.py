from django import forms

from general.models import Obra, Proveedor, Rubro, Subrubro

from .models import Compra, Semana


class SemanaForm(forms.ModelForm):
    class Meta:
        model = Semana
        fields = ["fecha"]
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = [
            "obra", "rubro", "subrubro", "item", "proveedor", "forma_pago",
            "monto_total", "estado",
            "numero_ppto_fc", "fecha_factura", "monto_sin_iva",
            "iva_21", "iva_105", "perc_iibb",
            "monto_a_pagar", "observaciones", "porcentaje_pago",
            "es_subcontrato",
        ]
        widgets = {
            "fecha_factura": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["obra"].queryset = Obra.objects.filter(
                company=request.company
            ).order_by("nombre")
            self.fields["proveedor"].queryset = Proveedor.objects.filter(
                company=request.company
            ).order_by("nombre")
            self.fields["rubro"].queryset = Rubro.objects.filter(
                company=request.company
            ).order_by("nombre")
            self.fields["subrubro"].queryset = Subrubro.objects.filter(
                company=request.company
            ).select_related("rubro").order_by("rubro__nombre", "nombre")
