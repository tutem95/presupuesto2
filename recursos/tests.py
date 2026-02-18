from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from general.models import (
    CategoriaMaterial,
    Company,
    CompanyMembership,
    CompanyMembershipSection,
    Equipo,
    Proveedor,
    RefEquipo,
    Rubro,
    Section,
    Subrubro,
    TipoMaterial,
    Unidad,
)
from recursos.models import (
    HojaPrecios,
    HojaPreciosManoDeObra,
    HojaPreciosSubcontrato,
    Lote,
    ManoDeObra,
    Material,
    Subcontrato,
    Tarea,
    TareaRecurso,
)


class LoteCreationAtomicityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="planner", password="pw12345")
        owner = User.objects.create_user(username="owner", password="pw12345")
        self.company = Company.objects.create(nombre="Empresa Lotes")
        CompanyMembership.objects.create(user=owner, company=self.company, is_admin=True)

        membership = CompanyMembership.objects.create(
            user=self.user,
            company=self.company,
            is_admin=False,
        )
        section_presupuestos = Section.objects.get_or_create(
            code="presupuestos",
            defaults={"nombre": "Presupuestos"},
        )[0]
        CompanyMembershipSection.objects.create(
            membership=membership,
            section=section_presupuestos,
        )

        self.client.login(username="planner", password="pw12345")
        session = self.client.session
        session["company_id"] = self.company.pk
        session.save()

    def test_lote_create_hace_rollback_si_falla_un_paso_intermedio(self):
        client = Client(raise_request_exception=False)
        client.login(username="planner", password="pw12345")
        session = client.session
        session["company_id"] = self.company.pk
        session.save()

        nombre_lote = "Lote Atomico"
        with patch(
            "recursos.views._create_hoja_mo_vacia",
            side_effect=RuntimeError("fallo forzado"),
        ):
            response = client.post(
                reverse("recursos:lote_create"),
                {"nombre": nombre_lote},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("recursos:lote_create"))
        self.assertFalse(
            HojaPrecios.objects.filter(company=self.company, nombre=nombre_lote).exists()
        )
        self.assertFalse(
            HojaPreciosManoDeObra.objects.filter(
                company=self.company,
                nombre=nombre_lote,
            ).exists()
        )
        self.assertFalse(
            HojaPreciosSubcontrato.objects.filter(
                company=self.company,
                nombre=nombre_lote,
            ).exists()
        )
        self.assertFalse(
            Lote.objects.filter(company=self.company, nombre=nombre_lote).exists()
        )

    def test_lote_create_crea_estructura_completa_en_flujo_normal(self):
        nombre_lote = "Lote Exitoso"
        response = self.client.post(
            reverse("recursos:lote_create"),
            {"nombre": nombre_lote},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("tareas"))
        self.assertTrue(
            HojaPrecios.objects.filter(company=self.company, nombre=nombre_lote).exists()
        )
        self.assertTrue(
            HojaPreciosManoDeObra.objects.filter(
                company=self.company,
                nombre=nombre_lote,
            ).exists()
        )
        self.assertTrue(
            HojaPreciosSubcontrato.objects.filter(
                company=self.company,
                nombre=nombre_lote,
            ).exists()
        )
        self.assertTrue(
            Lote.objects.filter(company=self.company, nombre=nombre_lote).exists()
        )


class TareaRecursoConstraintTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(nombre="Empresa Constraint")
        self.rubro = Rubro.objects.create(company=self.company, nombre="Rubro 1")
        self.subrubro = Subrubro.objects.create(
            company=self.company,
            rubro=self.rubro,
            nombre="Subrubro 1",
        )
        self.unidad = Unidad.objects.create(company=self.company, nombre="u")
        self.tipo_material = TipoMaterial.objects.create(
            company=self.company,
            nombre="Tipo 1",
        )
        self.categoria = CategoriaMaterial.objects.create(
            company=self.company,
            tipo=self.tipo_material,
            nombre="Categoria 1",
        )
        self.proveedor = Proveedor.objects.create(company=self.company, nombre="Prov")
        self.equipo = Equipo.objects.create(company=self.company, nombre="Equipo 1")
        self.ref_equipo = RefEquipo.objects.create(
            company=self.company,
            equipo=self.equipo,
            nombre="Ref 1",
        )

        self.material = Material.objects.create(
            company=self.company,
            nombre="Material 1",
            proveedor=self.proveedor,
            tipo=self.tipo_material,
            categoria=self.categoria,
            unidad_de_venta=self.unidad,
            cantidad_por_unidad_venta=1,
            precio_unidad_venta=100,
            moneda="ARS",
        )
        self.mano_de_obra = ManoDeObra.objects.create(
            company=self.company,
            rubro=self.rubro,
            subrubro=self.subrubro,
            tarea="Puesto 1",
            equipo=self.equipo,
            ref_equipo=self.ref_equipo,
            cantidad_por_unidad_venta=1,
            unidad_de_venta=self.unidad,
            precio_unidad_venta=50,
        )
        self.subcontrato = Subcontrato.objects.create(
            company=self.company,
            rubro=self.rubro,
            subrubro=self.subrubro,
            tarea="Subc 1",
            proveedor=self.proveedor,
            cantidad_por_unidad_venta=1,
            unidad_de_venta=self.unidad,
            precio_unidad_venta=25,
            moneda="ARS",
        )

        hoja_materiales = HojaPrecios.objects.create(
            company=self.company,
            nombre="Hoja Mat",
        )
        hoja_mo = HojaPreciosManoDeObra.objects.create(
            company=self.company,
            nombre="Hoja MO",
        )
        hoja_sub = HojaPreciosSubcontrato.objects.create(
            company=self.company,
            nombre="Hoja Sub",
        )
        self.lote = Lote.objects.create(
            company=self.company,
            nombre="Lote 1",
            hoja_materiales=hoja_materiales,
            hoja_mano_de_obra=hoja_mo,
            hoja_subcontratos=hoja_sub,
        )
        self.tarea = Tarea.objects.create(
            company=self.company,
            lote=self.lote,
            nombre="Tarea 1",
            rubro=self.rubro,
            subrubro=self.subrubro,
        )

    def test_db_constraint_exige_un_unico_recurso(self):
        with self.assertRaises(IntegrityError):
            TareaRecurso.objects.create(
                tarea=self.tarea,
                material=self.material,
                mano_de_obra=self.mano_de_obra,
                cantidad=1,
            )

    def test_db_constraint_exige_cantidad_positiva(self):
        with self.assertRaises(IntegrityError):
            TareaRecurso.objects.create(
                tarea=self.tarea,
                subcontrato=self.subcontrato,
                cantidad=0,
            )
