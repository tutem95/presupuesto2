from django import forms

from general.models import (
    CategoriaMaterial,
    Equipo,
    Proveedor,
    RefEquipo,
    Rubro,
    Subrubro,
    TipoMaterial,
    Unidad,
)

from .models import (
    HojaPrecioMaterial,
    HojaPrecioManoDeObra,
    HojaPrecioSubcontrato,
    HojaPrecios,
    HojaPreciosManoDeObra,
    HojaPreciosSubcontrato,
    Lote,
    ManoDeObra,
    Material,
    Mezcla,
    MezclaMaterial,
    Subcontrato,
    Tarea,
    TareaRecurso,
)


class HojaPrecioMaterialForm(forms.ModelForm):
    """Form para editar cantidad, precio y moneda de un material en una hoja de precios."""
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = HojaPrecioMaterial
        fields = ["cantidad_por_unidad_venta", "precio_unidad_venta", "moneda"]


class MaterialForm(forms.ModelForm):
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
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

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["proveedor"].queryset = Proveedor.objects.filter(
                company=request.company
            )
            self.fields["tipo"].queryset = TipoMaterial.objects.filter(
                company=request.company
            )
            self.fields["categoria"].queryset = CategoriaMaterial.objects.filter(
                company=request.company
            )
            self.fields["unidad_de_venta"].queryset = Unidad.objects.filter(
                company=request.company
            )


class ManoDeObraForm(forms.ModelForm):
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = ManoDeObra
        fields = [
            "rubro",
            "subrubro",
            "tarea",
            "equipo",
            "ref_equipo",
            "cantidad_por_unidad_venta",
            "unidad_de_venta",
            "precio_unidad_venta",
        ]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["rubro"].queryset = Rubro.objects.filter(
                company=request.company
            )
            self.fields["subrubro"].queryset = Subrubro.objects.filter(
                company=request.company
            )
            self.fields["equipo"].queryset = Equipo.objects.filter(
                company=request.company
            )
            self.fields["ref_equipo"].queryset = RefEquipo.objects.filter(
                company=request.company
            )
            self.fields["unidad_de_venta"].queryset = Unidad.objects.filter(
                company=request.company
            )


class SubcontratoForm(forms.ModelForm):
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = Subcontrato
        fields = [
            "rubro",
            "subrubro",
            "tarea",
            "proveedor",
            "cantidad_por_unidad_venta",
            "unidad_de_venta",
            "precio_unidad_venta",
            "moneda",
        ]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["rubro"].queryset = Rubro.objects.filter(
                company=request.company
            )
            self.fields["subrubro"].queryset = Subrubro.objects.filter(
                company=request.company
            )
            self.fields["proveedor"].queryset = Proveedor.objects.filter(
                company=request.company
            )
            self.fields["unidad_de_venta"].queryset = Unidad.objects.filter(
                company=request.company
            )


class HojaPrecioManoDeObraForm(forms.ModelForm):
    """Form para editar cantidad y precio de mano de obra en una hoja."""
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = HojaPrecioManoDeObra
        fields = ["cantidad_por_unidad_venta", "precio_unidad_venta"]


