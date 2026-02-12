"""
Signals para general app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CompanyMembership


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
