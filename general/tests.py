from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from general.models import Company, CompanyMembership, CompanyMembershipSection, Section


class SectionAccessMiddlewareTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="comprador", password="pw12345")
        owner = User.objects.create_user(username="owner", password="pw12345")
        self.company = Company.objects.create(nombre="Empresa Test")

        # Evita que la señal convierta al usuario de prueba en admin.
        CompanyMembership.objects.create(user=owner, company=self.company, is_admin=True)
        self.membership = CompanyMembership.objects.create(
            user=self.user,
            company=self.company,
            is_admin=False,
        )

        self.section_compras = Section.objects.get_or_create(
            code="compras",
            defaults={"nombre": "Compras"},
        )[0]
        Section.objects.get_or_create(
            code="presupuestos",
            defaults={"nombre": "Presupuestos"},
        )
        Section.objects.get_or_create(
            code="sueldos",
            defaults={"nombre": "Sueldos"},
        )
        CompanyMembershipSection.objects.create(
            membership=self.membership,
            section=self.section_compras,
        )

        self.client.login(username="comprador", password="pw12345")
        session = self.client.session
        session["company_id"] = self.company.pk
        session.save()

    def test_usuario_compras_puede_entrar_a_modulo_compras(self):
        response = self.client.get(reverse("compras:compras_list"))
        self.assertEqual(response.status_code, 200)

    def test_usuario_compras_no_puede_entrar_a_modulo_presupuestos(self):
        response = self.client.get(reverse("general:indice"))
        self.assertRedirects(response, reverse("no_section_access"))

    def test_usuario_compras_no_puede_entrar_a_modulo_sueldos(self):
        response = self.client.get(reverse("empleados:index"))
        self.assertRedirects(response, reverse("no_section_access"))
