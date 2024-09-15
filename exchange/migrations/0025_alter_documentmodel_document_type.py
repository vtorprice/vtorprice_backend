# Generated by Django 4.1.7 on 2023-10-19 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "exchange",
            "0024_rename_total_weight_recyclablesapplication_full_weigth",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentmodel",
            name="document_type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Договор на отгрузку"),
                    (2, "Договор-заявка"),
                    (3, "Товарно-транспортная накладная"),
                    (4, "Счет-фактура"),
                    (5, "Договор приложение спецификация"),
                    (6, "Унифицированный транспортный документ"),
                    (7, "Акт"),
                    (8, "Платежный счет"),
                ],
                null=True,
                verbose_name="Тип документа",
            ),
        ),
    ]
