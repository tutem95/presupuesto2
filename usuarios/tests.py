from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from general.models import Company, CompanyMembership, CompanyMembershipSection, Section


class LoginRoutingTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.section_presupuestos = Section.objects.get_or_create(
            code="presupuestos",
            defaults={"nombre": "Presupuestos"},
        )[0]
        self.section_compras = Section.objects.get_or_create(
            code="compras",
            defaults={"nombre": "Compras"},
        )[0]
        self.section_sueldos = Section.objects.get_or_create(
            code="sueldos",
            defaults={"nombre": "Sueldos"},
        )[0]

    def _create_user_with_company_membership(
        self,
        username,
        company,
        section=None,
        with_admin_owner=True,
    ):
        user = self.User.objects.create_user(username=username, password="pw12345")
        if with_admin_owner:
            owner = self.User.objects.create_user(
                username=f"{username}_owner",
                password="pw12345",
            )
            CompanyMembership.objects.create(user=owner, company=company, is_admin=True)
        membership = CompanyMembership.objects.create(
            user=user,
            company=company,
            is_admin=False,
        )
        if section is not None:
            CompanyMembershipSection.objects.create(
                membership=membership,
                section=section,
            )
        return user, membership

    def test_login_usuario_con_una_empresa_y_acceso_compras_redirige_a_compras(self):
        company = Company.objects.create(nombre="Empresa Compras")
        user, membership = self._create_user_with_company_membership(
            "user_compras",
            company,
            section=self.section_compras,
        )

        response = self.client.post(
            reverse("usuarios:login"),
            {"username": user.username, "password": "pw12345"},
        )
        self.assertRedirects(response, reverse("compras:compras_list"))
        self.assertEqual(self.client.session.get("company_id"), membership.company_id)

    def test_login_usuario_sin_secciones_redirige_a_sin_empresa(self):
        company = Company.objects.create(nombre="Empresa Sin Secciones")
        user, _ = self._create_user_with_company_membership(
            "user_sin_secciones",
            company,
            section=None,
        )

        response = self.client.post(
            reverse("usuarios:login"),
            {"username": user.username, "password": "pw12345"},
        )
        self.assertRedirects(response, reverse("usuarios:no_company"))

    def test_company_select_redirige_a_home_de_la_seccion_elegida(self):
        user = self.User.objects.create_user(username="selector", password="pw12345")

        company_compras = Company.objects.create(nombre="Empresa Compras")
        owner_1 = self.User.objects.create_user(username="owner_c1", password="pw12345")
        CompanyMembership.objects.create(
            user=owner_1,
            company=company_compras,
            is_admin=True,
        )
        membership_compras = CompanyMembership.objects.create(
            user=user,
            company=company_compras,
            is_admin=False,
        )
        CompanyMembershipSection.objects.create(
            membership=membership_compras,
            section=self.section_compras,
        )

        company_sueldos = Company.objects.create(nombre="Empresa Sueldos")
        owner_2 = self.User.objects.create_user(username="owner_c2", password="pw12345")
        CompanyMembership.objects.create(
            user=owner_2,
            company=company_sueldos,
            is_admin=True,
        )
        membership_sueldos = CompanyMembership.objects.create(
            user=user,
            company=company_sueldos,
            is_admin=False,
        )
        CompanyMembershipSection.objects.create(
            membership=membership_sueldos,
            section=self.section_sueldos,
        )

        self.client.login(username="selector", password="pw12345")
        response = self.client.post(
            reverse("usuarios:company_select"),
            {"company_id": str(company_sueldos.pk)},
        )
        self.assertRedirects(response, reverse("empleados:index"))
        self.assertEqual(self.client.session.get("company_id"), company_sueldos.pk)
