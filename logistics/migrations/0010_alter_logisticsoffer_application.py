# Generated by Django 4.1.7 on 2023-05-15 13:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0009_alter_transportapplication_content_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logisticsoffer",
            name="application",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="offers",
                to="logistics.transportapplication",
            ),
        ),
    ]
