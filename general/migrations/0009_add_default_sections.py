# Data migration: crear secciones Presupuestos, Sueldos, Compras

from django.db import migrations


def create_sections(apps, schema_editor):
    Section = apps.get_model("general", "Section")
    Section.objects.bulk_create([
        Section(code="presupuestos", nombre="Presupuestos"),
        Section(code="sueldos", nombre="Sueldos"),
        Section(code="compras", nombre="Compras"),
    ])


def remove_sections(apps, schema_editor):
    Section = apps.get_model("general", "Section")
    Section.objects.filter(code__in=["presupuestos", "sueldos", "compras"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("general", "0008_add_sections_and_membership_admin"),
    ]

    operations = [
        migrations.RunPython(create_sections, remove_sections),
    ]
