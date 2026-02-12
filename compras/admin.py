from django.contrib import admin
from .models import Compra, Semana


class CompraInline(admin.TabularInline):
    model = Compra
    extra = 0


@admin.register(Semana)
class SemanaAdmin(admin.ModelAdmin):
    list_display = ["fecha", "company"]
    list_filter = ["company"]
    date_hierarchy = "fecha"
    inlines = [CompraInline]


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = [
        "semana", "obra", "rubro", "subrubro", "item", "proveedor",
        "forma_pago", "monto_total", "estado", "es_subcontrato",
    ]
    list_filter = ["estado", "forma_pago", "es_subcontrato"]
    search_fields = ["item", "obra__nombre", "proveedor__nombre"]
