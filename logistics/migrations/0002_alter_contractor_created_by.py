# Generated by Django 4.1.7 on 2023-04-09 18:37

import common.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("logistics", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contractor",
            name="created_by",
            field=models.ForeignKey(
                default=common.utils.get_current_user_id,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contractor",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кем создан",
            ),
        ),
    ]
