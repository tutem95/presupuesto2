from django.urls import path

from . import views


app_name = "recursos"

urlpatterns = [
    # Materiales
    path("materiales/", views.material_list, name="material_list"),
    path("materiales/<int:pk>/editar/", views.material_edit, name="material_edit"),
    path("materiales/<int:pk>/eliminar/", views.material_delete, name="material_delete"),
    path(
        "materiales/actualizar-precios/",
        views.material_bulk_update,
        name="material_bulk_update",
    ),
    # Mano de obra
    path("mano-de-obra/", views.mano_de_obra_list, name="mano_de_obra_list"),
    path(
        "mano-de-obra/<int:pk>/editar/",
        views.mano_de_obra_edit,
        name="mano_de_obra_edit",
    ),
    path(
        "mano-de-obra/<int:pk>/eliminar/",
        views.mano_de_obra_delete,
        name="mano_de_obra_delete",
    ),
    # Subcontratos
    path("subcontratos/", views.subcontrato_list, name="subcontrato_list"),
    path(
        "subcontratos/<int:pk>/editar/",
        views.subcontrato_edit,
        name="subcontrato_edit",
    ),
    path(
        "subcontratos/<int:pk>/eliminar/",
        views.subcontrato_delete,
        name="subcontrato_delete",
    ),
    # Hojas de precios
    path("hojas-precio/", views.hoja_precios_list, name="hoja_precios_list"),
    path(
        "hojas-precio/<int:pk>/",
        views.hoja_precios_detalle,
        name="hoja_precios_detalle",
    ),
]

