from django.urls import path

from . import views

app_name = "empleados"

urlpatterns = [
    path("", views.index, name="index"),
    path("nomina/", views.nomina, name="nomina"),
    path("sueldos/", views.sueldos, name="sueldos"),
]
