import uuid

from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from model_utils import FieldTracker
from phonenumber_field.modelfields import PhoneNumberField

from common.model_fields import (
    get_field_from_choices,
    AmountField,
    LatitudeField,
    LongitudeField,
)
from common.models import (
    BaseModel,
    BaseNameDescModel,
    BaseNameModel,
    AddressFieldsModelMixin,
)
from common.utils import get_current_user_id
from company.signals import verification_status_changed
from user.models import UserRole, UserStatus

User = get_user_model()


def company_storage(instance, filename):
    ext = filename.split(".")[-1]
    uuid_filename = "{}.{}".format(uuid.uuid4(), ext)
    return "company_storage/{0}".format(uuid_filename)


class Region(BaseNameModel):
    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        db_table = "regions"


class City(BaseNameModel):
    region = models.ForeignKey(
        Region, verbose_name="Район", on_delete=models.SET_NULL, null=True
    )
    latitude = LatitudeField(null=True, blank=True)
    longitude = LongitudeField(null=True, blank=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        db_table = "cities"


class CompanyStatus(models.IntegerChoices):
    NOT_VERIFIED = 1, "Не проверенная"
    VERIFIED = 2, "Проверенная"
    RELIABLE = 3, "Надежная"


class Company(AddressFieldsModelMixin, BaseNameDescModel):
    # Main
    image = models.ImageField(
        "Фото/логотип", upload_to=company_storage, null=True, blank=True
    )

    # bank information
    inn = models.CharField(
        "ИНН", unique=True, db_index=True, max_length=32, blank=True
    )
    bic = models.CharField(
        "БИК", unique=False, max_length=15, null=True, blank=True
    )
    payment_account = models.CharField(
        "Расчетный счет", unique=True, max_length=32, null=True, blank=True
    )
    correction_account = models.CharField(
        "Корресп. счет", unique=False, max_length=32, null=True, blank=True
    )
    bank_name = models.CharField(
        "Наименование банка",
        unique=False,
        max_length=100,
        null=True,
        blank=True,
    )
    status = get_field_from_choices(
        "Статус", CompanyStatus, default=CompanyStatus.NOT_VERIFIED
    )
    head_full_name = models.CharField(
        "ФИО директора", max_length=100, null=True
    )

    owner = models.OneToOneField(
        User,
        verbose_name="Владелец",
        on_delete=models.PROTECT,
        related_name="my_company",
        limit_choices_to={"role": UserRole.COMPANY_ADMIN},
        null=True,
        blank=True,
    )
    manager = models.ForeignKey(
        User,
        verbose_name="Менеджер",
        on_delete=models.PROTECT,
        related_name="companies",
        limit_choices_to={"is_staff": True},
        null=True,
        blank=True,
    )
    with_nds = models.BooleanField("С НДС", default=False)

    # Contacts
    email = models.EmailField("Электронная почта", default="", blank=True)
    phone = PhoneNumberField("Номер телефона", db_index=True)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        db_table = "companies"


class CompanyDocumentType(models.IntegerChoices):
    CHARTER = 1, "Устав"
    REQUISITES = 2, "Реквизиты"
    INN = 3, "ИНН"


class CompanyDocument(BaseModel):
    company = models.ForeignKey(
        "company.Company",
        verbose_name="Компания",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = get_field_from_choices(
        "Тип документа", CompanyDocumentType, null=True, blank=True
    )
    file = models.FileField("Документ", upload_to=company_storage)
    comment = models.CharField(
        "Комментарий", max_length=64, default="", blank=True
    )

    class Meta:
        verbose_name = "Документ компании"
        verbose_name_plural = "Документы компаний"
        db_table = "company_documents"


class CompanyRecyclablesActionType(models.IntegerChoices):
    BUY = 1, "Покупаю"
    SELL = 2, "Продаю"


class CompanyRecyclables(BaseModel):
    company = models.ForeignKey(
        "company.Company",
        verbose_name="Компания",
        on_delete=models.CASCADE,
        related_name="recyclables",
    )
    recyclables = models.ForeignKey(
        "product.Recyclables",
        verbose_name="Вторсырье",
        on_delete=models.PROTECT,
    )
    action = get_field_from_choices(
        "Действие",
        CompanyRecyclablesActionType,
        default=CompanyRecyclablesActionType.BUY,
    )
    monthly_volume = models.FloatField("Примерный ежемесячный объем")
    price = AmountField("Цена")

    class Meta:
        verbose_name = "Тип вторсырья компании"
        verbose_name_plural = "Типы вторсырья компаний"
        db_table = "company_recyclables"


class ActivityType(models.IntegerChoices):
    SUPPLIER = 1, "Поставщик"
    PROCESSOR = 2, "Переработчик"
    BUYER = 3, "Покупатель"


class RecyclingCollectionType(BaseNameModel):
    activity = get_field_from_choices("Вид деятельности", ActivityType)
    color = ColorField(default="#FF0000")

    class Meta:
        verbose_name = "Тип сбора/переработки"
        verbose_name_plural = "Типы сбора/переработки"
        db_table = "recycling_collection_types"
        unique_together = ("name", "activity")


class CompanyAdvantage(BaseNameModel):
    activity = get_field_from_choices("Вид деятельности", ActivityType)

    class Meta:
        verbose_name = "Преимущество компании"
        verbose_name_plural = "Преимущества компании"
        db_table = "company_advantages"
        unique_together = ("name", "activity")


class CompanyActivityType(BaseModel):
    company = models.ForeignKey(
        "company.Company",
        verbose_name="Компания",
        on_delete=models.CASCADE,
        related_name="activity_types",
    )
    activity = get_field_from_choices("Вид деятельности", ActivityType)
    rec_col_types = models.ManyToManyField(
        "company.RecyclingCollectionType",
        verbose_name="Тип сбора/переработки",
        blank=True,
    )
    advantages = models.ManyToManyField(
        "company.CompanyAdvantage",
        verbose_name="Преимущества компании",
        blank=True,
    )

    class Meta:
        verbose_name = "Виды деятельности компании"
        verbose_name_plural = "Виды деятельности компаний"
        db_table = "company_activity_types"
        # unique_together = ("company", "activity")


class ContactType(models.IntegerChoices):
    PHONE = 1, "Телефон"
    EMAIL = 2, "Электронная почта"
    WHATSAPP = 3, "Whatsapp"
    TELEGRAM = 4, "Telegram"


class CompanyAdditionalContact(BaseModel):
    company = models.ForeignKey(
        "company.Company",
        verbose_name="Компания",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    contact_type = get_field_from_choices("Тип", ContactType)
    value = models.CharField("Контакт", max_length=32)
    comment = models.TextField("Комментарий", default="", blank=True)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Контакт компании"
        verbose_name_plural = "Контакты компаний"
        db_table = "company_contacts"


class CompanyVerificationRequestStatus(models.IntegerChoices):
    NEW = 1, "Новая"
    VERIFIED = 2, "Проверенная"
    RELIABLE = 3, "Надежная"
    DECLINE = 4, "Отклонена"


class CompanyVerificationRequest(BaseModel):
    company = models.ForeignKey(
        "company.Company",
        verbose_name="Компания",
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    employee = models.ForeignKey(
        User,
        verbose_name="Сотрудник",
        on_delete=models.CASCADE,
        default=get_current_user_id,
        related_name="verifications",
    )
    status = get_field_from_choices(
        "Статус",
        CompanyVerificationRequestStatus,
        default=CompanyVerificationRequestStatus.NEW,
    )
    comment = models.TextField("Комментарий", default="", blank=True)

    status_tracker = FieldTracker(fields=["status"])

    class Meta:
        verbose_name = "Заявка на верификацию"
        verbose_name_plural = "Заявки на верификацию"
        db_table = "company_verification_requests"
        get_latest_by = "-created_at"
        ordering = ["-created_at"]

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        created = False
        if self.pk is None:
            created = True

        # delete previously created unprocessed requests
        if created:
            self.company.verifications.filter(
                status=CompanyVerificationRequestStatus.NEW
            ).delete()

        company_changed = False
        employee_changed = False
        status_changed = self.status_tracker.changed()

        if status_changed:
            if self.status == CompanyVerificationRequestStatus.VERIFIED:
                self.company.status = CompanyStatus.VERIFIED
                self.employee.status = UserStatus.VERIFIED
                company_changed = employee_changed = True

                verification_status_changed.send_robust(
                    self.__class__, instance=self
                )

            if self.status == CompanyVerificationRequestStatus.RELIABLE:
                self.company.status = CompanyStatus.RELIABLE
                company_changed = True

                verification_status_changed.send_robust(
                    self.__class__, instance=self
                )

                if self.employee.status == UserStatus.NOT_VERIFIED:
                    self.employee.status = UserStatus.VERIFIED
                    employee_changed = True

        if company_changed:
            self.company.save()
        if employee_changed:
            self.employee.save()

        super().save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        return reverse("company_verification-detail", kwargs={"pk": self.pk})
