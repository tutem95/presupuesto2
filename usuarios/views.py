from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from general.models import CompanyMembership


class LoginView(auth_views.LoginView):
    """
    Login: después de autenticar, setea la empresa activa por membership.
    - 0 empresas: redirige a mensaje sin acceso.
    - 1 empresa: setea session['company_id'] y redirige al dashboard.
    - 2+: redirige al selector de empresa.
    """

    template_name = "usuarios/login.html"

    def get_success_url(self):
        companies = list(
            CompanyMembership.objects.filter(user=self.request.user)
            .select_related("company")
            .values_list("company_id", "company__nombre")
        )
        if not companies:
            return reverse("usuarios:no_company")
        if len(companies) == 1:
            self.request.session["company_id"] = companies[0][0]
            return reverse("general:dashboard")
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
    memberships = [m for m in memberships_qs if m.is_admin or m.membership_sections.exists()]

    if not memberships:
        return redirect("usuarios:no_company")

    if request.method == "POST":
        company_id = request.POST.get("company_id")
        valid_ids = [m.company_id for m in memberships]
        try:
            if company_id and int(company_id) in valid_ids:
                request.session["company_id"] = int(company_id)
                return redirect("general:dashboard")
        except (ValueError, TypeError):
            pass

    return render(
        request,
        "usuarios/company_select.html",
        {"memberships": memberships},
    )


def no_company(request):
    """El usuario no pertenece a ninguna empresa."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")
    return render(request, "usuarios/no_company.html")


def no_section_access(request):
    """El usuario no tiene acceso a esta sección."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")
    if not request.company:
        return redirect("usuarios:company_select")
    return render(request, "usuarios/no_section_access.html")
