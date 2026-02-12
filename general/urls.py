from django.urls import path

from . import views


app_name = "general"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("indice/", views.indice, name="indice"),
    path("presupuesto/", views.presupuesto, name="presupuesto"),
    # Obras
    path("obras/", views.obra_list, name="obra_list"),
    path("obras/<int:pk>/editar/", views.obra_edit, name="obra_edit"),
    path("obras/<int:pk>/eliminar/", views.obra_delete, name="obra_delete"),
    # Rubros
    path("rubros/", views.rubro_list, name="rubro_list"),
    path("rubros/<int:pk>/editar/", views.rubro_edit, name="rubro_edit"),
    path("rubros/<int:pk>/eliminar/", views.rubro_delete, name="rubro_delete"),
    # Unidades
    path("unidades/", views.unidad_list, name="unidad_list"),
    path("unidades/<int:pk>/editar/", views.unidad_edit, name="unidad_edit"),
    path("unidades/<int:pk>/eliminar/", views.unidad_delete, name="unidad_delete"),
    # Tipos de material
    path("tipos-material/", views.tipo_material_list, name="tipo_material_list"),
    path(
        "tipos-material/<int:pk>/editar/",
        views.tipo_material_edit,
        name="tipo_material_edit",
    ),
    path(
        "tipos-material/<int:pk>/eliminar/",
        views.tipo_material_delete,
        name="tipo_material_delete",
    ),
    # Equipos
    path("equipos/", views.equipo_list, name="equipo_list"),
    path("equipos/<int:pk>/editar/", views.equipo_edit, name="equipo_edit"),
    path("equipos/<int:pk>/eliminar/", views.equipo_delete, name="equipo_delete"),
    # Categorías de material
    path(
        "categorias-material/",
        views.categoria_material_list,
        name="categoria_material_list",
    ),
    path(
        "categorias-material/<int:pk>/editar/",
        views.categoria_material_edit,
        name="categoria_material_edit",
    ),
    path(
        "categorias-material/<int:pk>/eliminar/",
        views.categoria_material_delete,
        name="categoria_material_delete",
    ),
    # Ref. Equipos (subcategoría de Equipo)
    path("ref-equipos/", views.ref_equipo_list, name="ref_equipo_list"),
    path(
        "ref-equipos/<int:pk>/editar/",
        views.ref_equipo_edit,
        name="ref_equipo_edit",
    ),
    path(
        "ref-equipos/<int:pk>/eliminar/",
        views.ref_equipo_delete,
        name="ref_equipo_delete",
    ),
    # Subrubros
    path("subrubros/", views.subrubro_list, name="subrubro_list"),
    path(
        "subrubros/<int:pk>/editar/",
        views.subrubro_edit,
        name="subrubro_edit",
    ),
    path(
        "subrubros/<int:pk>/eliminar/",
        views.subrubro_delete,
        name="subrubro_delete",
    ),
    # Proveedores
    path("proveedores/", views.proveedor_list, name="proveedor_list"),
    path(
        "proveedores/<int:pk>/editar/",
        views.proveedor_edit,
        name="proveedor_edit",
    ),
    path(
        "proveedores/<int:pk>/eliminar/",
        views.proveedor_delete,
        name="proveedor_delete",
    ),
    # Tipos de dólar
    path("tipos-dolar/", views.tipo_dolar_list, name="tipo_dolar_list"),
    path("tipos-dolar/<int:pk>/editar/", views.tipo_dolar_edit, name="tipo_dolar_edit"),
    path("tipos-dolar/<int:pk>/eliminar/", views.tipo_dolar_delete, name="tipo_dolar_delete"),
    # Tabla de dólar
    path("tabla-dolar/", views.tabla_dolar, name="tabla_dolar"),
    # Gestión de usuarios (solo admin)
    path("miembros/", views.member_list, name="member_list"),
    path("miembros/agregar/", views.member_add, name="member_add"),
    path("miembros/<int:pk>/editar/", views.member_edit, name="member_edit"),
    path("miembros/<int:pk>/quitar/", views.member_remove, name="member_remove"),
]

