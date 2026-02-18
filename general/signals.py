"""
Signals para general app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Company, CompanyMembership


@receiver(post_save, sender=Company)
def create_initial_lote(sender, instance, created, **kwargs):
    """
    Cuando se crea una empresa, se crea automáticamente un lote inicial
    con hojas de precios vacías (materiales, mano de obra y subcontratos).
    """
    if not created:
        return
    
    # Importar aquí para evitar importaciones circulares
    from recursos.models import (
        HojaPrecios,
        HojaPreciosManoDeObra,
        HojaPreciosSubcontrato,
        Lote,
    )
    
    # Crear las tres hojas de precios vacías
    nombre_lote = "Lote Inicial"
    hoja_materiales = HojaPrecios.objects.create(
        nombre=f"{nombre_lote} - Materiales",
        company=instance
    )
    hoja_mo = HojaPreciosManoDeObra.objects.create(
        nombre=f"{nombre_lote} - Mano de Obra",
        company=instance
    )
    hoja_sub = HojaPreciosSubcontrato.objects.create(
        nombre=f"{nombre_lote} - Subcontratos",
        company=instance
    )
    
    # Crear el lote inicial con las tres hojas
    Lote.objects.create(
        nombre=nombre_lote,
        company=instance,
        hoja_materiales=hoja_materiales,
        hoja_mano_de_obra=hoja_mo,
        hoja_subcontratos=hoja_sub,
    )


@receiver(post_save, sender=CompanyMembership)
def first_member_is_admin(sender, instance, created, **kwargs):
    """
    El primer usuario que se une a una empresa es admin.
    Si la empresa no tiene ningún admin, este membership se marca como admin.
    """
    if not created:
        return
    company = instance.company
    has_admin = CompanyMembership.objects.filter(
        company=company, is_admin=True
    ).exists()
    if not has_admin:
        instance.is_admin = True
        instance.save(update_fields=["is_admin"])
