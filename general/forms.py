from django import forms
from django.contrib.auth import get_user_model

from .models import (
    CategoriaMaterial,
    CompanyMembership,
    CompanyMembershipSection,
    CotizacionDolar,
    Equipo,
    Obra,
    Proveedor,
    RefEquipo,
    Rubro,
    Section,
    Subrubro,
    TipoDolar,
    TipoMaterial,
    Unidad,
)


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

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


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

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


class TipoMaterialForm(forms.ModelForm):
    class Meta:
        model = TipoMaterial
        fields = ["nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ["nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


class CategoriaMaterialForm(forms.ModelForm):
    class Meta:
        model = CategoriaMaterial
        fields = ["tipo", "nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request
        if request and request.company:
            self.fields["tipo"].queryset = TipoMaterial.objects.filter(company=request.company)


class SubrubroForm(forms.ModelForm):
    class Meta:
        model = Subrubro
        fields = ["rubro", "nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request
        if request and request.company:
            self.fields["rubro"].queryset = Rubro.objects.filter(company=request.company)


class RefEquipoForm(forms.ModelForm):
    class Meta:
        model = RefEquipo
        fields = ["equipo", "nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request
        if request and request.company:
            self.fields["equipo"].queryset = Equipo.objects.filter(company=request.company)


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "direccion", "telefono", "email"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


class TipoDolarForm(forms.ModelForm):
    class Meta:
        model = TipoDolar
        fields = ["nombre"]

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = ["nombre", "direccion", "pisos", "m2_construibles", "m2_vendibles", "valor_terreno"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Edificio Centro"}),
            "direccion": forms.TextInput(attrs={"placeholder": "Calle, número, ciudad"}),
            "pisos": forms.TextInput(attrs={"placeholder": "Ej: PB + 2 pisos"}),
            "m2_construibles": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "m2_vendibles": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "valor_terreno": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request
        self.fields["direccion"].required = False
        self.fields["pisos"].required = False
        self.fields["m2_construibles"].required = False
        self.fields["m2_vendibles"].required = False
        self.fields["valor_terreno"].required = False


class MemberAddForm(forms.Form):
    """Formulario para agregar usuario a la empresa (por username)."""
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Nombre de usuario", "autocomplete": "off"}),
    )
    sections = forms.MultipleChoiceField(
        label="Secciones",
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        if company:
            self.fields["sections"].choices = [
                (s.code, s.nombre) for s in Section.objects.all().order_by("nombre")
            ]

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("Ingresá el nombre de usuario.")
        User = get_user_model()
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Usuario no encontrado. Creá el usuario en Django admin primero.")
        if self.company and CompanyMembership.objects.filter(user=user, company=self.company).exists():
            raise forms.ValidationError("Ese usuario ya pertenece a esta empresa.")
        return user.username

    def save(self):
        User = get_user_model()
        user = User.objects.get(username__iexact=self.cleaned_data["username"])
        membership = CompanyMembership.objects.create(user=user, company=self.company)
        for code in self.cleaned_data["sections"]:
            section = Section.objects.get(code=code)
            CompanyMembershipSection.objects.create(membership=membership, section=section)
        return membership


class MemberEditForm(forms.Form):
    """Formulario para editar secciones de un miembro."""
    sections = forms.MultipleChoiceField(
        label="Secciones",
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, company=None, membership=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.membership = membership
        if company:
            self.fields["sections"].choices = [
                (s.code, s.nombre) for s in Section.objects.all().order_by("nombre")
            ]
        if membership:
            self.fields["sections"].required = not membership.is_admin
            self.fields["sections"].initial = list(
                membership.membership_sections.values_list("section__code", flat=True)
            )

    def clean_sections(self):
        sections = self.cleaned_data.get("sections", [])
        if self.membership and not self.membership.is_admin and not sections:
            raise forms.ValidationError("Los usuarios no-admin deben tener al menos una sección.")
        return sections

    def save(self):
        self.membership.membership_sections.all().delete()
        for code in self.cleaned_data.get("sections", []):
            section = Section.objects.get(code=code)
            CompanyMembershipSection.objects.create(membership=self.membership, section=section)

