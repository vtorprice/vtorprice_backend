# Generated by Django 4.1.3 on 2023-01-30 19:31

import common.model_fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import exchange.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("company", "0008_alter_companyactivitytype_advantages_and_more"),
        ("product", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImageModel",
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
                    "image",
                    models.ImageField(
                        upload_to=exchange.models.exchange_storage,
                        verbose_name="Изображение",
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                        verbose_name="Тип контента",
                    ),
                ),
            ],
            options={
                "verbose_name": "Изображение",
                "verbose_name_plural": "Изображения",
                "db_table": "images",
            },
        ),
        migrations.CreateModel(
            name="RecyclablesApplication",
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
                    "deal_type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Покупка"), (2, "Продажа")],
                        verbose_name="Тип сделки",
                    ),
                ),
                (
                    "urgency_type",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Готово к отгрузке"),
                            (2, "Контракт на поставку"),
                        ],
                        verbose_name="Срочность",
                    ),
                ),
                (
                    "with_nds",
                    models.BooleanField(default=False, verbose_name="С НДС"),
                ),
                (
                    "bale_count",
                    models.FloatField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Количество кип",
                    ),
                ),
                (
                    "bale_weight",
                    models.FloatField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Вес одной кипы",
                    ),
                ),
                (
                    "volume",
                    models.FloatField(
                        blank=True,
                        help_text="Указывается, если тип заявки контракт на поставку",
                        null=True,
                        verbose_name="Объем",
                    ),
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
                    "lot_size",
                    models.FloatField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        null=True,
                        verbose_name="Лотность",
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
                    "video_url",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        max_length=512,
                        verbose_name="Ссылка на видео",
                    ),
                ),
                (
                    "comment",
                    models.TextField(
                        blank=True, default="", verbose_name="Комментарий"
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=1024,
                        verbose_name="Адрес",
                    ),
                ),
                (
                    "latitude",
                    common.model_fields.LatitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                        verbose_name="Широта",
                    ),
                ),
                (
                    "longitude",
                    common.model_fields.LongitudeField(
                        blank=True,
                        decimal_places=15,
                        max_digits=18,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                        verbose_name="Долгота",
                    ),
                ),
                (
                    "city",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="company.city",
                        verbose_name="Город",
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="company.company",
                        verbose_name="Компания",
                    ),
                ),
                (
                    "images",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Указывается, если тип заявки готово к отгрузке",
                        to="exchange.imagemodel",
                        verbose_name="Фотографии вторсырья",
                    ),
                ),
                (
                    "recyclables",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product.recyclables",
                        verbose_name="Вторсырье",
                    ),
                ),
            ],
            options={
                "verbose_name": "Заявка по вторсырью",
                "verbose_name_plural": "Заявки по вторсырью",
                "db_table": "recyclables_applications",
            },
        ),
    ]
