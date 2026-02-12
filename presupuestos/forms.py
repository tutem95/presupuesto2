from django import forms

from general.models import Obra, TipoDolar
from recursos.models import Lote, Tarea

from .models import Presupuesto, PresupuestoItem


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ["obra", "fecha", "instancia", "lote", "tipo_dolar", "fecha_dolar", "activo"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "instancia": forms.TextInput(attrs={"placeholder": "Ej: 1, 2, Revisión"}),
            "fecha_dolar": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["obra"].queryset = Obra.objects.filter(company=request.company)
            self.fields["lote"].queryset = Lote.objects.filter(
                company=request.company
            ).select_related("hoja_materiales", "hoja_mano_de_obra", "hoja_subcontratos")
            self.fields["tipo_dolar"].queryset = TipoDolar.objects.filter(
                company=request.company
            )
            self.fields["obra"].required = True
            self.fields["fecha"].required = True
            self.fields["instancia"].required = True
            self.fields["lote"].required = True
            self.fields["tipo_dolar"].required = False
            self.fields["fecha_dolar"].required = False


class PresupuestoItemForm(forms.Form):
    tarea = forms.ModelChoiceField(queryset=Tarea.objects.none(), label="Tarea")
    cantidad = forms.DecimalField(
        max_digits=12,
        decimal_places=4,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )

    def __init__(self, *args, presupuesto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if presupuesto:
            tareas_en_presupuesto = presupuesto.items.values_list("tarea_id", flat=True)
            self.fields["tarea"].queryset = presupuesto.lote.tareas.exclude(
                pk__in=tareas_en_presupuesto
            ).select_related("rubro", "subrubro").order_by(
                "rubro__nombre", "subrubro__nombre", "nombre"
            )
