# Generated by Django 4.1.3 on 2023-02-04 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exchange", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="recyclablesapplication",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "На проверке"),
                    (2, "Опубликована"),
                    (3, "Завершена"),
                    (4, "Отклонена"),
                ],
                default=1,
                verbose_name="Статус",
            ),
        ),
    ]
