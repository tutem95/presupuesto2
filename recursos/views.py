from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ManoDeObraForm, MaterialForm, SubcontratoForm
from .models import HojaPrecioMaterial, HojaPrecios, ManoDeObra, Material, Subcontrato


@login_required
def material_list(request):
    if request.method == "POST":
        form_new = MaterialForm(request.POST)
        if form_new.is_valid():
            form_new.save()
            return redirect("recursos:material_list")
    else:
        form_new = MaterialForm()

    materiales = Material.objects.select_related(
        "proveedor", "tipo", "categoria", "unidad_de_venta"
    ).all()
    return render(
        request,
        "recursos/material_list.html",
        {"materiales": materiales, "form_new": form_new},
    )


@login_required
def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        form_edit = MaterialForm(request.POST, instance=material)
        if form_edit.is_valid():
            form_edit.save()
            return redirect("recursos:material_list")
    else:
        form_edit = MaterialForm(instance=material)

    materiales = Material.objects.select_related(
        "proveedor", "tipo", "categoria", "unidad_de_venta"
    ).all()
    form_new = MaterialForm()
    return render(
        request,
        "recursos/material_list.html",
        {
            "materiales": materiales,
            "form_new": form_new,
            "form_edit": form_edit,
            "editing": material,
        },
    )


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        material.delete()
        return redirect("recursos:material_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": material, "cancel_url": "recursos:material_list"},
    )


@login_required
def material_bulk_update(request):
    """
    Actualiza el precio_unidad_venta de los materiales seleccionados por un porcentaje.
    """
    if request.method != "POST":
        return redirect("recursos:material_list")

    ids = request.POST.getlist("selected_ids")
    porcentaje_str = request.POST.get("porcentaje") or "0"

    if not ids:
        return redirect("recursos:material_list")

    try:
        porcentaje = Decimal(porcentaje_str)
    except InvalidOperation:
        return redirect("recursos:material_list")

    queryset = Material.objects.filter(pk__in=ids)
    Material.actualizar_precios_por_porcentaje(queryset, porcentaje)

    return redirect("recursos:material_list")


@login_required
def hoja_precios_list(request):
    """
    Listado de hojas de precios y creación de nuevas hojas copiando de
    los precios actuales o de otra hoja.
    """
    if request.method == "POST":
        nombre = request.POST.get("nombre") or ""
        origen_tipo = request.POST.get("origen_tipo") or "actual"
        origen_hoja_id = request.POST.get("origen_hoja") or None

        if not nombre.strip():
            return redirect("recursos:hoja_precios_list")

        hoja = HojaPrecios.objects.create(nombre=nombre.strip())

        # Copiar datos según el origen
        if origen_tipo == "actual":
            materiales = Material.objects.all().only(
                "pk",
                "cantidad_por_unidad_venta",
                "precio_unidad_venta",
                "moneda",
            )
            HojaPrecioMaterial.objects.bulk_create(
                [
                    HojaPrecioMaterial(
                        hoja=hoja,
                        material=m,
                        cantidad_por_unidad_venta=m.cantidad_por_unidad_venta,
                        precio_unidad_venta=m.precio_unidad_venta,
                        moneda=m.moneda,
                    )
                    for m in materiales
                ]
            )
        elif origen_tipo == "hoja" and origen_hoja_id:
            origen = get_object_or_404(HojaPrecios, pk=origen_hoja_id)
            hoja.origen = origen
            hoja.save(update_fields=["origen"])
            detalles = origen.detalles.select_related("material").all()
            HojaPrecioMaterial.objects.bulk_create(
                [
                    HojaPrecioMaterial(
                        hoja=hoja,
                        material=d.material,
                        cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                        precio_unidad_venta=d.precio_unidad_venta,
                        moneda=d.moneda,
                    )
                    for d in detalles
                ]
            )

        return redirect("recursos:hoja_precios_list")

    hojas = HojaPrecios.objects.all()
    return render(
        request,
        "recursos/hoja_precios_list.html",
        {"hojas": hojas},
    )


@login_required
def hoja_precios_detalle(request, pk):
    hoja = get_object_or_404(HojaPrecios, pk=pk)
    detalles = hoja.detalles.select_related("material").all()
    return render(
        request,
        "recursos/hoja_precios_detalle.html",
        {"hoja": hoja, "detalles": detalles},
    )


@login_required
def mano_de_obra_list(request):
    if request.method == "POST":
        form = ManoDeObraForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("recursos:mano_de_obra_list")
    else:
        form = ManoDeObraForm()

    items = ManoDeObra.objects.select_related("unidad_de_analisis").all()
    return render(
        request,
        "recursos/mano_de_obra_list.html",
        {"items": items, "form": form},
    )


@login_required
def mano_de_obra_edit(request, pk):
    item = get_object_or_404(ManoDeObra, pk=pk)
    if request.method == "POST":
        form = ManoDeObraForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("recursos:mano_de_obra_list")
    else:
        form = ManoDeObraForm(instance=item)

    items = ManoDeObra.objects.select_related("unidad_de_analisis").all()
    return render(
        request,
        "recursos/mano_de_obra_list.html",
        {"items": items, "form": form, "editing": item},
    )


@login_required
def mano_de_obra_delete(request, pk):
    item = get_object_or_404(ManoDeObra, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("recursos:mano_de_obra_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": item, "cancel_url": "recursos:mano_de_obra_list"},
    )


@login_required
def subcontrato_list(request):
    if request.method == "POST":
        form = SubcontratoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("recursos:subcontrato_list")
    else:
        form = SubcontratoForm()

    subcontratos = Subcontrato.objects.select_related("unidad_de_analisis").all()
    return render(
        request,
        "recursos/subcontrato_list.html",
        {"subcontratos": subcontratos, "form": form},
    )


@login_required
def subcontrato_edit(request, pk):
    subcontrato = get_object_or_404(Subcontrato, pk=pk)
    if request.method == "POST":
        form = SubcontratoForm(request.POST, instance=subcontrato)
        if form.is_valid():
            form.save()
            return redirect("recursos:subcontrato_list")
    else:
        form = SubcontratoForm(instance=subcontrato)

    subcontratos = Subcontrato.objects.select_related("unidad_de_analisis").all()
    return render(
        request,
        "recursos/subcontrato_list.html",
        {"subcontratos": subcontratos, "form": form, "editing": subcontrato},
    )


@login_required
def subcontrato_delete(request, pk):
    subcontrato = get_object_or_404(Subcontrato, pk=pk)
    if request.method == "POST":
        subcontrato.delete()
        return redirect("recursos:subcontrato_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": subcontrato, "cancel_url": "recursos:subcontrato_list"},
    )

