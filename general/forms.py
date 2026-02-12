from django import forms

from .models import CategoriaMaterial, Proveedor, Rubro, Subrubro, TipoMaterial, Unidad


class RubroForm(forms.ModelForm):
    class Meta:
        model = Rubro
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Ej: Obra gruesa",
                    "autocomplete": "off",
                }
            )
        }


class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ej: m2, kg, hora",
                    "autocomplete": "off",
                }
            )
        }


class TipoMaterialForm(forms.ModelForm):
    class Meta:
        model = TipoMaterial
        fields = ["nombre"]


class CategoriaMaterialForm(forms.ModelForm):
    class Meta:
        model = CategoriaMaterial
        fields = ["tipo", "nombre"]


class SubrubroForm(forms.ModelForm):
    class Meta:
        model = Subrubro
        fields = ["rubro", "nombre"]


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "direccion", "telefono", "email"]