class MezclaForm(forms.ModelForm):
    class Meta:
        model = Mezcla
        fields = ["nombre", "unidad_de_mezcla", "hoja"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["unidad_de_mezcla"].queryset = Unidad.objects.filter(
                company=request.company
            )
            self.fields["hoja"].queryset = HojaPrecios.objects.filter(
                company=request.company
            )
            self.fields["hoja"].required = False
            self.fields["hoja"].empty_label = "Precios actuales"


class MezclaMaterialForm(forms.ModelForm):
    cantidad = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = MezclaMaterial
        fields = ["material", "cantidad"]

    def __init__(self, *args, mezcla=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mezcla:
            if mezcla.hoja:
                ids = mezcla.hoja.detalles.values_list("material_id", flat=True)
                self.fields["material"].queryset = Material.objects.filter(
                    pk__in=ids
                ).select_related("proveedor", "unidad_de_venta")
            else:
                self.fields["material"].queryset = Material.objects.filter(
                    company=mezcla.company
                ).select_related("proveedor", "unidad_de_venta")


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ["nombre", "rubro", "subrubro"]

    def __init__(self, *args, request=None, lote=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request and request.company:
            self.fields["rubro"].queryset = Rubro.objects.filter(
                company=request.company
            )
            # Subrubros solo del rubro seleccionado (instance o POST)
            rubro_id = None
            if kwargs.get("instance") and kwargs["instance"].rubro_id:
                rubro_id = kwargs["instance"].rubro_id
            elif args and args[0].get("rubro"):
                try:
                    rubro_id = int(args[0]["rubro"])
                except (ValueError, TypeError):
                    pass
            if rubro_id:
                self.fields["subrubro"].queryset = Subrubro.objects.filter(
                    company=request.company, rubro_id=rubro_id
                )
            else:
                self.fields["subrubro"].queryset = Subrubro.objects.none()


class TareaRecursoForm(forms.Form):
    """Form para agregar un recurso a una tarea."""
    tipo = forms.ChoiceField(
        choices=[
            ("material", "Material"),
            ("mano_de_obra", "Mano de obra"),
            ("subcontrato", "Subcontrato"),
            ("mezcla", "Mezcla"),
        ],
        widget=forms.RadioSelect,
    )
    material = forms.ModelChoiceField(
        queryset=Material.objects.none(),
        required=False,
        empty_label="-- Elegir material --",
    )
    mano_de_obra = forms.ModelChoiceField(
        queryset=ManoDeObra.objects.none(),
        required=False,
        empty_label="-- Elegir puesto --",
    )
    subcontrato = forms.ModelChoiceField(
        queryset=Subcontrato.objects.none(),
        required=False,
        empty_label="-- Elegir subcontrato --",
    )
    mezcla = forms.ModelChoiceField(
        queryset=Mezcla.objects.none(),
        required=False,
        empty_label="-- Elegir mezcla --",
    )
    cantidad = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    def __init__(self, *args, lote=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lote:
            # Materiales de la hoja de materiales (incl. proveedor para distinguir)
            mat_ids = lote.hoja_materiales.detalles.values_list("material_id", flat=True)
            self.fields["material"].queryset = Material.objects.filter(
                pk__in=mat_ids
            ).select_related("proveedor", "unidad_de_venta").order_by("nombre", "proveedor__nombre")
            # Mano de obra de la hoja (incl. equipo y ref_equipo para distinguir)
            mo_ids = lote.hoja_mano_de_obra.detalles.values_list("mano_de_obra_id", flat=True)
            self.fields["mano_de_obra"].queryset = ManoDeObra.objects.filter(
                pk__in=mo_ids
            ).select_related("unidad_de_venta", "equipo", "ref_equipo", "subrubro").order_by(
                "tarea", "equipo__nombre", "ref_equipo__nombre"
            )
            # Subcontratos de la hoja
            sub_ids = lote.hoja_subcontratos.detalles.values_list("subcontrato_id", flat=True)
            self.fields["subcontrato"].queryset = Subcontrato.objects.filter(
                pk__in=sub_ids
            ).select_related("proveedor", "unidad_de_venta")
            # Mezclas que usan la hoja de materiales del lote
            self.fields["mezcla"].queryset = Mezcla.objects.filter(
                hoja=lote.hoja_materiales
            ).select_related("unidad_de_mezcla")

    def clean(self):
        data = super().clean()
        tipo = data.get("tipo")
        if tipo == "material" and not data.get("material"):
            raise forms.ValidationError("Seleccioná un material.")
        if tipo == "mano_de_obra" and not data.get("mano_de_obra"):
            raise forms.ValidationError("Seleccioná mano de obra.")
        if tipo == "subcontrato" and not data.get("subcontrato"):
            raise forms.ValidationError("Seleccioná un subcontrato.")
        if tipo == "mezcla" and not data.get("mezcla"):
            raise forms.ValidationError("Seleccioná una mezcla.")
        return data


class HojaPrecioSubcontratoForm(forms.ModelForm):
    """Form para editar cantidad, precio y moneda de un subcontrato en una hoja."""
    cantidad_por_unidad_venta = forms.DecimalField(
        max_digits=10, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    precio_unidad_venta = forms.DecimalField(
        max_digits=12, decimal_places=4,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )

    class Meta:
        model = HojaPrecioSubcontrato
        fields = ["cantidad_por_unidad_venta", "precio_unidad_venta", "moneda"]

