# Generated by Django 4.1.7 on 2023-10-16 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exchange", "0021_alter_equipmentapplication_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentmodel",
            name="document_type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Договор поставки"),
                    (2, "Транспортная накладная УПД"),
                    (3, "Доверенность на водителя"),
                ],
                null=True,
                verbose_name="Тип документа",
            ),
        ),
    ]
