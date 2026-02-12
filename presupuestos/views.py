from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from recursos.models import Rubro, Subrubro

from .forms import PresupuestoForm, PresupuestoItemForm
from .models import Presupuesto, PresupuestoItem


@login_required
def presupuesto_list(request):
    presupuestos = Presupuesto.objects.filter(
        company=request.company
    ).select_related("obra", "lote", "tipo_dolar").prefetch_related(
        "items__tarea"
    ).order_by("-creado_en")

    # Filtro: activos, todos, cancelados
    filtro = request.GET.get("filtro", "activos")
    if filtro == "activos":
        presupuestos = presupuestos.filter(activo=True)
    elif filtro == "cancelados":
        presupuestos = presupuestos.filter(activo=False)

    # Búsqueda por nombre (obra)
    buscar = (request.GET.get("buscar") or "").strip()
    if buscar:
        presupuestos = presupuestos.filter(obra__nombre__icontains=buscar)

    return render(
        request,
        "presupuestos/presupuesto_list.html",
        {"presupuestos": presupuestos, "filtro": filtro, "buscar": buscar},
    )


@login_required
def presupuesto_create(request):
    if request.method == "POST":
        form = PresupuestoForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.company
            obj.save()
            return redirect("presupuestos:presupuesto_rubros", pk=obj.pk)
    else:
        form = PresupuestoForm(request=request)

    return render(
        request,
        "presupuestos/presupuesto_form.html",
        {"form": form, "presupuesto": None},
    )


@login_required
def presupuesto_edit(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, company=request.company)
    if request.method == "POST":
        form = PresupuestoForm(request.POST, request=request, instance=presupuesto)
        if form.is_valid():
            form.save()
            return redirect("presupuestos:presupuesto_rubros", pk=presupuesto.pk)
    else:
        form = PresupuestoForm(request=request, instance=presupuesto)

    return render(
        request,
        "presupuestos/presupuesto_form.html",
        {"form": form, "presupuesto": presupuesto},
    )


@login_required
def presupuesto_toggle_activo(request, pk):
    """Alterna activo/cancelado del presupuesto."""
    presupuesto = get_object_or_404(Presupuesto, pk=pk, company=request.company)
    if request.method == "POST":
        presupuesto.activo = not presupuesto.activo
        presupuesto.save()
    filtro = request.GET.get("filtro", "activos")
    buscar = request.GET.get("buscar", "")
    url = reverse("presupuestos:presupuesto_list")
    params = []
    if filtro:
        params.append(f"filtro={filtro}")
    if buscar:
        params.append(f"buscar={buscar}")
    if params:
        url += "?" + "&".join(params)
    return redirect(url)


@login_required
def presupuesto_delete(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, company=request.company)
    if request.method == "POST":
        presupuesto.delete()
        return redirect("presupuestos:presupuesto_list")
    return render(
        request,
        "general/confirm_delete.html",
        {"object": presupuesto, "cancel_url": "presupuestos:presupuesto_list"},
    )


@login_required
def presupuesto_rubros(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related("obra", "lote", "tipo_dolar"),
        pk=pk,
        company=request.company,
    )
    cotiz = presupuesto.get_cotizacion_usd()

    # Rubros del lote (que tienen tareas) - para poder navegar y agregar
    rubro_ids = presupuesto.lote.tareas.values_list("rubro_id", flat=True).distinct()
    rubros = Rubro.objects.filter(
        pk__in=rubro_ids, company=request.company
    ).order_by("nombre")

    rubros_con_total = []
    for rubro in rubros:
        items = presupuesto.items.filter(tarea__rubro=rubro)
        total_usd = None
        if cotiz:
            total_usd = sum(
                (item.total_general_usd() or Decimal("0")) for item in items
            )
        rubros_con_total.append((rubro, total_usd))

    presupuesto_total = presupuesto.total_usd()

    # Datos para el pie chart (etiqueta, valor, porcentaje)
    chart_data = []
    if presupuesto_total and presupuesto_total > 0:
        for rubro, total_usd in rubros_con_total:
            val = float(total_usd or 0)
            pct = float((total_usd or 0) / presupuesto_total * 100)
            if val > 0:
                chart_data.append({
                    "label": rubro.nombre,
                    "value": val,
                    "percentage": round(pct, 1),
                })

    return render(
        request,
        "presupuestos/presupuesto_rubros.html",
        {
            "presupuesto": presupuesto,
            "rubros_con_total": rubros_con_total,
            "presupuesto_total": presupuesto_total,
            "chart_data": chart_data,
        },
    )


