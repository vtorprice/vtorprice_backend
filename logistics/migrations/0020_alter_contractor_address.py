# Generated by Django 4.1.7 on 2023-09-28 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0019_transportapplication_accepted_weight"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contractor",
            name="address",
            field=models.CharField(
                blank=True,
                default="",
                max_length=1024,
                null=True,
                verbose_name="Адрес",
            ),
        ),
    ]
