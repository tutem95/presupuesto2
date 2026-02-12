from django.urls import path

from . import views


app_name = "general"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
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
]

