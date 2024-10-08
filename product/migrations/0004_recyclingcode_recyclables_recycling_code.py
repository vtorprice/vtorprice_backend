# Generated by Django 4.1.7 on 2023-10-09 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0003_alter_equipment_category_alter_equipment_table"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecyclingCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        default=False, verbose_name="Помечен как удаленный"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата добавления"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True, max_length=1024, verbose_name="Название"
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, default="", verbose_name="Описание"
                    ),
                ),
                (
                    "gost_name",
                    models.CharField(
                        db_index=True,
                        max_length=10,
                        null=True,
                        unique=True,
                        verbose_name="ГОСТ 24888-81",
                    ),
                ),
            ],
            options={
                "verbose_name": "Код переработки",
                "verbose_name_plural": "Коды переработки",
                "db_table": "recycling_codes",
            },
        ),
        migrations.AddField(
            model_name="recyclables",
            name="recycling_code",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recyclables",
                to="product.recyclingcode",
                verbose_name="Код переработки",
            ),
        ),
    ]
