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
    path(
        "mano-de-obra/actualizar-precios/",
        views.mano_de_obra_bulk_update,
        name="mano_de_obra_bulk_update",
    ),
    # Hojas de precios mano de obra
    path(
        "hojas-mano-de-obra/",
        views.hoja_mano_de_obra_list,
        name="hoja_mano_de_obra_list",
    ),
    path(
        "hojas-mano-de-obra/<int:pk>/",
        views.hoja_mano_de_obra_detalle,
        name="hoja_mano_de_obra_detalle",
    ),
    path(
        "hojas-mano-de-obra/<int:hoja_pk>/detalle/<int:detalle_pk>/editar/",
        views.hoja_mano_de_obra_detalle_edit,
        name="hoja_mano_de_obra_detalle_edit",
    ),
    path(
        "hojas-mano-de-obra/<int:hoja_pk>/detalle/<int:detalle_pk>/eliminar/",
        views.hoja_mano_de_obra_detalle_delete,
        name="hoja_mano_de_obra_detalle_delete",
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
    path(
        "subcontratos/actualizar-precios/",
        views.subcontrato_bulk_update,
        name="subcontrato_bulk_update",
    ),
    # Hojas de precios subcontratos
    path(
        "hojas-subcontrato/",
        views.hoja_subcontrato_list,
        name="hoja_subcontrato_list",
    ),
    path(
        "hojas-subcontrato/<int:pk>/",
        views.hoja_subcontrato_detalle,
        name="hoja_subcontrato_detalle",
    ),
    path(
        "hojas-subcontrato/<int:hoja_pk>/detalle/<int:detalle_pk>/editar/",
        views.hoja_subcontrato_detalle_edit,
        name="hoja_subcontrato_detalle_edit",
    ),
    path(
        "hojas-subcontrato/<int:hoja_pk>/detalle/<int:detalle_pk>/eliminar/",
        views.hoja_subcontrato_detalle_delete,
        name="hoja_subcontrato_detalle_delete",
    ),
    # Lotes y Maestro Tareas
    path("lotes/", views.lote_list, name="lote_list"),
    path("lotes/nuevo/", views.lote_create, name="lote_create"),
    path("lotes/<int:pk>/editar/", views.lote_edit, name="lote_edit"),
    path("lotes/<int:pk>/", views.lote_detalle, name="lote_detalle"),
    path("lotes/<int:lote_pk>/tareas/", views.tarea_list, name="tarea_list"),
    path("lotes/<int:lote_pk>/tareas/nueva/", views.tarea_create, name="tarea_create"),
    path("lotes/<int:lote_pk>/tareas/<int:pk>/", views.tarea_detalle, name="tarea_detalle"),
    path("lotes/<int:lote_pk>/tareas/<int:pk>/editar/", views.tarea_edit, name="tarea_edit"),
    path("lotes/<int:lote_pk>/tareas/<int:pk>/eliminar/", views.tarea_delete, name="tarea_delete"),
    path(
        "lotes/<int:lote_pk>/tareas/<int:tarea_pk>/agregar-recurso/",
        views.tarea_recurso_add,
        name="tarea_recurso_add",
    ),
    path(
        "lotes/<int:lote_pk>/tareas/<int:tarea_pk>/recurso/<int:recurso_pk>/eliminar/",
        views.tarea_recurso_delete,
        name="tarea_recurso_delete",
    ),
    # Mezclas
    path("mezclas/", views.mezcla_list, name="mezcla_list"),
    path("mezclas/<int:pk>/", views.mezcla_detalle, name="mezcla_detalle"),
    path("mezclas/<int:pk>/editar/", views.mezcla_edit, name="mezcla_edit"),
    path("mezclas/<int:pk>/eliminar/", views.mezcla_delete, name="mezcla_delete"),
    path(
        "mezclas/<int:pk>/agregar-material/",
        views.mezcla_material_add,
        name="mezcla_material_add",
    ),
    path(
        "mezclas/<int:mezcla_pk>/material/<int:detalle_pk>/eliminar/",
        views.mezcla_material_delete,
        name="mezcla_material_delete",
    ),
    # Hojas de precios
    path("hojas-precio/", views.hoja_precios_list, name="hoja_precios_list"),
    path(
        "hojas-precio/<int:pk>/",
        views.hoja_precios_detalle,
        name="hoja_precios_detalle",
    ),
    path(
        "hojas-precio/<int:hoja_pk>/detalle/<int:detalle_pk>/editar/",
        views.hoja_detalle_edit,
        name="hoja_detalle_edit",
    ),
    path(
        "hojas-precio/<int:hoja_pk>/detalle/<int:detalle_pk>/eliminar/",
        views.hoja_detalle_delete,
        name="hoja_detalle_delete",
    ),
]

