"""
Carga tipos de material y categorías desde un archivo JSON.

Uso:
  python manage.py load_tipos_categorias data_tipos_categorias.json
"""
import json

from django.core.management.base import BaseCommand

from general.models import Company, TipoMaterial, CategoriaMaterial


class Command(BaseCommand):
    help = "Carga tipos de material y categorías desde un archivo JSON."

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

        tipos_data = data.get("tipos", [])
        categorias_data = data.get("categorias", [])

        tipo_by_name = {}
        for t in tipos_data:
            nombre = (t.get("nombre") or "").strip()
            if not nombre:
                continue
            tipo, created = TipoMaterial.objects.get_or_create(
                company=company, nombre=nombre
            )
            tipo_by_name[nombre] = tipo
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Tipo creado: {nombre}"))

        created_cat = 0
        for cat in categorias_data:
            nombre = (cat.get("nombre") or "").strip()
            tipo_nombre = (cat.get("tipo") or "").strip()
            if not nombre or not tipo_nombre:
                continue
            tipo = tipo_by_name.get(tipo_nombre)
            if not tipo:
                self.stderr.write(
                    self.style.WARNING(f"  Categoría '{nombre}' ignorada: tipo '{tipo_nombre}' no encontrado.")
                )
                continue
            _, created = CategoriaMaterial.objects.get_or_create(
                company=company, tipo=tipo, nombre=nombre
            )
            if created:
                created_cat += 1
                self.stdout.write(self.style.SUCCESS(f"  Categoría creada: {nombre} ({tipo_nombre})"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Tipos: {len(tipo_by_name)}, categorías nuevas: {created_cat}."
            )
        )
