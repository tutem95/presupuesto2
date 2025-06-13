from django.contrib import admin
from .models import CategoriaMaterial, Proveedor, Rubro, TipoMaterial, Unidad, Subrubro

admin.site.register(Rubro)
admin.site.register(Unidad)

@admin.register(Subrubro)
class SubrubroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rubro',)
    list_filter = ('rubro',)
    search_fields = ('nombre',)
    
    
admin.site.register(Proveedor)
admin.site.register(TipoMaterial)
admin.site.register(CategoriaMaterial)