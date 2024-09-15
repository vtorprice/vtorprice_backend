from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from common.serializers import (
    NonNullDynamicFieldsModelSerializer,
    BaseCreateSerializer,
    LazyRefSerializer,
    BulkCreateListSerializer,
)
from company.models import (
    Company,
    CompanyDocument,
    CompanyRecyclables,
    CompanyAdditionalContact,
    CompanyVerificationRequest,
    RecyclingCollectionType,
    CompanyAdvantage,
    CompanyActivityType,
    City,
    ActivityType,
    CompanyRecyclablesActionType,
    CompanyStatus,
    Region,
)

from exchange.models import (
    ApplicationStatus,
    DealType,
    RecyclablesApplication,
    UrgencyType,
)
from product.api.serializers import RecyclablesSerializer
from user.models import UserRole


class CreateMyCompanyMixin:
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        user = self.context["request"].user
        if not internal.get("company") and getattr(user, "company", None):
            internal["company"] = user.company
            return internal

        if "company" not in internal:
            if (
                user.role != UserRole.COMPANY_ADMIN
                or getattr(user, "my_company", None) is None
            ):
                raise PermissionDenied
            internal["company"] = self.context["request"].user.my_company
        return internal


class RegionSerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = Region


class CitySerializer(NonNullDynamicFieldsModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = City


class CompanyDocumentSerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = CompanyDocument


class CompanySettingsMixin:
    def check_access(self, attrs):
        user = self.context["request"].user
        attrs = super().validate(attrs)
        company = attrs.get("company")
        company = company or user.company
        if (
            (user.role == UserRole.COMPANY_ADMIN and user.company != company)
            or (user.role == UserRole.MANAGER and company.manager != user)
            or user.role == UserRole.LOGIST
        ):
            raise PermissionDenied(
                "Вы должны быть в находиться компании или являться ее менеджером"
            )
        return attrs

    def validate(self, attrs):
        return self.check_access(attrs)


class CreateCompanyDocumentSerializer(
    CreateMyCompanyMixin, CompanySettingsMixin, BaseCreateSerializer
):
    class Meta:
        model = CompanyDocument
        extra_kwargs = {"company": {"required": False}}

    def to_representation(self, instance):
        return CompanyDocumentSerializer(instance).data


class CompanyRecyclablesSerializer(NonNullDynamicFieldsModelSerializer):
    recyclables = RecyclablesSerializer()

    class Meta:
        model = CompanyRecyclables


class BulkCreateCompanyRecyclablesSerializer(BulkCreateListSerializer):
    """
    Overridden to support the creation recyclables applications
    """

    def create(self, validated_data):

        to_create = []

        for item in validated_data:
            company = item["company"]
            if company.status in (
                CompanyStatus.RELIABLE,
                CompanyStatus.VERIFIED,
            ):
                status = ApplicationStatus.PUBLISHED
            else:
                status = ApplicationStatus.ON_REVIEW

            action = item["action"]
            if action == CompanyRecyclablesActionType.BUY:
                deal_type = DealType.BUY
            else:
                deal_type = DealType.SELL

            is_exists = RecyclablesApplication.objects.filter(
                company=company,
                deal_type=deal_type,
                volume=item["monthly_volume"],
                price=item["price"],
            ).exists()
            if not is_exists:
                to_create.append(
                    RecyclablesApplication(
                        recyclables=item["recyclables"],
                        company=company,
                        status=status,
                        urgency_type=UrgencyType.SUPPLY_CONTRACT,
                        deal_type=deal_type,
                        volume=item["monthly_volume"],
                        price=item["price"],
                        with_nds=company.with_nds,
                        city_id=company.city_id,
                        address=company.address,
                        latitude=company.latitude,
                        longitude=company.longitude,
                    )
                )

        RecyclablesApplication.objects.bulk_create(to_create)

        return super().create(validated_data)


class CreateCompanyRecyclablesSerializer(
    CompanySettingsMixin, CreateMyCompanyMixin, BaseCreateSerializer
):
    class Meta:
        model = CompanyRecyclables
        extra_kwargs = {"company": {"required": False}}

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # Set list serializer class for support bulk creation
        setattr(
            self.Meta,
            "list_serializer_class",
            BulkCreateCompanyRecyclablesSerializer,
        )

    def to_representation(self, instance):
        return CompanyRecyclablesSerializer(instance).data

    def create(self, validated_data):
        to_delete_from_company = validated_data["company"]
        self.context["to_delete_from_company"] = to_delete_from_company
        return super().create(validated_data)


class CompanyAdditionalContactSerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = CompanyAdditionalContact


class CreateCompanyAdditionalContactSerializer(BaseCreateSerializer):
    class Meta:
        model = CompanyAdditionalContact

    def to_representation(self, instance):
        return CompanyAdditionalContactSerializer(instance).data


class RecyclingCollectionTypeSerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = RecyclingCollectionType


class CompanyAdvantageSerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = CompanyAdvantage


class CompanyActivityTypeSerializer(NonNullDynamicFieldsModelSerializer):
    rec_col_types = RecyclingCollectionTypeSerializer(many=True)
    advantages = CompanyAdvantageSerializer(many=True)

    class Meta:
        model = CompanyActivityType


class CreateCompanyActivityTypeSerializer(
    CreateMyCompanyMixin, CompanySettingsMixin, BaseCreateSerializer
):
    class Meta:
        model = CompanyActivityType

    def to_representation(self, instance):
        return CompanyActivityTypeSerializer(instance).data

    def create(self, validated_data):
        # Preliminary deletion of existing objects
        company = validated_data["company"]
        company.activity_types.filter(
            activity=validated_data["activity"]
        ).delete()
        return super().create(validated_data)

    def validate(self, data):

        rec_col_types = data.get("rec_col_types", [])

        if rec_col_types:
            not_match_rec_col_types_names = []

            for rec_col_type in data["rec_col_types"]:
                if rec_col_type.activity != data["activity"]:
                    not_match_rec_col_types_names.append(rec_col_type.name)

            if not_match_rec_col_types_names:
                message = (
                    "Выбранные типы сбора/переработки не соответствуют типу деятельности: "
                    + ", ".join(not_match_rec_col_types_names)
                )
                raise serializers.ValidationError({"rec_col_types": message})

        advantages = data.get("advantages", [])

        if advantages:
            not_match_advantages_names = []

            for advantage in data["advantages"]:
                if advantage.activity != data["activity"]:
                    not_match_advantages_names.append(advantage.name)

            if not_match_advantages_names:
                message = (
                    "Выбранные преимущества не соответствуют типу деятельности: "
                    + ", ".join(not_match_advantages_names)
                )
                raise serializers.ValidationError({"advantages": message})

        data = super().check_access(data)
        return data


class NonExistCompanySerializer(NonNullDynamicFieldsModelSerializer):
    class Meta:
        model = Company
        fields = ("name", "inn", "city", "address", "latitude", "longitude")


class ListCompanySerializer(NonNullDynamicFieldsModelSerializer):
    activities = serializers.SerializerMethodField()
    recyclables_type = serializers.SerializerMethodField()
    recyclables_count = serializers.IntegerField(read_only=True)
    recyclables = CompanyRecyclablesSerializer(many=True)
    application_types = serializers.SerializerMethodField()
    city = CitySerializer()
    reviews_count = serializers.SerializerMethodField(read_only=True)
    deals_count = serializers.SerializerMethodField(read_only=True)
    average_review_rate = serializers.SerializerMethodField(read_only=True)
    is_favorite = serializers.BooleanField(
        read_only=True, required=False, default=False
    )

    class Meta:
        model = Company

    def get_activities(self, obj):
        # FIXME: оптимизировать по запросам в БД
        activity_types = obj.activity_types.values_list(
            "activity", flat=True
        ).distinct()
        return [ActivityType(item).label for item in activity_types]

    def get_application_types(self, obj):
        # FIXME: оптимизировать по запросам в БД
        application_types = obj.recyclables.values_list(
            "action", flat=True
        ).distinct()
        return [
            CompanyRecyclablesActionType(item).label
            for item in application_types
        ]

    def get_recyclables_type(self, obj):
        # FIXME: оптимизировать по запросам в БД
        company_recyclables = obj.recyclables.select_related(
            "recyclables"
        ).first()
        if company_recyclables:
            return company_recyclables.recyclables.name
        return None

    def get_recyclables_count(self, obj):
        if obj.recyclables_count > 0:
            return obj.recyclables_count - 1
        return obj.recyclables_count

    def get_reviews_count(self, instance: Company):
        return instance.review_set.count()

    # FIXME: сделать через аннотацию
    def get_deals_count(self, instance: Company):
        return (
            instance.recyclables_sell_deals.count()
            + instance.recyclables_buy_deals.count()
            + instance.equipment_buy_deals.count()
            + instance.equipment_sell_deals.count()
        )

    def get_average_review_rate(self, instance: Company):
        return (
            instance.review_set.aggregate(models.Avg("rate"))["rate__avg"]
            or 0.0
        )


class CompanySerializer(NonNullDynamicFieldsModelSerializer):
    documents = CompanyDocumentSerializer(many=True)
    recyclables = CompanyRecyclablesSerializer(many=True)
    contacts = CompanyAdditionalContactSerializer(many=True)
    activity_types = CompanyActivityTypeSerializer(many=True)
    city = CitySerializer()
    manager = LazyRefSerializer(
        "user.api.serializers.UserSerializer", exclude=("company", "groups")
    )
    owner = LazyRefSerializer(
        "user.api.serializers.UserSerializer", exclude=("company", "groups")
    )
    recyclables_count = serializers.IntegerField(read_only=True)
    monthly_volume = serializers.FloatField(read_only=True)
    is_favorite = serializers.BooleanField(
        read_only=True, required=False, default=False
    )
    reviews_count = serializers.SerializerMethodField(read_only=True)
    deals_count = serializers.SerializerMethodField(read_only=True)
    average_review_rate = serializers.SerializerMethodField(read_only=True)
    reviews = serializers.SerializerMethodField()

    def get_reviews(self, instance):
        from exchange.api.serializers import DealReviewSerializer

        return DealReviewSerializer(instance.review_set, many=True).data

    def get_reviews_count(self, instance: Company):
        return instance.review_set.count()

    # FIXME: сделать через аннотацию и добавить кол-во сделок по оборудованию
    def get_deals_count(self, instance: Company):
        return (
            instance.recyclables_sell_deals.count()
            + instance.recyclables_buy_deals.count()
        )

    def get_average_review_rate(self, instance: Company):
        return (
            instance.review_set.aggregate(models.Avg("rate"))["rate__avg"]
            or 0.0
        )

    class Meta:
        model = Company


class SetOwnerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ()


class CreateCompanySerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=128, required=False)

    class Meta:
        model = Company
        fields = (
            "inn",
            "bic",
            "payment_account",
            "correction_account",
            "bank_name",
            "name",
            "head_full_name",
            "description",
            "address",
            "email",
            "phone",
            "city",
            "latitude",
            "longitude",
            "image",
            "with_nds",
        )

    def to_representation(self, instance):
        return CompanySerializer(instance).data

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["owner"] = user
        if "phone" not in validated_data:
            validated_data["phone"] = user.phone
        instance = super().create(validated_data)

        # Set company for owner
        user.company = instance
        user.save()

        return instance


class CompanyVerificationRequestSerializer(
    NonNullDynamicFieldsModelSerializer
):
    company = CompanySerializer(exclude=("manager", "owner"))
    employee = LazyRefSerializer(
        "user.api.serializers.UserSerializer", exclude=("company",)
    )

    class Meta:
        model = CompanyVerificationRequest


class CreateCompanyVerificationRequestSerializer(
    CreateMyCompanyMixin, CompanySettingsMixin, serializers.ModelSerializer
):
    class Meta:
        model = CompanyVerificationRequest
        fields = ()

    def validate(self, attrs):
        company = attrs["company"]
        if company.status in (CompanyStatus.VERIFIED, CompanyStatus.RELIABLE):
            raise serializers.ValidationError("Компания уже верифицирована")
        return attrs

    def to_representation(self, instance):
        return CompanyVerificationRequestSerializer(instance).data


class UpdateCompanyVerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyVerificationRequest
        fields = ("status", "comment")

    def to_representation(self, instance):
        return CompanyVerificationRequestSerializer(instance).data
