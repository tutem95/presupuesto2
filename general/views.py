from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from general.models import CategoriaMaterial, Proveedor, Rubro, Subrubro, TipoMaterial, Unidad
from recursos.models import ManoDeObra, Material, Subcontrato

from .forms import (
    CategoriaMaterialForm,
    ProveedorForm,
    RubroForm,
    SubrubroForm,
    TipoMaterialForm,
    UnidadForm,
)


def dashboard(request):
    """
    Panel de control básico del sistema de presupuestos.

    Muestra un resumen de las entidades principales:
    - Catálogos generales: rubros, subrubros, unidades, tipos y categorías de material.
    - Recursos económicos: materiales, mano de obra y subcontratos.
    """
    contexto = {
        "totales": {
            "rubros": Rubro.objects.count(),
            "subrubros": Subrubro.objects.count(),
            "unidades": Unidad.objects.count(),
            "tipos_material": TipoMaterial.objects.count(),
            "categorias_material": CategoriaMaterial.objects.count(),
            "materiales": Material.objects.count(),
            "mano_de_obra": ManoDeObra.objects.count(),
            "subcontratos": Subcontrato.objects.count(),
            "proveedores": Proveedor.objects.count(),
        }
    }
    return render(request, "general/dashboard.html", contexto)


@login_required
def rubro_list(request):
    """
    Listado y alta rápida de Rubros para usuarios autenticados (no hace falta ser staff).
    """
    if request.method == "POST":
        form = RubroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:rubro_list")
    else:
        form = RubroForm()

    rubros = Rubro.objects.all()
    contexto = {
        "rubros": rubros,
        "form": form,
    }
    return render(request, "general/rubro_list.html", contexto)


@login_required
def rubro_edit(request, pk):
    rubro = get_object_or_404(Rubro, pk=pk)
    if request.method == "POST":
        form = RubroForm(request.POST, instance=rubro)
        if form.is_valid():
            form.save()
            return redirect("general:rubro_list")
    else:
        form = RubroForm(instance=rubro)

    rubros = Rubro.objects.all()
    return render(
        request,
        "general/rubro_list.html",
        {"rubros": rubros, "form": form, "editing": rubro},
    )


@login_required
def rubro_delete(request, pk):
    rubro = get_object_or_404(Rubro, pk=pk)
    if request.method == "POST":
        rubro.delete()
        return redirect("general:rubro_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": rubro, "cancel_url": "general:rubro_list"},
    )


@login_required
def unidad_list(request):
    if request.method == "POST":
        form = UnidadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:unidad_list")
    else:
        form = UnidadForm()

    unidades = Unidad.objects.all()
    return render(
        request,
        "general/unidad_list.html",
        {"unidades": unidades, "form": form},
    )


@login_required
def unidad_edit(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == "POST":
        form = UnidadForm(request.POST, instance=unidad)
        if form.is_valid():
            form.save()
            return redirect("general:unidad_list")
    else:
        form = UnidadForm(instance=unidad)

    unidades = Unidad.objects.all()
    return render(
        request,
        "general/unidad_list.html",
        {"unidades": unidades, "form": form, "editing": unidad},
    )


@login_required
def unidad_delete(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == "POST":
        unidad.delete()
        return redirect("general:unidad_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": unidad, "cancel_url": "general:unidad_list"},
    )


@login_required
def tipo_material_list(request):
    if request.method == "POST":
        form = TipoMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:tipo_material_list")
    else:
        form = TipoMaterialForm()

    tipos = TipoMaterial.objects.all()
    return render(
        request,
        "general/tipo_material_list.html",
        {"tipos": tipos, "form": form},
    )


@login_required
def tipo_material_edit(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk)
    if request.method == "POST":
        form = TipoMaterialForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect("general:tipo_material_list")
    else:
        form = TipoMaterialForm(instance=tipo)

    tipos = TipoMaterial.objects.all()
    return render(
        request,
        "general/tipo_material_list.html",
        {"tipos": tipos, "form": form, "editing": tipo},
    )


@login_required
def tipo_material_delete(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk)
    if request.method == "POST":
        tipo.delete()
        return redirect("general:tipo_material_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": tipo, "cancel_url": "general:tipo_material_list"},
    )


@login_required
def categoria_material_list(request):
    if request.method == "POST":
        form = CategoriaMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:categoria_material_list")
    else:
        form = CategoriaMaterialForm()

    categorias = CategoriaMaterial.objects.select_related("tipo").all()
    return render(
        request,
        "general/categoria_material_list.html",
        {"categorias": categorias, "form": form},
    )


@login_required
def categoria_material_edit(request, pk):
    categoria = get_object_or_404(CategoriaMaterial, pk=pk)
    if request.method == "POST":
        form = CategoriaMaterialForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect("general:categoria_material_list")
    else:
        form = CategoriaMaterialForm(instance=categoria)

    categorias = CategoriaMaterial.objects.select_related("tipo").all()
    return render(
        request,
        "general/categoria_material_list.html",
        {"categorias": categorias, "form": form, "editing": categoria},
    )


@login_required
def categoria_material_delete(request, pk):
    categoria = get_object_or_404(CategoriaMaterial, pk=pk)
    if request.method == "POST":
        categoria.delete()
        return redirect("general:categoria_material_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": categoria, "cancel_url": "general:categoria_material_list"},
    )


@login_required
def subrubro_list(request):
    if request.method == "POST":
        form = SubrubroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:subrubro_list")
    else:
        form = SubrubroForm()

    subrubros = Subrubro.objects.select_related("rubro").all()
    return render(
        request,
        "general/subrubro_list.html",
        {"subrubros": subrubros, "form": form},
    )


@login_required
def subrubro_edit(request, pk):
    subrubro = get_object_or_404(Subrubro, pk=pk)
    if request.method == "POST":
        form = SubrubroForm(request.POST, instance=subrubro)
        if form.is_valid():
            form.save()
            return redirect("general:subrubro_list")
    else:
        form = SubrubroForm(instance=subrubro)

    subrubros = Subrubro.objects.select_related("rubro").all()
    return render(
        request,
        "general/subrubro_list.html",
        {"subrubros": subrubros, "form": form, "editing": subrubro},
    )


@login_required
def subrubro_delete(request, pk):
    subrubro = get_object_or_404(Subrubro, pk=pk)
    if request.method == "POST":
        subrubro.delete()
        return redirect("general:subrubro_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": subrubro, "cancel_url": "general:subrubro_list"},
    )


@login_required
def proveedor_list(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("general:proveedor_list")
    else:
        form = ProveedorForm()

    proveedores = Proveedor.objects.all()
    return render(
        request,
        "general/proveedor_list.html",
        {"proveedores": proveedores, "form": form},
    )


@login_required
def proveedor_edit(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect("general:proveedor_list")
    else:
        form = ProveedorForm(instance=proveedor)

    proveedores = Proveedor.objects.all()
    return render(
        request,
        "general/proveedor_list.html",
        {"proveedores": proveedores, "form": form, "editing": proveedor},
    )


@login_required
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        proveedor.delete()
        return redirect("general:proveedor_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": proveedor, "cancel_url": "general:proveedor_list"},
    )
