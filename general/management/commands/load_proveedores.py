"""
Carga proveedores desde un archivo JSON.

Uso:
  python manage.py load_proveedores data_proveedores.json
"""
import json

from django.core.management.base import BaseCommand

from general.models import Company, Proveedor


class Command(BaseCommand):
    help = "Carga proveedores desde un archivo JSON."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str)

    def handle(self, *args, **options):
        archivo = options["archivo"]

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Archivo no encontrado: {archivo}"))
            return
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"JSON inválido: {e}"))
            return

        company_name = (data.get("company") or "").strip()
        if not company_name:
            self.stderr.write(self.style.ERROR('Falta "company" en el JSON.'))
            return

        company = None
        for c in Company.objects.all():
            if c.nombre.strip().lower() == company_name.lower():
                company = c
                break
        if not company:
            self.stderr.write(self.style.ERROR(f"Empresa no encontrada: '{company_name}'."))
            return

        proveedores_data = data.get("proveedores", [])
        created_count = 0
        for p in proveedores_data:
            nombre = (p.get("nombre") or "").strip()
            if not nombre:
                continue
            _, created = Proveedor.objects.get_or_create(
                company=company, nombre=nombre
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Proveedor creado: {nombre}"))

        self.stdout.write(
            self.style.SUCCESS(f"Listo. Proveedores nuevos: {created_count}.")
        )
