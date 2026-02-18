import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from general.models import CategoriaMaterial

logger = logging.getLogger(__name__)


def _categorias_por_tipo(company):
    """Dict tipo_pk -> [{id, nombre}, ...] para filtrar categorías por tipo en el form de material."""
    result = {}
    categorias = CategoriaMaterial.objects.filter(company=company).order_by(
        "tipo__nombre",
        "nombre",
    ).values("tipo_id", "id", "nombre")
    for cat in categorias:
        tipo_id = str(cat["tipo_id"])
        if tipo_id not in result:
            result[tipo_id] = []
        result[tipo_id].append({"id": cat["id"], "nombre": cat["nombre"]})
    return result


from .forms import (
    HojaPrecioMaterialForm,
    HojaPrecioManoDeObraForm,
    HojaPrecioSubcontratoForm,
    ManoDeObraForm,
    MaterialForm,
    MezclaForm,
    MezclaMaterialForm,
    SubcontratoForm,
    TareaForm,
    TareaRecursoForm,
)
from .models import (
    HojaPrecioMaterial,
    HojaPrecioManoDeObra,
    HojaPrecioSubcontrato,
    HojaPrecios,
    HojaPreciosManoDeObra,
    HojaPreciosSubcontrato,
    Lote,
    ManoDeObra,
    Material,
    Mezcla,
    MezclaMaterial,
    Subcontrato,
    Tarea,
    TareaRecurso,
)


@login_required
def material_list(request):
    company = request.company
    hojas = HojaPrecios.objects.filter(company=company).order_by("-creado_en")
    hoja_id = request.GET.get("hoja")
    editar_id = request.GET.get("editar")
    agregar = request.GET.get("agregar")
    hoja_seleccionada = None
    modo_hoja = False
    editing_hoja = None
    form_hoja_detalle = None

    if hoja_id:
        hoja_seleccionada = get_object_or_404(HojaPrecios, pk=hoja_id, company=company)
        modo_hoja = True
        materiales = list(
            hoja_seleccionada.detalles.select_related(
                "material",
                "material__proveedor",
                "material__tipo",
                "material__categoria",
                "material__unidad_de_venta",
            ).all()
        )

        # Agregar material a la hoja
        if agregar and request.method == "POST":
            material_id = request.POST.get("material_id")
            if material_id:
                material = get_object_or_404(Material, pk=material_id, company=company)
                if not hoja_seleccionada.detalles.filter(material=material).exists():
                    HojaPrecioMaterial.objects.create(
                        hoja=hoja_seleccionada,
                        material=material,
                        cantidad_por_unidad_venta=material.cantidad_por_unidad_venta,
                        precio_unidad_venta=material.precio_unidad_venta,
                        moneda=material.moneda,
                    )
                return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_id}")

        # Editar detalle de hoja
        if editar_id:
            editing_hoja = get_object_or_404(
                HojaPrecioMaterial,
                pk=editar_id,
                hoja=hoja_seleccionada,
            )
            if request.method == "POST":
                form_hoja_detalle = HojaPrecioMaterialForm(
                    request.POST, instance=editing_hoja
                )
                if form_hoja_detalle.is_valid():
                    form_hoja_detalle.save()
                    return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_id}")
            else:
                form_hoja_detalle = HojaPrecioMaterialForm(instance=editing_hoja)

        # Nuevo material desde la hoja: crear en catálogo y agregar a esta hoja
        if request.method == "POST" and not agregar:
            form_new = MaterialForm(request.POST, request=request)
            if form_new.is_valid():
                obj = form_new.save(commit=False)
                obj.company = company
                obj.save()
                HojaPrecioMaterial.objects.create(
                    hoja=hoja_seleccionada,
                    material=obj,
                    cantidad_por_unidad_venta=obj.cantidad_por_unidad_venta,
                    precio_unidad_venta=obj.precio_unidad_venta,
                    moneda=obj.moneda,
                )
                return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_id}")
        else:
            form_new = MaterialForm(request=request)

        materiales_no_en_hoja = None
        if agregar:
            ids_en_hoja = set(
                hoja_seleccionada.detalles.values_list("material_id", flat=True)
            )
            todos = list(
                Material.objects.filter(company=company)
                .select_related("proveedor", "tipo", "categoria", "unidad_de_venta")
            )
            materiales_no_en_hoja = (
                [m for m in todos if m.pk not in ids_en_hoja] if ids_en_hoja else todos
            )

        lote = Lote.objects.filter(hoja_materiales=hoja_seleccionada).first()
        return render(
            request,
            "recursos/material_list.html",
            {
                "materiales": materiales,
                "form_new": form_new,
                "hojas": hojas,
                "hoja_seleccionada": hoja_seleccionada,
                "modo_hoja": modo_hoja,
                "editing_hoja": editing_hoja,
                "form_hoja_detalle": form_hoja_detalle,
                "materiales_no_en_hoja": materiales_no_en_hoja,
                "lote": lote,
                "lote_nav_active": "materiales",
                "categorias_by_tipo": _categorias_por_tipo(company),
            },
        )

    if request.method == "POST":
        form_new = MaterialForm(request.POST, request=request)
        if form_new.is_valid():
            obj = form_new.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("recursos:material_list")
    else:
        form_new = MaterialForm(request=request)

    materiales = Material.objects.filter(company=company).select_related(
        "proveedor", "tipo", "categoria", "unidad_de_venta"
    )
    return render(
        request,
        "recursos/material_list.html",
        {
            "materiales": materiales,
            "form_new": form_new,
            "hojas": hojas,
            "hoja_seleccionada": hoja_seleccionada,
            "modo_hoja": modo_hoja,
            "lote": None,
            "categorias_by_tipo": _categorias_por_tipo(company),
        },
    )


