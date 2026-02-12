from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "empleados/index.html")


@login_required
def nomina(request):
    return render(request, "empleados/nomina.html")


@login_required
def sueldos(request):
    return render(request, "empleados/sueldos.html")
