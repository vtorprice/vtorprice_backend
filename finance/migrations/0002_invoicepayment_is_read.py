# Generated by Django 4.1.7 on 2023-07-24 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoicepayment",
            name="is_read",
            field=models.BooleanField(default=False, verbose_name="Прочитано"),
        ),
    ]
