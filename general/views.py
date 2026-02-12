from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from general.models import (
    CategoriaMaterial,
    CompanyMembership,
    CotizacionDolar,
    Equipo,
    Obra,
    Proveedor,
    RefEquipo,
    Rubro,
    Subrubro,
    TipoDolar,
    TipoMaterial,
    Unidad,
)
from recursos.models import Lote, ManoDeObra, Material, Mezcla, Subcontrato, Tarea

from .forms import (
    CategoriaMaterialForm,
    EquipoForm,
    MemberAddForm,
    MemberEditForm,
    ObraForm,
    ProveedorForm,
    RefEquipoForm,
    RubroForm,
    SubrubroForm,
    TipoDolarForm,
    TipoMaterialForm,
    UnidadForm,
)


def _get_totales(company):
    return {
        "ref_equipos": RefEquipo.objects.filter(company=company).count(),
        "rubros": Rubro.objects.filter(company=company).count(),
        "subrubros": Subrubro.objects.filter(company=company).count(),
        "unidades": Unidad.objects.filter(company=company).count(),
        "tipos_material": TipoMaterial.objects.filter(company=company).count(),
        "categorias_material": CategoriaMaterial.objects.filter(company=company).count(),
        "equipos": Equipo.objects.filter(company=company).count(),
        "materiales": Material.objects.filter(company=company).count(),
        "mano_de_obra": ManoDeObra.objects.filter(company=company).count(),
        "subcontratos": Subcontrato.objects.filter(company=company).count(),
        "mezclas": Mezcla.objects.filter(company=company).count(),
        "lotes": Lote.objects.filter(company=company).count(),
        "tareas": Tarea.objects.filter(company=company).count(),
        "proveedores": Proveedor.objects.filter(company=company).count(),
        "tipos_dolar": TipoDolar.objects.filter(company=company).count(),
        "obras": Obra.objects.filter(company=company).count(),
    }


@login_required
def dashboard(request):
    """Panel general: acceso a Índice, Tareas y Presupuesto."""
    return render(request, "general/dashboard.html")


@login_required
def indice(request):
    """Catálogos generales (antes Catálogos generales)."""
    company = request.company
    return render(request, "general/indice.html", {"totales": _get_totales(company)})


@login_required
def presupuesto(request):
    """Página general de Presupuestos: Índice, Tareas, Presupuesto, Tabla Dólar."""
    return render(request, "general/presupuesto.html")


@login_required
def rubro_list(request):
    company = request.company
    if request.method == "POST":
        form = RubroForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:rubro_list")
    else:
        form = RubroForm(request=request)

    rubros = Rubro.objects.filter(company=company)
    return render(request, "general/rubro_list.html", {"rubros": rubros, "form": form})