@login_required
def presupuesto_subrubros(request, pk, rubro_pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related("obra", "lote", "tipo_dolar"),
        pk=pk,
        company=request.company,
    )
    rubro = get_object_or_404(Rubro, pk=rubro_pk, company=request.company)
    cotiz = presupuesto.get_cotizacion_usd()

    # Subrubros del lote en este rubro
    subrubro_ids = presupuesto.lote.tareas.filter(
        rubro=rubro
    ).values_list("subrubro_id", flat=True).distinct()
    subrubros = Subrubro.objects.filter(
        pk__in=subrubro_ids, company=request.company
    ).order_by("nombre")

    subrubros_con_total = []
    for subrubro in subrubros:
        items = presupuesto.items.filter(
            tarea__rubro=rubro, tarea__subrubro=subrubro
        )
        total_usd = None
        if cotiz:
            total_usd = sum(
                (item.total_general_usd() or Decimal("0")) for item in items
            )
        subrubros_con_total.append((subrubro, total_usd))

    rubro_total = sum(
        (t or Decimal("0")) for _, t in subrubros_con_total
    ) if cotiz else None

    # Datos para el pie chart (subrubros y sus %)
    chart_data = []
    if rubro_total and rubro_total > 0:
        for subrubro, total_usd in subrubros_con_total:
            val = float(total_usd or 0)
            pct = float((total_usd or 0) / rubro_total * 100)
            if val > 0:
                chart_data.append({
                    "label": subrubro.nombre,
                    "value": val,
                    "percentage": round(pct, 1),
                })

    return render(
        request,
        "presupuestos/presupuesto_subrubros.html",
        {
            "presupuesto": presupuesto,
            "rubro": rubro,
            "subrubros_con_total": subrubros_con_total,
            "rubro_total": rubro_total,
            "chart_data": chart_data,
        },
    )


@login_required
def presupuesto_tareas(request, pk, rubro_pk, subrubro_pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related("obra", "lote", "tipo_dolar"),
        pk=pk,
        company=request.company,
    )
    rubro = get_object_or_404(Rubro, pk=rubro_pk, company=request.company)
    subrubro = get_object_or_404(Subrubro, pk=subrubro_pk, company=request.company)

    items = presupuesto.items.filter(
        tarea__rubro=rubro,
        tarea__subrubro=subrubro,
    ).select_related(
        "tarea",
        "tarea__rubro",
        "tarea__subrubro",
    ).order_by("tarea__nombre")

    if request.method == "POST":
        form = PresupuestoItemForm(request.POST, presupuesto=presupuesto)
        if form.is_valid():
            tarea = form.cleaned_data["tarea"]
            cantidad = form.cleaned_data["cantidad"]
            if tarea.rubro_id == rubro.pk and tarea.subrubro_id == subrubro.pk:
                PresupuestoItem.objects.update_or_create(
                    presupuesto=presupuesto,
                    tarea=tarea,
                    defaults={"cantidad": cantidad},
                )
            return redirect(
                "presupuestos:presupuesto_tareas",
                pk=pk,
                rubro_pk=rubro_pk,
                subrubro_pk=subrubro_pk,
            )
    else:
        form = PresupuestoItemForm(presupuesto=presupuesto)
        # Filtrar solo tareas de este rubro/subrubro
        form.fields["tarea"].queryset = form.fields["tarea"].queryset.filter(
            rubro=rubro, subrubro=subrubro
        )

    cotiz = presupuesto.get_cotizacion_usd()
    subrubro_total = sum(
        (item.total_general_usd() or Decimal("0")) for item in items
    ) if cotiz else None

    return render(
        request,
        "presupuestos/presupuesto_tareas.html",
        {
            "presupuesto": presupuesto,
            "rubro": rubro,
            "subrubro": subrubro,
            "items": items,
            "form": form,
            "subrubro_total": subrubro_total,
        },
    )


@login_required
def presupuesto_item_delete(request, pk, item_pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, company=request.company)
    item = get_object_or_404(PresupuestoItem, pk=item_pk, presupuesto=presupuesto)
    rubro_pk = item.tarea.rubro_id
    subrubro_pk = item.tarea.subrubro_id
    if request.method == "POST":
        item.delete()
    return redirect(
        "presupuestos:presupuesto_tareas",
        pk=pk,
        rubro_pk=rubro_pk,
        subrubro_pk=subrubro_pk,
    )
