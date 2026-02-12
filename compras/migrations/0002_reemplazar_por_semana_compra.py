# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("compras", "0001_initial"),
        ("general", "0010_backfill_admin_and_presupuestos"),
    ]

    operations = [
        migrations.DeleteModel(name="OrdenCompraItem"),
        migrations.DeleteModel(name="OrdenCompra"),
        migrations.CreateModel(
            name="Semana",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateField(help_text="Fecha de la semana (ej: lunes)")),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="semanas_compras",
                        to="general.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "Semana",
                "verbose_name_plural": "Semanas",
                "ordering": ["-fecha"],
                "unique_together": {("company", "fecha")},
            },
        ),
        migrations.CreateModel(
            name="Compra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item", models.CharField(help_text="Descripción del ítem", max_length=255)),
                (
                    "forma_pago",
                    models.CharField(
                        choices=[
                            ("efectivo", "Efectivo"),
                            ("transferencia", "Transferencia"),
                            ("cheque", "Cheque"),
                            ("tarjeta", "Tarjeta"),
                            ("otro", "Otro"),
                        ],
                        default="transferencia",
                        max_length=20,
                    ),
                ),
                ("monto_total", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("numero_ppto_fc", models.CharField(blank=True, max_length=80, verbose_name="Nº de PPTO/FC")),
                ("fecha_factura", models.DateField(blank=True, null=True)),
                ("monto_sin_iva", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("iva_21", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("iva_105", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("perc_iibb", models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name="PERC. IIBB")),
                ("monto_a_pagar", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name="Monto a pagar $")),
                ("observaciones", models.TextField(blank=True)),
                ("porcentaje_pago", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name="% de pago")),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("pagado", "Pagado"),
                            ("parcial", "Parcial"),
                            ("cancelado", "Cancelado"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("es_subcontrato", models.BooleanField(default=False)),
                (
                    "obra",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras",
                        to="general.obra",
                    ),
                ),
                (
                    "proveedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras",
                        to="general.proveedor",
                    ),
                ),
                (
                    "rubro",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras",
                        to="general.rubro",
                    ),
                ),
                (
                    "semana",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compras",
                        to="compras.semana",
                    ),
                ),
                (
                    "subrubro",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras",
                        to="general.subrubro",
                    ),
                ),
            ],
            options={
                "verbose_name": "Compra",
                "verbose_name_plural": "Compras",
                "ordering": ["obra__nombre", "rubro__nombre", "subrubro__nombre"],
            },
        ),
    ]
