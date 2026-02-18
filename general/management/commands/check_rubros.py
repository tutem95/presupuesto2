"""
Muestra cuántos rubros y subrubros tiene cada empresa.

Uso:
  python manage.py check_rubros
  python manage.py check_rubros --company Nocito
"""
from django.core.management.base import BaseCommand

from general.models import Company, Rubro, Subrubro


class Command(BaseCommand):
    help = "Lista empresas y cantidad de rubros/subrubros por empresa."

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            default=None,
            help="Solo mostrar esta empresa (por nombre, sin distinguir mayúsculas).",
        )

    def handle(self, *args, **options):
        filter_name = options.get("company")
        if filter_name:
            companies = Company.objects.filter(
                nombre__icontains=filter_name.strip()
            ).order_by("nombre")
            if not companies.exists():
                self.stdout.write(
                    self.style.WARNING(f"Ninguna empresa coincide con '{filter_name}'.")
                )
                return
        else:
            companies = Company.objects.all().order_by("nombre")

        for c in companies:
            n_rubros = Rubro.objects.filter(company=c).count()
            n_sub = Subrubro.objects.filter(company=c).count()
            msg = f"  {c.nombre} (id={c.pk}): {n_rubros} rubros, {n_sub} subrubros"
            if n_rubros == 0 and n_sub == 0:
                self.stdout.write(self.style.WARNING(msg))
            else:
                self.stdout.write(self.style.SUCCESS(msg))

        self.stdout.write("")
        self.stdout.write(
            "Si Nocito tiene 0 rubros: ejecutá load_rubros_subrubros con el JSON."
        )
        self.stdout.write(
            "Si Nocito tiene 10 rubros pero en la web no se ven: cerrá sesión, entrá de nuevo y elegí Nocito."
        )
