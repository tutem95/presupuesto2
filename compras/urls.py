from django.urls import path

from . import views

app_name = "compras"

urlpatterns = [
    path("", views.compras_list, name="compras_list"),
    path("semana/nueva/", views.semana_create, name="semana_create"),
    path("semana/<int:pk>/", views.semana_detalle, name="semana_detalle"),
    path("semana/<int:pk>/editar/", views.semana_edit, name="semana_edit"),
    path("<int:semana_pk>/compra/agregar/", views.compra_add, name="compra_add"),
    path(
        "<int:semana_pk>/compra/<int:compra_pk>/editar/",
        views.compra_edit,
        name="compra_edit",
    ),
    path(
        "<int:semana_pk>/compra/<int:compra_pk>/eliminar/",
        views.compra_delete,
        name="compra_delete",
    ),
]
