"""
Carga equipos y ref equipos desde un archivo JSON.

Uso:
  python manage.py load_equipos_ref data_equipos_ref.json
"""
import json

from django.core.management.base import BaseCommand

from general.models import Company, Equipo, RefEquipo


class Command(BaseCommand):
    help = "Carga equipos y ref equipos desde un archivo JSON."

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

        equipos_data = data.get("equipos", [])
        refs_data = data.get("ref_equipos", [])

        equipo_by_name = {}
        for e in equipos_data:
            nombre = (e.get("nombre") or "").strip()
            if not nombre:
                continue
            equipo, created = Equipo.objects.get_or_create(
                company=company, nombre=nombre
            )
            equipo_by_name[nombre] = equipo
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Equipo creado: {nombre}"))

        created_ref = 0
        for r in refs_data:
            nombre = (r.get("nombre") or "").strip()
            equipo_nombre = (r.get("equipo") or "").strip()
            if not nombre or not equipo_nombre:
                continue
            equipo = equipo_by_name.get(equipo_nombre)
            if not equipo:
                self.stderr.write(
                    self.style.WARNING(f"  Ref '{nombre}' ignorada: equipo '{equipo_nombre}' no encontrado.")
                )
                continue
            _, created = RefEquipo.objects.get_or_create(
                company=company, equipo=equipo, nombre=nombre
            )
            if created:
                created_ref += 1
                self.stdout.write(self.style.SUCCESS(f"  Ref creada: {nombre} ({equipo_nombre})"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Equipos: {len(equipo_by_name)}, refs nuevas: {created_ref}."
            )
        )
