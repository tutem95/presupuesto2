from datetime import date
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CompraForm, SemanaForm
from .models import Compra, Semana


def _get_week_start(d):
    """Lunes de la semana de la fecha d."""
    return d - __import__("datetime").timedelta(days=d.weekday())


@login_required
def compras_list(request):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")

    # Filtros
    año = request.GET.get("año")
    mes = request.GET.get("mes")
    semana_filtro = request.GET.get("semana")

    semanas_qs = Semana.objects.filter(company=company).annotate(
        compras_count=Count("compras")
    ).order_by("-fecha")

    if año:
        try:
            año = int(año)
            semanas_qs = semanas_qs.filter(fecha__year=año)
        except ValueError:
            año = None
    if mes:
        try:
            mes = int(mes)
            semanas_qs = semanas_qs.filter(fecha__month=mes)
        except ValueError:
            mes = None
    if semana_filtro:
        try:
            semana_filtro = int(semana_filtro)
            semanas_qs = semanas_qs.filter(fecha__isoweek=semana_filtro)
        except (ValueError, TypeError):
            semana_filtro = None

    semanas = list(semanas_qs[:200])
    años = sorted(
        set(s.fecha.year for s in Semana.objects.filter(company=company)),
        reverse=True,
    ) or [date.today().year]
    meses = list(range(1, 13))

    # Agrupar por año → mes → semanas
    tree = defaultdict(lambda: defaultdict(list))
    for s in semanas:
        tree[s.fecha.year][s.fecha.month].append(s)

    # Ordenar: año descendente, mes descendente, semanas descendente
    tree = {
        y: dict(
            (m, sorted(weeks, key=lambda x: x.fecha, reverse=True))
            for m, weeks in sorted(meses_dict.items(), reverse=True)
        )
        for y, meses_dict in sorted(tree.items(), reverse=True)
    }

    return render(
        request,
        "compras/compras_list.html",
        {
            "tree": dict(tree),
            "años": años,
            "meses": meses,
            "año_filtro": año,
            "mes_filtro": int(mes) if mes else None,
            "semana_filtro": semana_filtro,
        },
    )


@login_required
def semana_create(request):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    if request.method == "POST":
        form = SemanaForm(request.POST)
        if form.is_valid():
            semana = form.save(commit=False)
            semana.company = company
            # Normalizar al lunes de la semana
            semana.fecha = _get_week_start(semana.fecha)
            if Semana.objects.filter(company=company, fecha=semana.fecha).exists():
                return render(
                    request,
                    "compras/semana_form.html",
                    {"form": form, "error": "Ya existe una semana para esa fecha."},
                )
            semana.save()
            return redirect("compras:semana_detalle", pk=semana.pk)
    else:
        form = SemanaForm()
    return render(request, "compras/semana_form.html", {"form": form})


@login_required
def semana_detalle(request, pk):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    semana = get_object_or_404(Semana, pk=pk, company=company)
    compras = semana.compras.select_related(
        "obra", "rubro", "subrubro", "proveedor"
    ).order_by("obra__nombre", "rubro__nombre", "subrubro__nombre")
    return render(
        request,
        "compras/semana_detalle.html",
        {"semana": semana, "compras": compras},
    )


@login_required
def semana_edit(request, pk):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    semana = get_object_or_404(Semana, pk=pk, company=company)
    if request.method == "POST":
        form = SemanaForm(request.POST, instance=semana)
        if form.is_valid():
            form.save()
            return redirect("compras:semana_detalle", pk=pk)
    else:
        form = SemanaForm(instance=semana)
    return render(request, "compras/semana_form.html", {"form": form, "semana": semana})


@login_required
def compra_add(request, semana_pk):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    semana = get_object_or_404(Semana, pk=semana_pk, company=company)
    if request.method == "POST":
        form = CompraForm(request.POST, request=request)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.semana = semana
            compra.save()
            return redirect("compras:semana_detalle", pk=semana_pk)
    else:
        form = CompraForm(request=request)
    return render(request, "compras/compra_form.html", {"form": form, "semana": semana})


@login_required
def compra_edit(request, semana_pk, compra_pk):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    semana = get_object_or_404(Semana, pk=semana_pk, company=company)
    compra = get_object_or_404(Compra, pk=compra_pk, semana=semana)
    if request.method == "POST":
        form = CompraForm(request.POST, instance=compra, request=request)
        if form.is_valid():
            form.save()
            return redirect("compras:semana_detalle", pk=semana_pk)
    else:
        form = CompraForm(instance=compra, request=request)
    return render(
        request,
        "compras/compra_form.html",
        {"form": form, "semana": semana, "compra": compra},
    )


@login_required
def compra_delete(request, semana_pk, compra_pk):
    company = request.company
    if not company:
        return redirect("usuarios:company_select")
    semana = get_object_or_404(Semana, pk=semana_pk, company=company)
    compra = get_object_or_404(Compra, pk=compra_pk, semana=semana)
    if request.method == "POST":
        compra.delete()
        return redirect("compras:semana_detalle", pk=semana_pk)
    return render(
        request,
        "compras/compra_confirm_delete.html",
        {"semana": semana, "compra": compra},
    )
