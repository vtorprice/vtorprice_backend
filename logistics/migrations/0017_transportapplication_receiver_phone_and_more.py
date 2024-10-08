# Generated by Django 4.1.7 on 2023-08-01 12:35

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0016_alter_transportapplication_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="transportapplication",
            name="receiver_phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                max_length=128,
                null=True,
                region=None,
                verbose_name="Номер телефона получателя",
            ),
        ),
        migrations.AddField(
            model_name="transportapplication",
            name="sender_phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                max_length=128,
                null=True,
                region=None,
                verbose_name="Номер телефона отправителя",
            ),
        ),
    ]