@login_required
def rubro_edit(request, pk):
    company = request.company
    rubro = get_object_or_404(Rubro, pk=pk, company=company)
    if request.method == "POST":
        form = RubroForm(request.POST, instance=rubro, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:rubro_list")
    else:
        form = RubroForm(instance=rubro, request=request)

    rubros = Rubro.objects.filter(company=company)
    return render(
        request,
        "general/rubro_list.html",
        {"rubros": rubros, "form": form, "editing": rubro},
    )


@login_required
def rubro_delete(request, pk):
    rubro = get_object_or_404(Rubro, pk=pk, company=request.company)
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
    company = request.company
    if request.method == "POST":
        form = UnidadForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:unidad_list")
    else:
        form = UnidadForm(request=request)

    unidades = Unidad.objects.filter(company=company)
    return render(
        request,
        "general/unidad_list.html",
        {"unidades": unidades, "form": form},
    )


@login_required
def unidad_edit(request, pk):
    company = request.company
    unidad = get_object_or_404(Unidad, pk=pk, company=company)
    if request.method == "POST":
        form = UnidadForm(request.POST, instance=unidad, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:unidad_list")
    else:
        form = UnidadForm(instance=unidad, request=request)

    unidades = Unidad.objects.filter(company=company)
    return render(
        request,
        "general/unidad_list.html",
        {"unidades": unidades, "form": form, "editing": unidad},
    )


@login_required
def unidad_delete(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk, company=request.company)
    if request.method == "POST":
        unidad.delete()
        return redirect("general:unidad_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": unidad, "cancel_url": "general:unidad_list"},
    )


@login_required
def equipo_list(request):
    company = request.company
    if request.method == "POST":
        form = EquipoForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:equipo_list")
    else:
        form = EquipoForm(request=request)

    equipos = Equipo.objects.filter(company=company)
    return render(
        request,
        "general/equipo_list.html",
        {"equipos": equipos, "form": form},
    )


@login_required
def equipo_edit(request, pk):
    company = request.company
    equipo = get_object_or_404(Equipo, pk=pk, company=company)
    if request.method == "POST":
        form = EquipoForm(request.POST, instance=equipo, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:equipo_list")
    else:
        form = EquipoForm(instance=equipo, request=request)

    equipos = Equipo.objects.filter(company=company)
    return render(
        request,
        "general/equipo_list.html",
        {"equipos": equipos, "form": form, "editing": equipo},
    )


@login_required
def equipo_delete(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk, company=request.company)
    if request.method == "POST":
        equipo.delete()
        return redirect("general:equipo_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": equipo, "cancel_url": "general:equipo_list"},
    )


@login_required
def tipo_material_list(request):
    company = request.company
    if request.method == "POST":
        form = TipoMaterialForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:tipo_material_list")
    else:
        form = TipoMaterialForm(request=request)

    tipos = TipoMaterial.objects.filter(company=company)
    return render(
        request,
        "general/tipo_material_list.html",
        {"tipos": tipos, "form": form},
    )


@login_required
def tipo_material_edit(request, pk):
    company = request.company
    tipo = get_object_or_404(TipoMaterial, pk=pk, company=company)
    if request.method == "POST":
        form = TipoMaterialForm(request.POST, instance=tipo, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:tipo_material_list")
    else:
        form = TipoMaterialForm(instance=tipo, request=request)

    tipos = TipoMaterial.objects.filter(company=company)
    return render(
        request,
        "general/tipo_material_list.html",
        {"tipos": tipos, "form": form, "editing": tipo},
    )


@login_required
def tipo_material_delete(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk, company=request.company)
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
    company = request.company
    if request.method == "POST":
        form = CategoriaMaterialForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:categoria_material_list")
    else:
        form = CategoriaMaterialForm(request=request)

    categorias = CategoriaMaterial.objects.filter(company=company).select_related("tipo")
    return render(
        request,
        "general/categoria_material_list.html",
        {"categorias": categorias, "form": form},
    )


@login_required
def categoria_material_edit(request, pk):
    company = request.company
    categoria = get_object_or_404(CategoriaMaterial, pk=pk, company=company)
    if request.method == "POST":
        form = CategoriaMaterialForm(request.POST, instance=categoria, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:categoria_material_list")
    else:
        form = CategoriaMaterialForm(instance=categoria, request=request)

    categorias = CategoriaMaterial.objects.filter(company=company).select_related("tipo")
    return render(
        request,
        "general/categoria_material_list.html",
        {"categorias": categorias, "form": form, "editing": categoria},
    )


@login_required
def categoria_material_delete(request, pk):
    categoria = get_object_or_404(CategoriaMaterial, pk=pk, company=request.company)
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
    company = request.company
    if request.method == "POST":
        form = SubrubroForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:subrubro_list")
    else:
        form = SubrubroForm(request=request)

    subrubros = Subrubro.objects.filter(company=company).select_related("rubro")
    return render(
        request,
        "general/subrubro_list.html",
        {"subrubros": subrubros, "form": form},
    )


@login_required
def subrubro_edit(request, pk):
    company = request.company
    subrubro = get_object_or_404(Subrubro, pk=pk, company=company)
    if request.method == "POST":
        form = SubrubroForm(request.POST, instance=subrubro, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:subrubro_list")
    else:
        form = SubrubroForm(instance=subrubro, request=request)

    subrubros = Subrubro.objects.filter(company=company).select_related("rubro")
    return render(
        request,
        "general/subrubro_list.html",
        {"subrubros": subrubros, "form": form, "editing": subrubro},
    )


@login_required
def subrubro_delete(request, pk):
    subrubro = get_object_or_404(Subrubro, pk=pk, company=request.company)
    if request.method == "POST":
        subrubro.delete()
        return redirect("general:subrubro_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": subrubro, "cancel_url": "general:subrubro_list"},
    )


@login_required
def ref_equipo_list(request):
    company = request.company
    if request.method == "POST":
        form = RefEquipoForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:ref_equipo_list")
    else:
        form = RefEquipoForm(request=request)

    ref_equipos = RefEquipo.objects.filter(company=company).select_related("equipo")
    return render(
        request,
        "general/ref_equipo_list.html",
        {"ref_equipos": ref_equipos, "form": form},
    )


@login_required
def ref_equipo_edit(request, pk):
    company = request.company
    ref_equipo = get_object_or_404(RefEquipo, pk=pk, company=company)
    if request.method == "POST":
        form = RefEquipoForm(request.POST, instance=ref_equipo, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:ref_equipo_list")
    else:
        form = RefEquipoForm(instance=ref_equipo, request=request)

    ref_equipos = RefEquipo.objects.filter(company=company).select_related("equipo")
    return render(
        request,
        "general/ref_equipo_list.html",
        {"ref_equipos": ref_equipos, "form": form, "editing": ref_equipo},
    )


@login_required
def ref_equipo_delete(request, pk):
    ref_equipo = get_object_or_404(RefEquipo, pk=pk, company=request.company)
    if request.method == "POST":
        ref_equipo.delete()
        return redirect("general:ref_equipo_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": ref_equipo, "cancel_url": "general:ref_equipo_list"},
    )


@login_required
def proveedor_list(request):
    company = request.company
    if request.method == "POST":
        form = ProveedorForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:proveedor_list")
    else:
        form = ProveedorForm(request=request)

    proveedores = Proveedor.objects.filter(company=company)
    return render(
        request,
        "general/proveedor_list.html",
        {"proveedores": proveedores, "form": form},
    )


@login_required
def proveedor_edit(request, pk):
    company = request.company
    proveedor = get_object_or_404(Proveedor, pk=pk, company=company)
    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:proveedor_list")
    else:
        form = ProveedorForm(instance=proveedor, request=request)

    proveedores = Proveedor.objects.filter(company=company)
    return render(
        request,
        "general/proveedor_list.html",
        {"proveedores": proveedores, "form": form, "editing": proveedor},
    )


@login_required
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk, company=request.company)
    if request.method == "POST":
        proveedor.delete()
        return redirect("general:proveedor_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": proveedor, "cancel_url": "general:proveedor_list"},
    )


@login_required
def obra_list(request):
    company = request.company
    if request.method == "POST":
        form = ObraForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:obra_list")
    else:
        form = ObraForm(request=request)

    obras = Obra.objects.filter(company=company)
    return render(
        request,
        "general/obra_list.html",
        {"obras": obras, "form": form},
    )


@login_required
def obra_edit(request, pk):
    company = request.company
    obra = get_object_or_404(Obra, pk=pk, company=company)
    if request.method == "POST":
        form = ObraForm(request.POST, instance=obra, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:obra_list")
    else:
        form = ObraForm(instance=obra, request=request)

    obras = Obra.objects.filter(company=company)
    return render(
        request,
        "general/obra_list.html",
        {"obras": obras, "form": form, "editing": obra},
    )


@login_required
def obra_delete(request, pk):
    obra = get_object_or_404(Obra, pk=pk, company=request.company)
    if request.method == "POST":
        obra.delete()
        return redirect("general:obra_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": obra, "cancel_url": "general:obra_list"},
    )


@login_required
def tipo_dolar_list(request):
    company = request.company
    if request.method == "POST":
        form = TipoDolarForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            return redirect("general:tipo_dolar_list")
    else:
        form = TipoDolarForm(request=request)

    tipos = TipoDolar.objects.filter(company=company)
    return render(
        request,
        "general/tipo_dolar_list.html",
        {"tipos": tipos, "form": form},
    )


@login_required
def tipo_dolar_edit(request, pk):
    company = request.company
    tipo = get_object_or_404(TipoDolar, pk=pk, company=company)
    if request.method == "POST":
        form = TipoDolarForm(request.POST, instance=tipo, request=request)
        if form.is_valid():
            form.save()
            return redirect("general:tipo_dolar_list")
    else:
        form = TipoDolarForm(instance=tipo, request=request)

    tipos = TipoDolar.objects.filter(company=company)
    return render(
        request,
        "general/tipo_dolar_list.html",
        {"tipos": tipos, "form": form, "editing": tipo},
    )


@login_required
def tipo_dolar_delete(request, pk):
    tipo = get_object_or_404(TipoDolar, pk=pk, company=request.company)
    if request.method == "POST":
        tipo.delete()
        return redirect("general:tipo_dolar_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": tipo, "cancel_url": "general:tipo_dolar_list"},
    )