@login_required
def material_edit(request, pk):
    company = request.company
    material = get_object_or_404(Material, pk=pk, company=company)
    if request.method == "POST":
        form_edit = MaterialForm(request.POST, instance=material, request=request)
        if form_edit.is_valid():
            form_edit.save()
            return redirect("recursos:material_list")
    else:
        form_edit = MaterialForm(instance=material, request=request)

    materiales = Material.objects.filter(company=company).select_related(
        "proveedor", "tipo", "categoria", "unidad_de_venta"
    )
    form_new = MaterialForm(request=request)
    return render(
        request,
        "recursos/material_list.html",
        {
            "materiales": materiales,
            "form_new": form_new,
            "form_edit": form_edit,
            "editing": material,
            "categorias_by_tipo": _categorias_por_tipo(company),
        },
    )


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk, company=request.company)
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
    Actualiza el precio_unidad_venta por un porcentaje.
    Sin hoja: materiales del catálogo. Con hoja: detalles de la hoja (HojaPrecioMaterial).
    """
    if request.method != "POST":
        return redirect("recursos:material_list")

    ids = request.POST.getlist("selected_ids")
    porcentaje_str = request.POST.get("porcentaje") or "0"
    hoja_id = request.POST.get("hoja")

    if not ids:
        redirect_url = reverse("recursos:material_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    try:
        porcentaje = Decimal(porcentaje_str)
    except InvalidOperation:
        redirect_url = reverse("recursos:material_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    if hoja_id:
        hoja = get_object_or_404(HojaPrecios, pk=hoja_id, company=request.company)
        queryset = HojaPrecioMaterial.objects.filter(
            hoja=hoja, pk__in=ids
        )
        from django.db.models import F
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
    else:
        queryset = Material.objects.filter(company=request.company, pk__in=ids)
        Material.actualizar_precios_por_porcentaje(queryset, porcentaje)

    redirect_url = reverse("recursos:material_list")
    if hoja_id:
        redirect_url += f"?hoja={hoja_id}"
    return redirect(redirect_url)


@login_required
def hoja_precios_list(request):
    company = request.company
    if request.method == "POST":
        nombre = request.POST.get("nombre") or ""
        origen_tipo = request.POST.get("origen_tipo") or "actual"
        origen_hoja_id = request.POST.get("origen_hoja") or None

        if not nombre.strip():
            return redirect("recursos:hoja_precios_list")

        hoja = HojaPrecios.objects.create(nombre=nombre.strip(), company=company)

        if origen_tipo == "actual":
            materiales = Material.objects.filter(company=company).only(
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
            origen = get_object_or_404(HojaPrecios, pk=origen_hoja_id, company=company)
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

    hojas = HojaPrecios.objects.filter(company=company)
    return render(
        request,
        "recursos/hoja_precios_list.html",
        {"hojas": hojas},
    )


@login_required
def hoja_precios_detalle(request, pk):
    hoja = get_object_or_404(HojaPrecios, pk=pk, company=request.company)
    detalles = hoja.detalles.select_related("material").all()
    return render(
        request,
        "recursos/hoja_precios_detalle.html",
        {"hoja": hoja, "detalles": detalles},
    )


@login_required
def hoja_detalle_edit(request, hoja_pk, detalle_pk):
    """Editar cantidad, precio y moneda de un material en una hoja de precios."""
    hoja = get_object_or_404(HojaPrecios, pk=hoja_pk, company=request.company)
    detalle = get_object_or_404(HojaPrecioMaterial, pk=detalle_pk, hoja=hoja)
    if request.method == "POST":
        form = HojaPrecioMaterialForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_pk}")
    return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_pk}")


@login_required
def hoja_detalle_delete(request, hoja_pk, detalle_pk):
    """Quitar un material de una hoja de precios."""
    hoja = get_object_or_404(HojaPrecios, pk=hoja_pk, company=request.company)
    detalle = get_object_or_404(HojaPrecioMaterial, pk=detalle_pk, hoja=hoja)
    if request.method == "POST":
        detalle.delete()
        return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_pk}")
    return redirect(f"{reverse('recursos:material_list')}?hoja={hoja_pk}")


@login_required
def mano_de_obra_list(request):
    company = request.company
    hojas = HojaPreciosManoDeObra.objects.filter(company=company).order_by("-creado_en")
    hoja_id = request.GET.get("hoja")
    editar_id = request.GET.get("editar")
    agregar = request.GET.get("agregar")
    hoja_seleccionada = None
    modo_hoja = False
    editing_hoja = None
    form_hoja_detalle = None

    if hoja_id:
        hoja_seleccionada = get_object_or_404(
            HojaPreciosManoDeObra, pk=hoja_id, company=company
        )
        modo_hoja = True
        items = list(
            hoja_seleccionada.detalles.select_related(
                "mano_de_obra",
                "mano_de_obra__rubro",
                "mano_de_obra__subrubro",
                "mano_de_obra__equipo",
                "mano_de_obra__ref_equipo",
                "mano_de_obra__unidad_de_venta",
            ).all()
        )

        if agregar and request.method == "POST":
            md_id = request.POST.get("mano_de_obra_id")
            if md_id:
                md = get_object_or_404(ManoDeObra, pk=md_id, company=company)
                if not hoja_seleccionada.detalles.filter(mano_de_obra=md).exists():
                    HojaPrecioManoDeObra.objects.create(
                        hoja=hoja_seleccionada,
                        mano_de_obra=md,
                        cantidad_por_unidad_venta=md.cantidad_por_unidad_venta,
                        precio_unidad_venta=md.precio_unidad_venta,
                    )
                return redirect(f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_id}")

        if editar_id:
            editing_hoja = get_object_or_404(
                HojaPrecioManoDeObra,
                pk=editar_id,
                hoja=hoja_seleccionada,
            )
            if request.method == "POST":
                form_hoja_detalle = HojaPrecioManoDeObraForm(
                    request.POST, instance=editing_hoja
                )
                if form_hoja_detalle.is_valid():
                    form_hoja_detalle.save()
                    return redirect(
                        f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_id}"
                    )
            else:
                form_hoja_detalle = HojaPrecioManoDeObraForm(
                    instance=editing_hoja
                )

        # Nuevo puesto desde la hoja: crear en catálogo y agregar a esta hoja
        if request.method == "POST" and not agregar:
            form_new = ManoDeObraForm(request.POST, request=request)
            if form_new.is_valid():
                obj = form_new.save(commit=False)
                obj.company = company
                obj.save()
                HojaPrecioManoDeObra.objects.create(
                    hoja=hoja_seleccionada,
                    mano_de_obra=obj,
                    cantidad_por_unidad_venta=obj.cantidad_por_unidad_venta,
                    precio_unidad_venta=obj.precio_unidad_venta,
                )
                return redirect(f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_id}")
        else:
            form_new = ManoDeObraForm(request=request)

        items_no_en_hoja = None
        if agregar:
            ids_en_hoja = set(
                hoja_seleccionada.detalles.values_list("mano_de_obra_id", flat=True)
            )
            todos = list(
                ManoDeObra.objects.filter(company=company).select_related(
                    "rubro", "subrubro", "equipo", "ref_equipo", "unidad_de_venta"
                )
            )
            items_no_en_hoja = (
                [m for m in todos if m.pk not in ids_en_hoja] if ids_en_hoja else todos
            )

        lote = Lote.objects.filter(hoja_mano_de_obra=hoja_seleccionada).first()
        return render(
            request,
            "recursos/mano_de_obra_list.html",
            {
                "items": items,
                "form_new": form_new,
                "hojas": hojas,
                "hoja_seleccionada": hoja_seleccionada,
                "modo_hoja": modo_hoja,
                "editing_hoja": editing_hoja,
                "form_hoja_detalle": form_hoja_detalle,
                "items_no_en_hoja": items_no_en_hoja,
                "lote": lote,
                "lote_nav_active": "mano_obra",
            },
        )

    if request.method == "POST":
        form_new = ManoDeObraForm(request.POST, request=request)
        if form_new.is_valid():
            obj = form_new.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("recursos:mano_de_obra_list")
    else:
        form_new = ManoDeObraForm(request=request)

    items = ManoDeObra.objects.filter(company=company).select_related(
        "rubro", "subrubro", "equipo", "ref_equipo", "unidad_de_venta"
    )
    return render(
        request,
        "recursos/mano_de_obra_list.html",
        {
            "items": items,
            "form_new": form_new,
            "hojas": hojas,
            "hoja_seleccionada": hoja_seleccionada,
            "modo_hoja": modo_hoja,
            "editing": None,
            "lote": None,
        },
    )


@login_required
def mano_de_obra_edit(request, pk):
    company = request.company
    item = get_object_or_404(ManoDeObra, pk=pk, company=company)
    if request.method == "POST":
        form = ManoDeObraForm(request.POST, instance=item, request=request)
        if form.is_valid():
            form.save()
            return redirect("recursos:mano_de_obra_list")
    else:
        form = ManoDeObraForm(instance=item, request=request)

    items = ManoDeObra.objects.filter(company=company).select_related(
        "rubro", "subrubro", "equipo", "ref_equipo", "unidad_de_venta"
    )
    form_new = ManoDeObraForm(request=request)
    hojas = HojaPreciosManoDeObra.objects.filter(company=company).order_by("-creado_en")
    return render(
        request,
        "recursos/mano_de_obra_list.html",
        {
            "items": items,
            "form_new": form_new,
            "form_edit": form,
            "editing": item,
            "hojas": hojas,
            "hoja_seleccionada": None,
            "modo_hoja": False,
            "lote": None,
        },
    )


@login_required
def mano_de_obra_delete(request, pk):
    item = get_object_or_404(ManoDeObra, pk=pk, company=request.company)
    if request.method == "POST":
        item.delete()
        return redirect("recursos:mano_de_obra_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": item, "cancel_url": "recursos:mano_de_obra_list"},
    )


@login_required
def mano_de_obra_bulk_update(request):
    """
    Actualiza precio_unidad_venta por porcentaje.
    Sin hoja: mano de obra del catálogo. Con hoja: detalles de la hoja (HojaPrecioManoDeObra).
    """
    if request.method != "POST":
        return redirect("recursos:mano_de_obra_list")

    ids = request.POST.getlist("selected_ids")
    porcentaje_str = request.POST.get("porcentaje") or "0"
    hoja_id = request.POST.get("hoja")

    if not ids:
        redirect_url = reverse("recursos:mano_de_obra_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    try:
        porcentaje = Decimal(porcentaje_str)
    except InvalidOperation:
        redirect_url = reverse("recursos:mano_de_obra_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    if hoja_id:
        hoja = get_object_or_404(HojaPreciosManoDeObra, pk=hoja_id, company=request.company)
        queryset = HojaPrecioManoDeObra.objects.filter(hoja=hoja, pk__in=ids)
        from django.db.models import F
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
    else:
        queryset = ManoDeObra.objects.filter(company=request.company, pk__in=ids)
        ManoDeObra.actualizar_precios_por_porcentaje(queryset, porcentaje)

    redirect_url = reverse("recursos:mano_de_obra_list")
    if hoja_id:
        redirect_url += f"?hoja={hoja_id}"
    return redirect(redirect_url)


@login_required
def hoja_mano_de_obra_list(request):
    company = request.company
    if request.method == "POST":
        nombre = request.POST.get("nombre") or ""
        origen_tipo = request.POST.get("origen_tipo") or "actual"
        origen_hoja_id = request.POST.get("origen_hoja") or None

        if not nombre.strip():
            return redirect("recursos:hoja_mano_de_obra_list")

        hoja = HojaPreciosManoDeObra.objects.create(
            nombre=nombre.strip(), company=company
        )

        if origen_tipo == "actual":
            items = ManoDeObra.objects.filter(company=company).only(
                "pk",
                "cantidad_por_unidad_venta",
                "precio_unidad_venta",
            )
            HojaPrecioManoDeObra.objects.bulk_create(
                [
                    HojaPrecioManoDeObra(
                        hoja=hoja,
                        mano_de_obra=md,
                        cantidad_por_unidad_venta=md.cantidad_por_unidad_venta,
                        precio_unidad_venta=md.precio_unidad_venta,
                    )
                    for md in items
                ]
            )
        elif origen_tipo == "hoja" and origen_hoja_id:
            origen = get_object_or_404(
                HojaPreciosManoDeObra, pk=origen_hoja_id, company=company
            )
            hoja.origen = origen
            hoja.save(update_fields=["origen"])
            detalles = origen.detalles.select_related("mano_de_obra").all()
            HojaPrecioManoDeObra.objects.bulk_create(
                [
                    HojaPrecioManoDeObra(
                        hoja=hoja,
                        mano_de_obra=d.mano_de_obra,
                        cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                        precio_unidad_venta=d.precio_unidad_venta,
                    )
                    for d in detalles
                ]
            )

        return redirect("recursos:hoja_mano_de_obra_list")

    hojas = HojaPreciosManoDeObra.objects.filter(company=company)
    return render(
        request,
        "recursos/hoja_mano_de_obra_list.html",
        {"hojas": hojas},
    )


@login_required
def hoja_mano_de_obra_detalle(request, pk):
    hoja = get_object_or_404(HojaPreciosManoDeObra, pk=pk, company=request.company)
    detalles = hoja.detalles.select_related(
        "mano_de_obra",
        "mano_de_obra__rubro",
        "mano_de_obra__subrubro",
        "mano_de_obra__equipo",
        "mano_de_obra__ref_equipo",
        "mano_de_obra__unidad_de_venta",
    ).all()
    lote = Lote.objects.filter(hoja_mano_de_obra=hoja).first()
    return render(
        request,
        "recursos/hoja_mano_de_obra_detalle.html",
        {"hoja": hoja, "detalles": detalles, "lote": lote},
    )


@login_required
def hoja_mano_de_obra_detalle_edit(request, hoja_pk, detalle_pk):
    hoja = get_object_or_404(
        HojaPreciosManoDeObra, pk=hoja_pk, company=request.company
    )
    detalle = get_object_or_404(
        HojaPrecioManoDeObra, pk=detalle_pk, hoja=hoja
    )
    if request.method == "POST":
        form = HojaPrecioManoDeObraForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            return redirect(
                f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_pk}"
            )
    return redirect(f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_pk}")


@login_required
def hoja_mano_de_obra_detalle_delete(request, hoja_pk, detalle_pk):
    hoja = get_object_or_404(
        HojaPreciosManoDeObra, pk=hoja_pk, company=request.company
    )
    detalle = get_object_or_404(
        HojaPrecioManoDeObra, pk=detalle_pk, hoja=hoja
    )
    if request.method == "POST":
        detalle.delete()
        return redirect(f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_pk}")
    return redirect(f"{reverse('recursos:mano_de_obra_list')}?hoja={hoja_pk}")


@login_required
def mezcla_list(request):
    company = request.company
    hojas = HojaPrecios.objects.filter(company=company).order_by("-creado_en")
    hoja_id = request.GET.get("hoja")
    hoja_seleccionada = None

    if hoja_id:
        hoja_seleccionada = get_object_or_404(HojaPrecios, pk=hoja_id, company=company)
        mezclas = Mezcla.objects.filter(company=company, hoja=hoja_seleccionada)
    else:
        mezclas = Mezcla.objects.filter(company=company, hoja__isnull=True)

    mezclas = mezclas.select_related("unidad_de_mezcla", "hoja").order_by("nombre")

    if request.method == "POST":
        form = MezclaForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.hoja = hoja_seleccionada
            obj.save()
            return redirect("recursos:mezcla_detalle", pk=obj.pk)
    else:
        form = MezclaForm(request=request, initial={"hoja": hoja_seleccionada})

    lote = Lote.objects.filter(hoja_materiales=hoja_seleccionada).first() if hoja_seleccionada else None
    return render(
        request,
        "recursos/mezcla_list.html",
        {
            "mezclas": mezclas,
            "form": form,
            "hojas": hojas,
            "hoja_seleccionada": hoja_seleccionada,
            "lote": lote,
            "lote_nav_active": "mezclas" if lote else None,
        },
    )


@login_required
def mezcla_detalle(request, pk):
    mezcla = get_object_or_404(Mezcla, pk=pk, company=request.company)
    detalles = mezcla.detalles.select_related(
        "material",
        "material__proveedor",
        "material__unidad_de_venta",
    ).all()
    total = sum(d.costo_en_hoja() for d in detalles)
    return render(
        request,
        "recursos/mezcla_detalle.html",
        {"mezcla": mezcla, "detalles": detalles, "total": total},
    )


@login_required
def mezcla_edit(request, pk):
    mezcla = get_object_or_404(Mezcla, pk=pk, company=request.company)
    if request.method == "POST":
        form = MezclaForm(request.POST, instance=mezcla, request=request)
        if form.is_valid():
            form.save()
            return redirect("recursos:mezcla_detalle", pk=mezcla.pk)
    else:
        form = MezclaForm(instance=mezcla, request=request)

    return render(
        request,
        "recursos/mezcla_form.html",
        {"form": form, "mezcla": mezcla, "editing": True},
    )


@login_required
def mezcla_delete(request, pk):
    mezcla = get_object_or_404(Mezcla, pk=pk, company=request.company)
    if request.method == "POST":
        mezcla.delete()
        return redirect("recursos:mezcla_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": mezcla, "cancel_url": "recursos:mezcla_list"},
    )


@login_required
def mezcla_material_add(request, pk):
    mezcla = get_object_or_404(Mezcla, pk=pk, company=request.company)
    if request.method == "POST":
        form = MezclaMaterialForm(request.POST, mezcla=mezcla)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mezcla = mezcla
            obj.save()
            return redirect("recursos:mezcla_detalle", pk=mezcla.pk)
    else:
        form = MezclaMaterialForm(mezcla=mezcla)

    return render(
        request,
        "recursos/mezcla_material_form.html",
        {"form": form, "mezcla": mezcla},
    )


@login_required
def mezcla_material_delete(request, mezcla_pk, detalle_pk):
    mezcla = get_object_or_404(Mezcla, pk=mezcla_pk, company=request.company)
    detalle = get_object_or_404(MezclaMaterial, pk=detalle_pk, mezcla=mezcla)
    if request.method == "POST":
        detalle.delete()
        return redirect("recursos:mezcla_detalle", pk=mezcla.pk)
    return redirect("recursos:mezcla_detalle", pk=mezcla.pk)


def _copy_hoja_materiales_desde_origen(hoja_origen, nombre, company):
    """Copia una hoja de materiales desde otra hoja o desde precios actuales."""
    hoja = HojaPrecios.objects.create(nombre=nombre, company=company)
    if hoja_origen:
        hoja.origen = hoja_origen
        hoja.save()
        for d in hoja_origen.detalles.select_related("material").all():
            HojaPrecioMaterial.objects.create(
                hoja=hoja,
                material=d.material,
                cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                precio_unidad_venta=d.precio_unidad_venta,
                moneda=d.moneda,
            )
    else:
        for m in Material.objects.filter(company=company):
            HojaPrecioMaterial.objects.create(
                hoja=hoja,
                material=m,
                cantidad_por_unidad_venta=m.cantidad_por_unidad_venta,
                precio_unidad_venta=m.precio_unidad_venta,
                moneda=m.moneda,
            )
    return hoja


def _create_hoja_materiales_vacia(nombre, company):
    """Crea una hoja de materiales vacía (sin copiar)."""
    return HojaPrecios.objects.create(nombre=nombre, company=company)


def _copy_hoja_mo_desde_origen(hoja_origen, nombre, company):
    """Copia hoja de mano de obra."""
    hoja = HojaPreciosManoDeObra.objects.create(nombre=nombre, company=company)
    if hoja_origen:
        hoja.origen = hoja_origen
        hoja.save()
        for d in hoja_origen.detalles.select_related("mano_de_obra").all():
            HojaPrecioManoDeObra.objects.create(
                hoja=hoja,
                mano_de_obra=d.mano_de_obra,
                cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                precio_unidad_venta=d.precio_unidad_venta,
            )
    else:
        for md in ManoDeObra.objects.filter(company=company):
            HojaPrecioManoDeObra.objects.create(
                hoja=hoja,
                mano_de_obra=md,
                cantidad_por_unidad_venta=md.cantidad_por_unidad_venta,
                precio_unidad_venta=md.precio_unidad_venta,
            )
    return hoja


def _create_hoja_mo_vacia(nombre, company):
    """Crea una hoja de mano de obra vacía (sin copiar)."""
    return HojaPreciosManoDeObra.objects.create(nombre=nombre, company=company)


def _copy_hoja_subcontratos_desde_origen(hoja_origen, nombre, company):
    """Copia hoja de subcontratos."""
    hoja = HojaPreciosSubcontrato.objects.create(nombre=nombre, company=company)
    if hoja_origen:
        hoja.origen = hoja_origen
        hoja.save()
        for d in hoja_origen.detalles.select_related("subcontrato").all():
            HojaPrecioSubcontrato.objects.create(
                hoja=hoja,
                subcontrato=d.subcontrato,
                cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                precio_unidad_venta=d.precio_unidad_venta,
                moneda=d.moneda,
            )
    else:
        for s in Subcontrato.objects.filter(company=company):
            HojaPrecioSubcontrato.objects.create(
                hoja=hoja,
                subcontrato=s,
                cantidad_por_unidad_venta=s.cantidad_por_unidad_venta,
                precio_unidad_venta=s.precio_unidad_venta,
                moneda=s.moneda,
            )
    return hoja


def _create_hoja_subcontratos_vacia(nombre, company):
    """Crea una hoja de subcontratos vacía (sin copiar)."""
    return HojaPreciosSubcontrato.objects.create(nombre=nombre, company=company)


def _copy_mezclas_desde_hoja(hoja_origen, hoja_nueva, company):
    """Copia mezclas que usan hoja_origen, creando nuevas que usan hoja_nueva."""
    if not hoja_origen:
        return
    for mezcla in Mezcla.objects.filter(company=company, hoja=hoja_origen).prefetch_related("detalles"):
        nueva_mezcla = Mezcla.objects.create(
            nombre=mezcla.nombre,
            company=company,
            unidad_de_mezcla=mezcla.unidad_de_mezcla,
            hoja=hoja_nueva,
        )
        for det in mezcla.detalles.all():
            MezclaMaterial.objects.create(
                mezcla=nueva_mezcla,
                material=det.material,
                cantidad=det.cantidad,
            )


def _copy_tareas_desde_lote(lote_origen, lote_nuevo, company):
    """Copia tareas y recursos desde un lote a otro."""
    if not lote_origen:
        return
    hoja_nueva = lote_nuevo.hoja_materiales
    for t in Tarea.objects.filter(lote=lote_origen, company=company).select_related("rubro", "subrubro"):
        nueva_t = Tarea.objects.create(
            nombre=t.nombre,
            company=company,
            rubro=t.rubro,
            subrubro=t.subrubro,
            lote=lote_nuevo,
        )
        for r in t.recursos.all():
            mezcla_nueva = None
            if r.mezcla_id:
                # Buscar la mezcla copiada (misma nombre, hoja del nuevo lote)
                mezcla_nueva = Mezcla.objects.filter(
                    company=company, nombre=r.mezcla.nombre, hoja=hoja_nueva
                ).first()
            TareaRecurso.objects.create(
                tarea=nueva_t,
                material=r.material,
                mano_de_obra=r.mano_de_obra,
                subcontrato=r.subcontrato,
                mezcla=mezcla_nueva,
                cantidad=r.cantidad,
            )


@login_required
def lote_list(request):
    company = request.company
    lotes = Lote.objects.filter(company=company).select_related(
        "hoja_materiales", "hoja_mano_de_obra", "hoja_subcontratos"
    ).order_by("-creado_en")
    return render(request, "recursos/lote_list.html", {"lotes": lotes})


@login_required
def lote_create(request):
    """Pantalla para agregar nuevo lote. --Sin copiar-- por defecto."""
    company = request.company
    lotes = Lote.objects.filter(company=company).order_by("-creado_en")

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        origen_mat = request.POST.get("origen_materiales")  # "" o lote pk
        origen_mo = request.POST.get("origen_mo")
        origen_sub = request.POST.get("origen_subcontratos")
        origen_mezclas = request.POST.get("origen_mezclas")
        origen_maestro = request.POST.get("origen_maestro")

        if not nombre:
            return redirect("recursos:lote_create")

        try:
            with transaction.atomic():
                hoja_mat_origen = None
                hoja_mo_origen = None
                hoja_sub_origen = None
                hoja_mezclas_origen = None
                lote_maestro_origen = None

                if origen_mat:
                    lote_mat = get_object_or_404(Lote, pk=origen_mat, company=company)
                    hoja_mat_origen = lote_mat.hoja_materiales
                if origen_mo:
                    lote_mo = get_object_or_404(Lote, pk=origen_mo, company=company)
                    hoja_mo_origen = lote_mo.hoja_mano_de_obra
                if origen_sub:
                    lote_sub = get_object_or_404(Lote, pk=origen_sub, company=company)
                    hoja_sub_origen = lote_sub.hoja_subcontratos
                if origen_mezclas:
                    lote_mez = get_object_or_404(
                        Lote, pk=origen_mezclas, company=company
                    )
                    hoja_mezclas_origen = lote_mez.hoja_materiales
                if origen_maestro:
                    lote_maestro_origen = get_object_or_404(
                        Lote, pk=origen_maestro, company=company
                    )

                if hoja_mat_origen:
                    hoja_mat = _copy_hoja_materiales_desde_origen(
                        hoja_mat_origen,
                        nombre,
                        company,
                    )
                else:
                    hoja_mat = _create_hoja_materiales_vacia(nombre, company)
                if hoja_mo_origen:
                    hoja_mo = _copy_hoja_mo_desde_origen(hoja_mo_origen, nombre, company)
                else:
                    hoja_mo = _create_hoja_mo_vacia(nombre, company)
                if hoja_sub_origen:
                    hoja_sub = _copy_hoja_subcontratos_desde_origen(
                        hoja_sub_origen,
                        nombre,
                        company,
                    )
                else:
                    hoja_sub = _create_hoja_subcontratos_vacia(nombre, company)

                _copy_mezclas_desde_hoja(hoja_mezclas_origen, hoja_mat, company)

                lote_nuevo = Lote.objects.create(
                    nombre=nombre,
                    company=company,
                    hoja_materiales=hoja_mat,
                    hoja_mano_de_obra=hoja_mo,
                    hoja_subcontratos=hoja_sub,
                )
                _copy_tareas_desde_lote(lote_maestro_origen, lote_nuevo, company)
        except Exception:
            logger.exception(
                "Error creando lote '%s' para company_id=%s",
                nombre,
                getattr(company, "pk", None),
            )
            messages.error(
                request,
                "No se pudo crear el lote. Revisá los datos de origen y volvé a intentar.",
            )
            return redirect("recursos:lote_create")

        return redirect("tareas")

    return render(request, "recursos/lote_form.html", {"lotes": lotes})


@login_required
def lote_edit(request, pk):
    """Editar el nombre del lote."""
    lote = get_object_or_404(Lote, pk=pk, company=request.company)
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        if nombre:
            lote.nombre = nombre
            lote.save()
            return redirect("recursos:lote_detalle", pk=lote.pk)
    return render(
        request,
        "recursos/lote_edit.html",
        {"lote": lote},
    )


@login_required
def lote_detalle(request, pk):
    from general.models import TipoDolar

    lote = get_object_or_404(Lote.objects.select_related("tipo_dolar"), pk=pk, company=request.company)
    tipos_dolar = TipoDolar.objects.filter(company=request.company).order_by("nombre")

    if request.method == "POST" and request.POST.get("form") == "dolar":
        tipo_id = request.POST.get("tipo_dolar") or None
        fecha_str = (request.POST.get("fecha_dolar") or "").strip() or None
        try:
            if tipo_id:
                tipo_pk = int(tipo_id)
                if tipos_dolar.filter(pk=tipo_pk).exists():
                    lote.tipo_dolar_id = tipo_pk
                else:
                    messages.error(
                        request,
                        "El tipo de dólar seleccionado no pertenece a la empresa activa.",
                    )
            else:
                lote.tipo_dolar_id = None
            if fecha_str:
                lote.fecha_dolar = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            else:
                lote.fecha_dolar = None
            lote.save()
        except (ValueError, TypeError):
            messages.error(
                request,
                "La fecha de cotización no es válida. Usá el formato correcto.",
            )
        return redirect("recursos:lote_detalle", pk=lote.pk)

    return render(
        request,
        "recursos/lote_detalle.html",
        {"lote": lote, "tipos_dolar": tipos_dolar},
    )


@login_required
def tarea_list(request, lote_pk):
    lote = get_object_or_404(Lote.objects.select_related("tipo_dolar"), pk=lote_pk, company=request.company)
    tareas = lote.tareas.select_related("rubro", "subrubro").order_by(
        "rubro__nombre", "subrubro__nombre", "nombre"
    )
    return render(
        request,
        "recursos/tarea_list.html",
        {"lote": lote, "tareas": tareas, "lote_nav_active": "maestro_tareas"},
    )


@login_required
def tarea_detalle(request, lote_pk, pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    tarea = get_object_or_404(Tarea, pk=pk, lote=lote, company=request.company)
    recursos = tarea.recursos.select_related(
        "material", "material__proveedor", "material__unidad_de_venta",
        "mano_de_obra", "mano_de_obra__unidad_de_venta", "mano_de_obra__equipo", "mano_de_obra__ref_equipo",
        "subcontrato", "subcontrato__proveedor", "subcontrato__unidad_de_venta",
        "mezcla", "mezcla__unidad_de_mezcla",
    ).all()
    total = sum(r.costo_total() for r in recursos)
    total_usd = tarea.precio_total_usd()
    return render(
        request,
        "recursos/tarea_detalle.html",
        {"lote": lote, "tarea": tarea, "recursos": recursos, "total": total, "total_usd": total_usd, "lote_nav_active": "maestro_tareas"},
    )


def _subrubros_by_rubro(company):
    """Dict rubro_id -> [(id, nombre), ...] para cascada rubro->subrubro."""
    from general.models import Subrubro
    subrubros = Subrubro.objects.filter(company=company).select_related("rubro").order_by("rubro__nombre", "nombre")
    result = {}
    for s in subrubros:
        rid = str(s.rubro_id)
        if rid not in result:
            result[rid] = []
        result[rid].append({"id": s.pk, "nombre": s.nombre})
    return result


@login_required
def tarea_create(request, lote_pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    if request.method == "POST":
        form = TareaForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.company
            obj.lote = lote
            obj.save()
            return redirect("recursos:tarea_detalle", lote_pk=lote.pk, pk=obj.pk)
    else:
        form = TareaForm(request=request)

    subrubros_by_rubro = _subrubros_by_rubro(request.company)
    return render(
        request,
        "recursos/tarea_form.html",
        {"form": form, "lote": lote, "editing": False, "subrubros_by_rubro": subrubros_by_rubro, "lote_nav_active": "maestro_tareas"},
    )


@login_required
def tarea_edit(request, lote_pk, pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    tarea = get_object_or_404(Tarea, pk=pk, lote=lote, company=request.company)
    if request.method == "POST":
        form = TareaForm(request.POST, instance=tarea, request=request)
        if form.is_valid():
            form.save()
            return redirect("recursos:tarea_detalle", lote_pk=lote.pk, pk=tarea.pk)
    else:
        form = TareaForm(instance=tarea, request=request)

    subrubros_by_rubro = _subrubros_by_rubro(request.company)
    return render(
        request,
        "recursos/tarea_form.html",
        {"form": form, "lote": lote, "tarea": tarea, "editing": True, "subrubros_by_rubro": subrubros_by_rubro, "lote_nav_active": "maestro_tareas"},
    )


@login_required
def tarea_delete(request, lote_pk, pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    tarea = get_object_or_404(Tarea, pk=pk, lote=lote, company=request.company)
    if request.method == "POST":
        tarea.delete()
        return redirect("recursos:tarea_list", lote_pk=lote.pk)
    return render(
        request,
        "general/confirm_delete.html",
        {
            "object": tarea,
            "cancel_url": "recursos:tarea_list",
            "cancel_link": reverse("recursos:tarea_list", kwargs={"lote_pk": lote.pk}),
        },
    )


@login_required
def tarea_recurso_add(request, lote_pk, tarea_pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    tarea = get_object_or_404(Tarea, pk=tarea_pk, lote=lote, company=request.company)
    if request.method == "POST":
        form = TareaRecursoForm(request.POST, lote=lote)
        if form.is_valid():
            tipo = form.cleaned_data["tipo"]
            cantidad = form.cleaned_data["cantidad"]
            if tipo == "material":
                TareaRecurso.objects.create(tarea=tarea, material=form.cleaned_data["material"], cantidad=cantidad)
            elif tipo == "mano_de_obra":
                TareaRecurso.objects.create(tarea=tarea, mano_de_obra=form.cleaned_data["mano_de_obra"], cantidad=cantidad)
            elif tipo == "subcontrato":
                TareaRecurso.objects.create(tarea=tarea, subcontrato=form.cleaned_data["subcontrato"], cantidad=cantidad)
            elif tipo == "mezcla":
                TareaRecurso.objects.create(tarea=tarea, mezcla=form.cleaned_data["mezcla"], cantidad=cantidad)
            return redirect("recursos:tarea_detalle", lote_pk=lote.pk, pk=tarea.pk)
    else:
        form = TareaRecursoForm(lote=lote)

    return render(
        request,
        "recursos/tarea_recurso_form.html",
        {"form": form, "lote": lote, "tarea": tarea, "lote_nav_active": "maestro_tareas"},
    )


@login_required
def tarea_recurso_delete(request, lote_pk, tarea_pk, recurso_pk):
    lote = get_object_or_404(Lote, pk=lote_pk, company=request.company)
    tarea = get_object_or_404(Tarea, pk=tarea_pk, lote=lote, company=request.company)
    recurso = get_object_or_404(TareaRecurso, pk=recurso_pk, tarea=tarea)
    if request.method == "POST":
        recurso.delete()
        return redirect("recursos:tarea_detalle", lote_pk=lote.pk, pk=tarea.pk)
    return redirect("recursos:tarea_detalle", lote_pk=lote.pk, pk=tarea.pk)


@login_required
def subcontrato_list(request):
    company = request.company
    hojas = HojaPreciosSubcontrato.objects.filter(company=company).order_by("-creado_en")
    hoja_id = request.GET.get("hoja")
    editar_id = request.GET.get("editar")
    agregar = request.GET.get("agregar")
    hoja_seleccionada = None
    modo_hoja = False
    editing_hoja = None
    form_hoja_detalle = None

    if hoja_id:
        hoja_seleccionada = get_object_or_404(
            HojaPreciosSubcontrato, pk=hoja_id, company=company
        )
        modo_hoja = True
        subcontratos = list(
            hoja_seleccionada.detalles.select_related(
                "subcontrato",
                "subcontrato__rubro",
                "subcontrato__subrubro",
                "subcontrato__proveedor",
                "subcontrato__unidad_de_venta",
            ).all()
        )

        if agregar and request.method == "POST":
            subcontrato_id = request.POST.get("subcontrato_id")
            if subcontrato_id:
                subc = get_object_or_404(
                    Subcontrato, pk=subcontrato_id, company=company
                )
                if not hoja_seleccionada.detalles.filter(subcontrato=subc).exists():
                    HojaPrecioSubcontrato.objects.create(
                        hoja=hoja_seleccionada,
                        subcontrato=subc,
                        cantidad_por_unidad_venta=subc.cantidad_por_unidad_venta,
                        precio_unidad_venta=subc.precio_unidad_venta,
                        moneda=subc.moneda,
                    )
                return redirect(f"{reverse('recursos:subcontrato_list')}?hoja={hoja_id}")

        if editar_id:
            editing_hoja = get_object_or_404(
                HojaPrecioSubcontrato,
                pk=editar_id,
                hoja=hoja_seleccionada,
            )
            if request.method == "POST":
                form_hoja_detalle = HojaPrecioSubcontratoForm(
                    request.POST, instance=editing_hoja
                )
                if form_hoja_detalle.is_valid():
                    form_hoja_detalle.save()
                    return redirect(
                        f"{reverse('recursos:subcontrato_list')}?hoja={hoja_id}"
                    )
            else:
                form_hoja_detalle = HojaPrecioSubcontratoForm(
                    instance=editing_hoja
                )

        # Nuevo subcontrato desde la hoja: crear en catálogo y agregar a esta hoja
        if request.method == "POST" and not agregar:
            form_new = SubcontratoForm(request.POST, request=request)
            if form_new.is_valid():
                obj = form_new.save(commit=False)
                obj.company = company
                obj.save()
                HojaPrecioSubcontrato.objects.create(
                    hoja=hoja_seleccionada,
                    subcontrato=obj,
                    cantidad_por_unidad_venta=obj.cantidad_por_unidad_venta,
                    precio_unidad_venta=obj.precio_unidad_venta,
                    moneda=obj.moneda,
                )
                return redirect(f"{reverse('recursos:subcontrato_list')}?hoja={hoja_id}")
        else:
            form_new = SubcontratoForm(request=request)

        subcontratos_no_en_hoja = None
        if agregar:
            ids_en_hoja = set(
                hoja_seleccionada.detalles.values_list("subcontrato_id", flat=True)
            )
            todos = list(
                Subcontrato.objects.filter(company=company).select_related(
                    "rubro", "subrubro", "proveedor", "unidad_de_venta"
                )
            )
            subcontratos_no_en_hoja = (
                [s for s in todos if s.pk not in ids_en_hoja] if ids_en_hoja else todos
            )

        lote = Lote.objects.filter(hoja_subcontratos=hoja_seleccionada).first()
        return render(
            request,
            "recursos/subcontrato_list.html",
            {
                "subcontratos": subcontratos,
                "form_new": form_new,
                "hojas": hojas,
                "hoja_seleccionada": hoja_seleccionada,
                "modo_hoja": modo_hoja,
                "editing_hoja": editing_hoja,
                "form_hoja_detalle": form_hoja_detalle,
                "subcontratos_no_en_hoja": subcontratos_no_en_hoja,
                "lote": lote,
                "lote_nav_active": "subcontratos",
            },
        )

    if request.method == "POST":
        form_new = SubcontratoForm(request.POST, request=request)
        if form_new.is_valid():
            obj = form_new.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("recursos:subcontrato_list")
    else:
        form_new = SubcontratoForm(request=request)

    subcontratos = Subcontrato.objects.filter(company=company).select_related(
        "rubro", "subrubro", "proveedor", "unidad_de_venta"
    )
    return render(
        request,
        "recursos/subcontrato_list.html",
        {
            "subcontratos": subcontratos,
            "form_new": form_new,
            "hojas": hojas,
            "hoja_seleccionada": hoja_seleccionada,
            "modo_hoja": modo_hoja,
            "editing": None,
            "lote": None,
        },
    )


@login_required
def subcontrato_edit(request, pk):
    company = request.company
    subcontrato = get_object_or_404(Subcontrato, pk=pk, company=company)
    if request.method == "POST":
        form = SubcontratoForm(request.POST, instance=subcontrato, request=request)
        if form.is_valid():
            form.save()
            return redirect("recursos:subcontrato_list")
    else:
        form = SubcontratoForm(instance=subcontrato, request=request)

    subcontratos = Subcontrato.objects.filter(company=company).select_related(
        "rubro", "subrubro", "proveedor", "unidad_de_venta"
    )
    form_new = SubcontratoForm(request=request)
    hojas = HojaPreciosSubcontrato.objects.filter(company=company).order_by("-creado_en")
    return render(
        request,
        "recursos/subcontrato_list.html",
        {
            "subcontratos": subcontratos,
            "form_new": form_new,
            "form_edit": form,
            "editing": subcontrato,
            "hojas": hojas,
            "hoja_seleccionada": None,
            "modo_hoja": False,
            "lote": None,
        },
    )


@login_required
def subcontrato_delete(request, pk):
    subcontrato = get_object_or_404(Subcontrato, pk=pk, company=request.company)
    if request.method == "POST":
        subcontrato.delete()
        return redirect("recursos:subcontrato_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": subcontrato, "cancel_url": "recursos:subcontrato_list"},
    )


@login_required
def subcontrato_bulk_update(request):
    """
    Actualiza precio_unidad_venta por porcentaje.
    Sin hoja: subcontratos del catálogo. Con hoja: detalles de la hoja (HojaPrecioSubcontrato).
    """
    if request.method != "POST":
        return redirect("recursos:subcontrato_list")

    ids = request.POST.getlist("selected_ids")
    porcentaje_str = request.POST.get("porcentaje") or "0"
    hoja_id = request.POST.get("hoja")

    if not ids:
        redirect_url = reverse("recursos:subcontrato_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    try:
        porcentaje = Decimal(porcentaje_str)
    except InvalidOperation:
        redirect_url = reverse("recursos:subcontrato_list")
        if hoja_id:
            redirect_url += f"?hoja={hoja_id}"
        return redirect(redirect_url)

    if hoja_id:
        hoja = get_object_or_404(HojaPreciosSubcontrato, pk=hoja_id, company=request.company)
        queryset = HojaPrecioSubcontrato.objects.filter(hoja=hoja, pk__in=ids)
        from django.db.models import F
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
    else:
        queryset = Subcontrato.objects.filter(company=request.company, pk__in=ids)
        Subcontrato.actualizar_precios_por_porcentaje(queryset, porcentaje)

    redirect_url = reverse("recursos:subcontrato_list")
    if hoja_id:
        redirect_url += f"?hoja={hoja_id}"
    return redirect(redirect_url)


@login_required
def hoja_subcontrato_list(request):
    company = request.company
    if request.method == "POST":
        nombre = request.POST.get("nombre") or ""
        origen_tipo = request.POST.get("origen_tipo") or "actual"
        origen_hoja_id = request.POST.get("origen_hoja") or None

        if not nombre.strip():
            return redirect("recursos:hoja_subcontrato_list")

        hoja = HojaPreciosSubcontrato.objects.create(
            nombre=nombre.strip(), company=company
        )

        if origen_tipo == "actual":
            subcontratos = Subcontrato.objects.filter(company=company).only(
                "pk",
                "cantidad_por_unidad_venta",
                "precio_unidad_venta",
                "moneda",
            )
            HojaPrecioSubcontrato.objects.bulk_create(
                [
                    HojaPrecioSubcontrato(
                        hoja=hoja,
                        subcontrato=s,
                        cantidad_por_unidad_venta=s.cantidad_por_unidad_venta,
                        precio_unidad_venta=s.precio_unidad_venta,
                        moneda=s.moneda,
                    )
                    for s in subcontratos
                ]
            )
        elif origen_tipo == "hoja" and origen_hoja_id:
            origen = get_object_or_404(
                HojaPreciosSubcontrato, pk=origen_hoja_id, company=company
            )
            hoja.origen = origen
            hoja.save(update_fields=["origen"])
            detalles = origen.detalles.select_related("subcontrato").all()
            HojaPrecioSubcontrato.objects.bulk_create(
                [
                    HojaPrecioSubcontrato(
                        hoja=hoja,
                        subcontrato=d.subcontrato,
                        cantidad_por_unidad_venta=d.cantidad_por_unidad_venta,
                        precio_unidad_venta=d.precio_unidad_venta,
                        moneda=d.moneda,
                    )
                    for d in detalles
                ]
            )

        return redirect("recursos:hoja_subcontrato_list")

    hojas = HojaPreciosSubcontrato.objects.filter(company=company)
    return render(
        request,
        "recursos/hoja_subcontrato_list.html",
        {"hojas": hojas},
    )


@login_required
def hoja_subcontrato_detalle(request, pk):
    hoja = get_object_or_404(HojaPreciosSubcontrato, pk=pk, company=request.company)
    detalles = hoja.detalles.select_related(
        "subcontrato",
        "subcontrato__rubro",
        "subcontrato__subrubro",
        "subcontrato__proveedor",
        "subcontrato__unidad_de_venta",
    ).all()
    lote = Lote.objects.filter(hoja_subcontratos=hoja).first()
    return render(
        request,
        "recursos/hoja_subcontrato_detalle.html",
        {"hoja": hoja, "detalles": detalles, "lote": lote},
    )


@login_required
def hoja_subcontrato_detalle_edit(request, hoja_pk, detalle_pk):
    hoja = get_object_or_404(
        HojaPreciosSubcontrato, pk=hoja_pk, company=request.company
    )
    detalle = get_object_or_404(
        HojaPrecioSubcontrato, pk=detalle_pk, hoja=hoja
    )
    if request.method == "POST":
        form = HojaPrecioSubcontratoForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            return redirect(
                f"{reverse('recursos:subcontrato_list')}?hoja={hoja_pk}"
            )
    return redirect(f"{reverse('recursos:subcontrato_list')}?hoja={hoja_pk}")


@login_required
def hoja_subcontrato_detalle_delete(request, hoja_pk, detalle_pk):
    hoja = get_object_or_404(
        HojaPreciosSubcontrato, pk=hoja_pk, company=request.company
    )
    detalle = get_object_or_404(
        HojaPrecioSubcontrato, pk=detalle_pk, hoja=hoja
    )
    if request.method == "POST":
        detalle.delete()
        return redirect(f"{reverse('recursos:subcontrato_list')}?hoja={hoja_pk}")
    return redirect(f"{reverse('recursos:subcontrato_list')}?hoja={hoja_pk}")

