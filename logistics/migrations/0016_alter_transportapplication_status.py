# Generated by Django 4.1.7 on 2023-07-21 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0015_alter_transportapplication_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transportapplication",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Назначение логиста"),
                    (2, "Машина загружена"),
                    (3, "Машина выгружена"),
                    (4, "Окончательная приемка"),
                    (5, "Выполнена"),
                    (6, "Отменена"),
                ],
                default=1,
                verbose_name="Статус",
            ),
        ),
    ]
