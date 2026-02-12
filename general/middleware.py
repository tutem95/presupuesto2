"""
Middleware multi-tenant: setea request.company y request.membership desde la sesión.
Controla acceso por secciones (Presupuestos, Sueldos, Compras).
"""
from django.shortcuts import redirect
from django.urls import resolve


def get_user_membership(request):
    """Obtiene el membership activo (company + membership) del usuario."""
    if not request.user.is_authenticated:
        return None, None
    company_id = request.session.get("company_id")
    if not company_id:
        return None, None
    membership = (
        request.user.company_memberships.select_related("company")
        .prefetch_related("membership_sections__section")
        .filter(company_id=company_id)
        .first()
    )
    if not membership:
        return None, None
    return membership.company, membership


# Rutas que no requieren company (url_name con namespace si aplica)
NO_COMPANY_URL_NAMES = (
    "usuarios:login",
    "usuarios:logout",
    "usuarios:company_select",
    "usuarios:no_company",
    "no_section_access",
)

# Rutas que requieren is_admin (gestión de usuarios)
ADMIN_ONLY_URL_NAMES = (
    "general:member_list",
    "general:member_add",
    "general:member_edit",
    "general:member_remove",
)

# Prefijos de path que requieren sección presupuestos
PRESUPUESTOS_PATH_PREFIXES = (
    "/indice",
    "/presupuesto",
    "/obras",
    "/rubros",
    "/unidades",
    "/tipos-material",
    "/equipos",
    "/categorias-material",
    "/ref-equipos",
    "/subrubros",
    "/proveedores",
    "/tipos-dolar",
    "/tabla-dolar",
    "/tareas",
    "/recursos",
    "/presupuestos",
)


def _path_requires_presupuestos(path):
    """True si el path requiere acceso a sección Presupuestos."""
    path = (path or "/").rstrip("/") or "/"
    if path == "/":
        return True
    return any(path.startswith(p) for p in PRESUPUESTOS_PATH_PREFIXES)


def _path_is_admin_only(path):
    """True si el path es solo para admins."""
    try:
        match = resolve(path)
        name = match.url_name
        if match.namespace:
            name = f"{match.namespace}:{name}"
        return name in ADMIN_ONLY_URL_NAMES
    except Exception:
        return False


class CompanyMiddleware:
    """
    Setea request.company y request.membership.
    Verifica acceso por sección (admin tiene acceso a todo).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        request.membership = None
        request.user_sections = []
        request.user_sections_info = []

        if request.user.is_authenticated:
            company, membership = get_user_membership(request)
            request.company = company
            request.membership = membership

            if membership:
                request.user_sections = list(
                    membership.membership_sections.values_list(
                        "section__code", flat=True
                    )
                )
                if membership.is_admin:
                    request.user_sections = ["presupuestos", "sueldos", "compras"]
                # Para templates: lista de {code, nombre}
                SECTION_NAMES = {"presupuestos": "Presupuestos", "sueldos": "Sueldos", "compras": "Compras"}
                request.user_sections_info = [
                    {"code": c, "nombre": SECTION_NAMES.get(c, c)}
                    for c in request.user_sections
                ]

            if request.company is None:
                try:
                    match = resolve(request.path_info)
                    name = match.url_name
                    if match.namespace:
                        name = f"{match.namespace}:{name}"
                    if name not in NO_COMPANY_URL_NAMES and not request.path.startswith("/admin/"):
                        return redirect("usuarios:company_select")
                except Exception:
                    pass
            elif request.membership and not request.path.startswith("/admin/"):
                path = request.path
                try:
                    match = resolve(path)
                    full_name = match.url_name
                    if match.namespace:
                        full_name = f"{match.namespace}:{full_name}"
                except Exception:
                    full_name = None

                if full_name not in NO_COMPANY_URL_NAMES:
                    if _path_is_admin_only(path):
                        if not request.membership.is_admin:
                            return redirect("no_section_access")
                    elif _path_requires_presupuestos(path):
                        if not request.membership.has_section_access("presupuestos"):
                            return redirect("no_section_access")
                    # sueldos y compras se verifican cuando existan esas URLs

        response = self.get_response(request)
        return response
