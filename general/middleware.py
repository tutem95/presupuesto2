"""
Middleware multi-tenant: setea request.company y request.membership desde la sesión.
Controla acceso por secciones (Presupuestos, Sueldos, Compras).
"""
import logging

from django.shortcuts import redirect
from django.urls import Resolver404, resolve

logger = logging.getLogger(__name__)

SECTION_NAMES = {
    "presupuestos": "Presupuestos",
    "sueldos": "Sueldos",
    "compras": "Compras",
}

# Rutas que no requieren company (url_name con namespace si aplica)
NO_COMPANY_URL_NAMES = {
    "usuarios:login",
    "usuarios:logout",
    "usuarios:company_select",
    "usuarios:no_company",
    "no_section_access",
}

# Rutas que requieren is_admin (gestión de usuarios)
ADMIN_ONLY_URL_NAMES = {
    "general:member_list",
    "general:member_add",
    "general:member_edit",
    "general:member_remove",
}

# Ruta pública para usuarios autenticados (sin sección específica)
NO_SECTION_REQUIRED_URL_NAMES = {
    "general:dashboard",
}

# Requisito de sección por namespace de URL
SECTION_BY_NAMESPACE = {
    "general": "presupuestos",
    "recursos": "presupuestos",
    "presupuestos": "presupuestos",
    "compras": "compras",
    "empleados": "sueldos",
}

# Rutas con nombre sin namespace (definidas en urls raíz)
SECTION_BY_URL_NAME = {
    "tareas": "presupuestos",
}


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


def _resolve_route(path):
    """Resuelve una ruta a (namespace, url_name, full_name), si existe."""
    try:
        match = resolve(path)
    except Resolver404:
        return None, None, None
    except Exception:
        logger.exception("Error resolviendo ruta para permisos: %s", path)
        return None, None, None

    namespace = match.namespace or None
    url_name = match.url_name or None
    full_name = f"{namespace}:{url_name}" if namespace and url_name else url_name
    return namespace, url_name, full_name


def _required_section(namespace, url_name, full_name):
    """Devuelve la sección requerida para la ruta actual."""
    if full_name in NO_SECTION_REQUIRED_URL_NAMES:
        return None
    if full_name in NO_COMPANY_URL_NAMES:
        return None
    if url_name in SECTION_BY_URL_NAME:
        return SECTION_BY_URL_NAME[url_name]
    if namespace in SECTION_BY_NAMESPACE:
        return SECTION_BY_NAMESPACE[namespace]
    return None


def _membership_sections(membership):
    """Devuelve los códigos de sección del membership activo."""
    if not membership:
        return []
    if membership.is_admin:
        return list(SECTION_NAMES.keys())

    # Usa prefetch de get_user_membership para evitar N+1.
    section_codes = [ms.section.code for ms in membership.membership_sections.all()]
    return list(dict.fromkeys(section_codes))


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
            request.user_sections = _membership_sections(membership)
            request.user_sections_info = [
                {"code": code, "nombre": SECTION_NAMES.get(code, code)}
                for code in request.user_sections
            ]

            namespace, url_name, full_name = _resolve_route(request.path_info)

            # Nunca interceptar el admin de Django.
            if request.path.startswith("/admin/"):
                return self.get_response(request)

            if request.company is None:
                # Usuario autenticado pero sin empresa activa: solo se permiten rutas públicas.
                if full_name not in NO_COMPANY_URL_NAMES:
                    return redirect("usuarios:company_select")
            elif request.membership:
                # Con empresa activa: validar rol admin y sección.
                if full_name in ADMIN_ONLY_URL_NAMES and not request.membership.is_admin:
                    return redirect("no_section_access")

                required_section = _required_section(namespace, url_name, full_name)
                if required_section and not request.membership.has_section_access(
                    required_section
                ):
                    return redirect("no_section_access")

        response = self.get_response(request)
        return response
