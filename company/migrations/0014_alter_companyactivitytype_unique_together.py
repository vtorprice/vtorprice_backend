# Generated by Django 4.1.7 on 2023-09-21 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0013_auto_20230803_1411"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="companyactivitytype",
            unique_together=set(),
        ),
    ]
