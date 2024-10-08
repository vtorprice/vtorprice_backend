# Generated by Django 4.1.7 on 2023-10-12 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_user_updated_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Супер-Администратор"),
                    (2, "Администратор"),
                    (3, "Менеджер"),
                    (4, "Логист"),
                    (5, "Пользователь"),
                ],
                default=5,
                verbose_name="Роль",
            ),
        ),
    ]
