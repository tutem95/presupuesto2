from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from general.models import CompanyMembership


SECTION_LANDING_ROUTES = (
    ("presupuestos", "general:dashboard"),
    ("compras", "compras:compras_list"),
    ("sueldos", "empleados:index"),
)


def _membership_section_codes(membership):
    if not membership:
        return []
    if membership.is_admin:
        return [code for code, _ in SECTION_LANDING_ROUTES]
    return [ms.section.code for ms in membership.membership_sections.all()]


def _membership_has_any_access(membership):
    return bool(_membership_section_codes(membership))


def _landing_url_for_membership(membership):
    """Devuelve la home según secciones habilitadas en el membership."""
    section_codes = set(_membership_section_codes(membership))
    for section_code, route_name in SECTION_LANDING_ROUTES:
        if section_code in section_codes:
            return reverse(route_name)
    return reverse("usuarios:no_company")


class LoginView(auth_views.LoginView):
    """
    Login: después de autenticar, setea la empresa activa por membership.
    - 0 empresas: redirige a mensaje sin acceso.
    - 1 empresa: setea session['company_id'] y redirige al dashboard.
    - 2+: redirige al selector de empresa.
    """

    template_name = "usuarios/login.html"

    def get_success_url(self):
        memberships = list(
            CompanyMembership.objects.filter(user=self.request.user)
            .select_related("company")
            .prefetch_related("membership_sections__section")
            .order_by("company__nombre")
        )
        valid_memberships = [m for m in memberships if _membership_has_any_access(m)]

        if not valid_memberships:
            return reverse("usuarios:no_company")
        if len(valid_memberships) == 1:
            membership = valid_memberships[0]
            self.request.session["company_id"] = membership.company_id
            return _landing_url_for_membership(membership)
        return reverse("usuarios:company_select")


@require_http_methods(["GET", "POST"])
def company_select(request):
    """Selector de empresa: el usuario elige con qué empresa trabajar. Setea session['company_id']."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    memberships_qs = (
        CompanyMembership.objects.filter(user=request.user)
        .select_related("company")
        .prefetch_related("membership_sections", "membership_sections__section")
        .order_by("company__nombre")
    )
    # Solo empresas donde tiene acceso (admin o al menos una sección)
    memberships = [m for m in memberships_qs if _membership_has_any_access(m)]

    if not memberships:
        return redirect("usuarios:no_company")

    if request.method == "POST":
        company_id = request.POST.get("company_id")
        selected_membership = next(
            (m for m in memberships if str(m.company_id) == str(company_id)),
            None,
        )
        if selected_membership:
            request.session["company_id"] = selected_membership.company_id
            return redirect(_landing_url_for_membership(selected_membership))
        messages.error(request, "La empresa seleccionada no es válida para tu usuario.")

    return render(
        request,
        "usuarios/company_select.html",
        {"memberships": memberships},
    )


@login_required
def no_company(request):
    """El usuario no pertenece a ninguna empresa."""
    return render(request, "usuarios/no_company.html")


@login_required
def no_section_access(request):
    """El usuario no tiene acceso a esta sección."""
    if not request.company:
        return redirect("usuarios:company_select")
    return render(request, "usuarios/no_section_access.html")
