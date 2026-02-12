from django import forms

from .models import ManoDeObra, Material, Subcontrato


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            "nombre",
            "proveedor",
            "tipo",
            "categoria",
            "unidad_de_venta",
            "cantidad_por_unidad_venta",
            "precio_unidad_venta",
            "moneda",
        ]


class ManoDeObraForm(forms.ModelForm):
    class Meta:
        model = ManoDeObra
        fields = [
            "descripcion_puesto",
            "equipo",
            "unidad_de_analisis",
            "precio_por_unidad",
        ]


class SubcontratoForm(forms.ModelForm):
    class Meta:
        model = Subcontrato
        fields = [
            "descripcion",
            "proveedor",
            "unidad_de_analisis",
            "precio_por_unidad",
            "moneda",
        ]

