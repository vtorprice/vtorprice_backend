# Generated by Django 4.1.3 on 2023-03-18 14:48

import common.model_fields
import common.utils
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0008_alter_companyactivitytype_advantages_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("exchange", "0004_remove_recyclablesapplication_images_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecyclablesDeal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        default=False, verbose_name="Помечен как удаленный"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата добавления"
                    ),
                ),
                (
                    "with_nds",
                    models.BooleanField(default=False, verbose_name="С НДС"),
                ),
                (
                    "price",
                    common.model_fields.AmountField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        verbose_name="Цена за единицу веса",
                    ),
                ),
                (
                    "is_packing_deduction",
                    models.BooleanField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Упаковка вычитается",
                    ),
                ),
                (
                    "packing_deduction_type",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (1, "На упаковку с каждой кипы"),
                            (2, "На упаковку с общего веса"),
                        ],
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Вычет",
                    ),
                ),
                (
                    "packing_deduction_value",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Значение вычета",
                    ),
                ),
                (
                    "comment",
                    models.TextField(
                        blank=True, default="", verbose_name="Комментарий"
                    ),
                ),
                (
                    "status",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Согласование условий"),
                            (2, "Назначена отгрузка"),
                            (3, "Назначение логиста"),
                            (4, "Машина загружена"),
                            (5, "Машина выгружена"),
                            (6, "Окончательная приемка"),
                            (7, "Сделка закрыта"),
                            (8, "Проблемная сделка"),
                            (9, "Сделка отменена"),
                        ],
                        default=1,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "weight",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Вес партии в кг"
                    ),
                ),
                (
                    "packing",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=128,
                        verbose_name="Упаковка",
                    ),
                ),
                (
                    "weediness",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Сорность в %"
                    ),
                ),
                (
                    "moisture",
                    models.FloatField(
                        blank=True,
                        null=True,
                        verbose_name="Влага или посторонние включения в %",
                    ),
                ),
                (
                    "payment_term",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "По факту погрузки"),
                            (2, "По факту выгрузки"),
                            (3, "Другое"),
                        ],
                        default=1,
                        verbose_name="Условие оплаты",
                    ),
                ),
                (
                    "other_payment_term",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=128,
                        verbose_name="Иное условие оплаты",
                    ),
                ),
                (
                    "loaded_weight",
                    models.FloatField(
                        blank=True,
                        help_text="Поле для справки, не влияет на расчет стоимости",
                        null=True,
                        verbose_name="Загруженный вес",
                    ),
                ),
                (
                    "accepted_weight",
                    models.FloatField(
                        blank=True,
                        help_text="Поле для справки, не влияет на расчет стоимости",
                        null=True,
                        verbose_name="Принятый вес",
                    ),
                ),
                (
                    "shipping_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Дата отгрузки"
                    ),
                ),
                (
                    "who_delivers",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Поставщик"),
                            (2, "Покупатель"),
                            (3, "ВторПрайс"),
                        ],
                        default=3,
                        verbose_name="Кто доставляет",
                    ),
                ),
                (
                    "buyer_pays_shipping",
                    models.BooleanField(
                        default=True,
                        verbose_name="Доставку оплачивает покупатель",
                    ),
                ),
                (
                    "shipping_address",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=1024,
                        verbose_name="Адрес отгрузки",
                    ),
                ),
                (
                    "shipping_latitude",
                    common.model_fields.LatitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                        verbose_name="Широта адреса отгрузки",
                    ),
                ),
                (
                    "shipping_longitude",
                    common.model_fields.LongitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                        verbose_name="Долгота адреса отгрузки",
                    ),
                ),
                (
                    "delivery_address",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=1024,
                        verbose_name="Адрес доставки",
                    ),
                ),
                (
                    "delivery_latitude",
                    common.model_fields.LatitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                        verbose_name="Широта адреса доставки",
                    ),
                ),
                (
                    "delivery_longitude",
                    common.model_fields.LongitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                        verbose_name="Долгота адреса доставки",
                    ),
                ),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="deals",
                        to="exchange.recyclablesapplication",
                        verbose_name="Заявка",
                    ),
                ),
                (
                    "buyer_company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recyclables_buy_deals",
                        to="company.company",
                        verbose_name="Покупатель",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        default=common.utils.get_current_user_id,
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recyclables_deals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь создавший сделку",
                    ),
                ),
                (
                    "delivery_city",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="delivery_recyclables_deal",
                        to="company.city",
                        verbose_name="Город доставки",
                    ),
                ),
                (
                    "shipping_city",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="shipping_recyclables_deal",
                        to="company.city",
                        verbose_name="Город отгрузки",
                    ),
                ),
                (
                    "supplier_company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recyclables_sell_deals",
                        to="company.company",
                        verbose_name="Поставщик",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сделка по вторсырью",
                "verbose_name_plural": "Сделка по вторсырью",
                "db_table": "recyclables_deals",
            },
        ),
    ]
