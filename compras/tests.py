from django.core.exceptions import ValidationError
from django.test import TestCase

from compras.models import Compra, Semana
from general.models import Company, Obra, Proveedor, Rubro, Subrubro


class CompraValidationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(nombre="Empresa Compras")
        self.semana = Semana.objects.create(company=self.company, fecha="2026-01-05")
        self.rubro_a = Rubro.objects.create(company=self.company, nombre="Rubro A")
        self.rubro_b = Rubro.objects.create(company=self.company, nombre="Rubro B")
        self.subrubro_b = Subrubro.objects.create(
            company=self.company,
            rubro=self.rubro_b,
            nombre="Subrubro B",
        )
        self.obra = Obra.objects.create(company=self.company, nombre="Obra 1")
        self.proveedor = Proveedor.objects.create(company=self.company, nombre="Prov 1")

    def test_compra_valida_relacion_rubro_subrubro(self):
        compra = Compra(
            semana=self.semana,
            obra=self.obra,
            rubro=self.rubro_a,
            subrubro=self.subrubro_b,
            item="Compra inválida",
            proveedor=self.proveedor,
            monto_total=1000,
        )
        with self.assertRaises(ValidationError):
            compra.full_clean()