@login_required
def tabla_dolar(request):
    """Tabla de cotizaciones: fecha + columnas por tipo de dólar."""
    company = request.company
    tipos = TipoDolar.objects.filter(company=company).order_by("nombre")

    if request.method == "POST":
        fecha_str = request.POST.get("fecha")
        if fecha_str:
            from datetime import datetime
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                for tipo in tipos:
                    val = request.POST.get(f"tipo_{tipo.pk}")
                    if val is not None and val.strip() != "":
                        try:
                            valor = Decimal(val.strip().replace(",", "."))
                            CotizacionDolar.objects.update_or_create(
                                company=company,
                                fecha=fecha,
                                tipo=tipo,
                                defaults={"valor": valor},
                            )
                        except (ValueError, InvalidOperation):
                            pass
                return redirect("general:tabla_dolar")
            except ValueError:
                pass

    from django.db.models import Min
    fechas = CotizacionDolar.objects.filter(company=company).values_list(
        "fecha", flat=True
    ).distinct().order_by("-fecha")[:200]  # últimas 200 fechas

    cotizacion_por_fecha = {}
    for c in CotizacionDolar.objects.filter(
        company=company, fecha__in=fechas
    ).select_related("tipo"):
        if c.fecha not in cotizacion_por_fecha:
            cotizacion_por_fecha[c.fecha] = {}
        cotizacion_por_fecha[c.fecha][c.tipo_id] = c.valor

    rows = []
    for fecha in fechas:
        valores = [cotizacion_por_fecha.get(fecha, {}).get(t.pk) for t in tipos]
        rows.append({"fecha": fecha, "valores": valores})

    return render(
        request,
        "general/tabla_dolar.html",
        {
            "tipos": tipos,
            "rows": rows,
        },
    )


