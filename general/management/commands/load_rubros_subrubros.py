"""
Carga rubros y subrubros desde un archivo JSON.

Uso:
  python manage.py load_rubros_subrubros data_rubros_subrubros.json
  python manage.py load_rubros_subrubros data_rubros_subrubros.json --create-company

Formato del JSON:
  {
    "company": "Nombre de la empresa",
    "rubros": [ { "nombre": "..." }, ... ],
    "subrubros": [ { "rubro": "nombre rubro", "nombre": "..." }, ... ]
  }
"""
import json

from django.core.management.base import BaseCommand

from general.models import Company, Rubro, Subrubro


class Command(BaseCommand):
    help = "Carga rubros y subrubros desde un archivo JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "archivo",
            type=str,
            help="Ruta al archivo JSON con rubros y subrubros.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se cargaría, sin guardar.",
        )
        parser.add_argument(
            "--create-company",
            action="store_true",
            help="Crear la empresa si no existe (por nombre).",
        )

    def handle(self, *args, **options):
        archivo = options["archivo"]
        dry_run = options["dry_run"]
        create_company = options.get("create_company", False)

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
        if not company and create_company:
            company = Company.objects.create(nombre=company_name)
            self.stdout.write(self.style.SUCCESS(f"Empresa creada: {company.nombre} (id={company.pk})"))
        elif not company:
            self.stderr.write(
                self.style.ERROR(
                    f"Empresa no encontrada: '{company_name}'. "
                    "Creala en Admin → General → Empresas, o usá --create-company para crearla al cargar."
                )
            )
            return

        rubros_data = data.get("rubros", [])
        subrubros_data = data.get("subrubros", [])

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Se cargarían {len(rubros_data)} rubros y "
                    f"{len(subrubros_data)} subrubros para '{company_name}'."
                )
            )
            for r in rubros_data:
                self.stdout.write(f"  Rubro: {r.get('nombre', '?')}")
            for s in subrubros_data:
                self.stdout.write(
                    f"  Subrubro: {s.get('nombre', '?')} (rubro: {s.get('rubro', '?')})"
                )
            return

        rubro_by_name = {}
        for r in rubros_data:
            nombre = (r.get("nombre") or "").strip()
            if not nombre:
                continue
            rubro, created = Rubro.objects.get_or_create(
                company=company, nombre=nombre, defaults={}
            )
            rubro_by_name[nombre] = rubro
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Rubro creado: {nombre}"))

        created_sub = 0
        for s in subrubros_data:
            nombre = (s.get("nombre") or "").strip()
            rubro_nombre = (s.get("rubro") or "").strip()
            if not nombre or not rubro_nombre:
                continue
            rubro = rubro_by_name.get(rubro_nombre)
            if not rubro:
                self.stderr.write(
                    self.style.WARNING(
                        f"  Subrubro '{nombre}' ignorado: rubro '{rubro_nombre}' no existe en la lista."
                    )
                )
                continue
            _, created = Subrubro.objects.get_or_create(
                company=company, rubro=rubro, nombre=nombre, defaults={}
            )
            if created:
                created_sub += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Subrubro creado: {nombre} ({rubro_nombre})")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Rubros: {len(rubro_by_name)}, subrubros nuevos: {created_sub}."
            )
        )
