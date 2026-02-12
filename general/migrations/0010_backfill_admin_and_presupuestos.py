# Data migration: miembros existentes:
# - primer miembro por empresa = admin
# - no-admins sin secciones = darles presupuestos

from django.db import migrations


def backfill(apps, schema_editor):
    CompanyMembership = apps.get_model("general", "CompanyMembership")
    Section = apps.get_model("general", "Section")
    CompanyMembershipSection = apps.get_model("general", "CompanyMembershipSection")
    presupuestos = Section.objects.filter(code="presupuestos").first()
    if not presupuestos:
        return

    for membership in CompanyMembership.objects.select_related("company").order_by("company_id", "id"):
        company = membership.company
        # Primer miembro de la empresa = admin
        first_in_company = CompanyMembership.objects.filter(
            company=company
        ).order_by("id").first()
        if first_in_company and first_in_company.pk == membership.pk:
            if not membership.is_admin:
                membership.is_admin = True
                membership.save(update_fields=["is_admin"])
        # No-admins sin secciones: darles presupuestos para que sigan entrando
        if not membership.is_admin:
            has_any = CompanyMembershipSection.objects.filter(membership=membership).exists()
            if not has_any:
                CompanyMembershipSection.objects.create(
                    membership=membership,
                    section=presupuestos,
                )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("general", "0009_add_default_sections"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