# ========== Gestión de usuarios (solo admin de empresa) ==========

@login_required
def member_list(request):
    """Lista de miembros de la empresa. Solo admin."""
    if not request.membership or not request.membership.is_admin:
        return redirect("no_section_access")
    company = request.company
    members = (
        CompanyMembership.objects.filter(company=company)
        .select_related("user")
        .prefetch_related("membership_sections__section")
        .order_by("user__username")
    )
    return render(
        request,
        "general/member_list.html",
        {"members": members},
    )


@login_required
def member_add(request):
    """Agregar usuario a la empresa. Solo admin."""
    if not request.membership or not request.membership.is_admin:
        return redirect("no_section_access")
    company = request.company
    if request.method == "POST":
        form = MemberAddForm(request.POST, company=company)
        if form.is_valid():
            form.save()
            return redirect("general:member_list")
    else:
        form = MemberAddForm(company=company)
    return render(
        request,
        "general/member_form.html",
        {"form": form, "member": None},
    )


@login_required
def member_edit(request, pk):
    """Editar secciones de un miembro. Solo admin."""
    if not request.membership or not request.membership.is_admin:
        return redirect("no_section_access")
    company = request.company
    membership = get_object_or_404(CompanyMembership, pk=pk, company=company)
    if request.method == "POST":
        form = MemberEditForm(request.POST, company=company, membership=membership)
        if form.is_valid():
            form.save()
            return redirect("general:member_list")
    else:
        form = MemberEditForm(company=company, membership=membership)
    return render(
        request,
        "general/member_form.html",
        {"form": form, "member": membership},
    )


@login_required
def member_remove(request, pk):
    """Quitar miembro de la empresa. Solo admin."""
    if not request.membership or not request.membership.is_admin:
        return redirect("no_section_access")
    membership = get_object_or_404(CompanyMembership, pk=pk, company=request.company)
    if request.method == "POST":
        membership.delete()
        return redirect("general:member_list")
    return render(
        request,
        "general/confirm_delete.html",
        {
            "object": membership.user,
            "cancel_url": "general:member_list",
            "message": "¿Quitar este usuario de la empresa?",
        },
    )
