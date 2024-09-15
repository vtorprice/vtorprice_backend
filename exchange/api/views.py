from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django_filters import (
    MultipleChoiceFilter,
    NumberFilter,
    ModelMultipleChoiceFilter,
    BooleanFilter,
)
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from djangorestframework_camel_case.parser import (
    CamelCaseFormParser,
    CamelCaseMultiPartParser,
)
from rest_framework import filters, generics, viewsets
from drf_yasg import openapi as api
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_nested.viewsets import NestedViewSetMixin

from common.filters import FavoriteFilterBackend
from common.views import (
    MultiSerializerMixin,
    ImagesMixin,
    FavoritableMixin,
    DocumentsMixin,
    ExcludeMixin,
)
from document_generator.api.serializers import GeneratedDocumentSerializer
from document_generator.common import get_or_generate_document
from document_generator.generators.document_generators import (
    AgreementSpecification,
    Act,
)
from document_generator.models import (
    GeneratedDocumentType,
)
from exchange.api.serializers import (
    CreateRecyclablesApplicationSerializer,
    RecyclablesApplicationSerializer,
    ExchangeRecyclablesSerializer,
    RecyclablesDealSerializer,
    CreateRecyclablesDealSerializer,
    CreateReviewSerializer,
    CreateEquipmentApplicationSerializer,
    EquipmentApplicationSerializer,
    EquipmentDealSerializer,
    CreateEquipmentDealSerializer,
    UpdateRecyclablesDealSerializer,
    UpdateEquipmentDealSerializer,
    MatchingApplicationSerializer,
    UpdateRecyclablesApplicationSerializer,
)
from exchange.models import (
    RecyclablesApplication,
    ApplicationStatus,
    RecyclablesDeal,
    DealStatus,
    Review,
    EquipmentApplication,
    EquipmentDeal,
)
from exchange.services import filter_qs_by_coordinates
from exchange.utils import (
    validate_period,
    get_truncation_class,
    get_lower_date_bound,
)
from exchange.signals import (
    recyclables_deal_status_changed,
    equipment_deal_status_changed,
)
from product.models import Recyclables, Equipment
from user.models import UserRole


class DealDocumentGeneratorMixin:
    @action(
        methods=["GET"],
        detail=True,
        description='Получение "Договор-приложение спецификация"',
    )
    def get_specification_agreement(self, request, pk):
        deal = self.get_object()
        content_type = ContentType.objects.get_for_model(deal)

        generator = AgreementSpecification(deal)
        filter_kwargs = {
            "content_type": content_type,
            "object_id": deal.id,
            "type": GeneratedDocumentType.AGREEMENT_SPECIFICATION,
        }
        document = get_or_generate_document(generator, filter_kwargs)

        return Response(GeneratedDocumentSerializer(document).data)

    @action(methods=["GET"], detail=True, description="Получение Акта")
    def get_act_document(self, request, pk):
        user = self.request.user
        if user.is_anonymous:
            raise NotAuthenticated
        deal = self.get_object()
        content_type = ContentType.objects.get_for_model(deal)
        generator = Act(company=request.user.company, deal=deal)
        document_type = (
            GeneratedDocumentType.ACT_BUYER
            if deal.buyer_company == user.company
            else GeneratedDocumentType.ACT_SELLER
        )
        document = get_or_generate_document(
            generator=generator,
            document_filter_kwargs={
                "content_type": content_type,
                "object_id": deal.id,
                "type": document_type,
            },
        )
        return Response(GeneratedDocumentSerializer(document).data)


class RecyclablesApplicationFilterSet(FilterSet):
    total_weight__gte = NumberFilter(
        field_name="total_weight", lookup_expr="gte"
    )
    total_weight__lte = NumberFilter(
        field_name="total_weight", lookup_expr="lte"
    )
    status = MultipleChoiceFilter(choices=ApplicationStatus.choices)
    recyclables = ModelMultipleChoiceFilter(queryset=Recyclables.objects.all())

    is_my = BooleanFilter(method="is_my_filter")

    def is_my_filter(self, queryset, value, *args, **kwargs):
        user = self.request.user
        if args[0] and user.is_authenticated:
            if user.role == UserRole.COMPANY_ADMIN:
                queryset = queryset.filter(company=user.company)
            if user.role == UserRole.MANAGER:
                queryset = queryset.filter(company__manager=user)
        return queryset

    class Meta:
        model = RecyclablesApplication
        fields = {
            "deal_type": ["exact"],
            "urgency_type": ["exact"],
            "recyclables": ["exact"],
            "recyclables__category": ["exact"],
            "city": ["exact"],
            "company": ["exact"],
            "created_at": ["gte", "lte"],
            "price": ["gte", "lte"],
        }


class RecyclablesApplicationViewSet(
    ImagesMixin,
    MultiSerializerMixin,
    FavoritableMixin,
    ExcludeMixin,
    viewsets.ModelViewSet,
):
    queryset = RecyclablesApplication.objects.select_related(
        "company", "recyclables"
    ).annotate_total_weight()
    serializer_classes = {
        "list": RecyclablesApplicationSerializer,
        "retrieve": RecyclablesApplicationSerializer,
        "create": CreateRecyclablesApplicationSerializer,
    }
    default_serializer_class = UpdateRecyclablesApplicationSerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    parent_lookup_kwargs = "company_pk"
    search_fields = ("company__name", "company__inn", "recyclables__name")
    ordering_fields = "__all__"
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
        FavoriteFilterBackend,
    )
    filterset_class = RecyclablesApplicationFilterSet

    def get_queryset(self):
        qs = super().get_queryset()

        raw_coordinates = self.request.query_params.getlist("point", [])
        if raw_coordinates:
            qs = filter_qs_by_coordinates(qs, raw_coordinates)

        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "exclude",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
                description="ID заявки(ок), которую(ые) необходимо исключить",
            ),
            api.Parameter(
                "is_favorite",
                api.IN_QUERY,
                type=api.TYPE_BOOLEAN,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """

        Принимает список query необязательных параметров point.
        ?point=55.781361,49.183067&point=55.781361,49.183067&point=55.781361,49.183067
        При использовании, необходимо передать как минимум три точки.
        Отбирает заявки, территориально находящиеся в указанном многоугольнике

        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        methods=["POST"], request_body=MatchingApplicationSerializer
    )
    @action(methods=["POST"], detail=False)
    def match_applications(self, request):
        serializer = MatchingApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = serializer.save()

        return Response(RecyclablesDealSerializer(deal).data)


class EquipmentApplicationFilterSet(FilterSet):
    status = MultipleChoiceFilter(choices=ApplicationStatus.choices)
    equipment = ModelMultipleChoiceFilter(queryset=Equipment.objects.all())

    is_my = BooleanFilter(method="is_my_filter")

    def is_my_filter(self, queryset, value, *args, **kwargs):
        user = self.request.user
        if args[0] and user.is_authenticated:
            if user.role == UserRole.COMPANY_ADMIN:
                queryset = queryset.filter(company=user.company)
            if user.role == UserRole.MANAGER:
                queryset = queryset.filter(company__manager=user)
        return queryset

    class Meta:
        model = EquipmentApplication
        fields = {
            "deal_type": ["exact"],
            "equipment": ["exact"],
            "equipment__category": ["exact"],
            "city": ["exact"],
            "company": ["exact"],
            "created_at": ["gte", "lte"],
            "price": ["gte", "lte"],
            "count": ["gte", "lte"],
        }


class EquipmentApplicationViewSet(
    ImagesMixin,
    MultiSerializerMixin,
    FavoritableMixin,
    ExcludeMixin,
    viewsets.ModelViewSet,
):
    queryset = EquipmentApplication.objects.select_related(
        "company", "equipment"
    )
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    parent_lookup_kwargs = "company_pk"
    search_fields = ("company__name", "company__inn", "equipment__name")
    ordering_fields = "__all__"
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
        FavoriteFilterBackend,
    )
    default_serializer_class = CreateEquipmentApplicationSerializer
    serializer_classes = {
        "list": EquipmentApplicationSerializer,
        "retrieve": EquipmentApplicationSerializer,
    }
    filterset_class = EquipmentApplicationFilterSet


class ExchangeRecyclablesViewSet(
    generics.ListAPIView,
    viewsets.GenericViewSet,
):
    queryset = Recyclables.objects.annotate_applications()
    serializer_class = ExchangeRecyclablesSerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    ordering_fields = (
        "name",
        "category__name",
    )
    search_fields = ("name",)
    filterset_fields = ("category",)

    def get_queryset(self):
        qs = super().get_queryset()

        urgency_type = self.request.query_params.get("urgency_type")

        if urgency_type:
            qs = qs.annotate_applications(urgency_type=int(urgency_type))

        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "urgency_type",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
                description="Срочность",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "period",
                api.IN_QUERY,
                type=api.TYPE_STRING,
                required=False,
                description="Период по которому выводить график(week/month/year/all)",
            ),
        ],
    )
    @action(methods=["GET"], detail=True)
    def graph(self, request, pk):
        period = request.query_params.get("period", "all")
        period = validate_period(period)

        recyclable: Recyclables = self.get_object()

        TruncClass = get_truncation_class(period)
        lower_date_bound = get_lower_date_bound(period)

        deals = self.get_filtered_deals(
            TruncClass, lower_date_bound, recyclable
        )

        graph_data = deals.values_list("price", "truncated_date")

        return Response(graph_data)

    @staticmethod
    def get_filtered_deals(TruncClass, lower_date_bound, recyclable):
        deals_filter = {
            "application__recyclables": recyclable,
            "status": DealStatus.COMPLETED,
        }
        if lower_date_bound:
            deals_filter["created_at__gte"] = lower_date_bound
        filtered_deals = RecyclablesDeal.objects.filter(**deals_filter)
        deals = (
            filtered_deals.annotate(truncated_date=TruncClass("created_at"))
            .order_by("truncated_date", "-created_at")
            .distinct("truncated_date")
        )
        return deals


class RecyclablesDealFilterSet(FilterSet):
    status = MultipleChoiceFilter(choices=DealStatus.choices)
    is_my = BooleanFilter(method="is_my_filter")

    def is_my_filter(self, queryset, value, *args, **kwargs):
        user = self.request.user
        if args[0] and user.is_authenticated:
            if user.role == UserRole.COMPANY_ADMIN:
                queryset = queryset.filter(
                    Q(supplier_company=user.company)
                    | Q(buyer_company=user.company)
                )
            if user.role == UserRole.MANAGER:
                queryset = queryset.filter(
                    Q(supplier_company__manager=user)
                    | Q(buyer_company__manager=user)
                )
        return queryset

    class Meta:
        model = RecyclablesDeal
        fields = {
            "application__recyclables": ["exact"],
            "application__recyclables__category": ["exact"],
            "shipping_city": ["exact"],
            "delivery_city": ["exact"],
            "supplier_company": ["exact"],
            "buyer_company": ["exact"],
            "created_at": ["gte", "lte"],
            "price": ["gte", "lte"],
            "weight": ["gte", "lte"],
        }


class RecyclablesDealViewSet(
    DealDocumentGeneratorMixin,
    DocumentsMixin,
    MultiSerializerMixin,
    viewsets.ModelViewSet,
):
    queryset = RecyclablesDeal.objects.select_related(
        "application",
        "application__recyclables",
        "supplier_company",
        "buyer_company",
    ).prefetch_related("reviews")
    serializer_classes = {
        "list": RecyclablesDealSerializer,
        "retrieve": RecyclablesDealSerializer,
        "create": CreateRecyclablesDealSerializer,
    }
    default_serializer_class = UpdateRecyclablesDealSerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    search_fields = (
        "supplier_company__name",
        "supplier_company__inn",
        "buyer_company__name",
        "buyer_company__inn",
        "application__recyclables__name",
    )
    ordering_fields = "__all__"
    filter_backends = (
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_class = RecyclablesDealFilterSet

    def update(self, request, *args, **kwargs):
        """
        Overriding in order to send signal when changing deal status
        """

        instance: RecyclablesDeal = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if old_status != instance.status:
            # Passing status as key-word arg because status in instance has int value
            recyclables_deal_status_changed.send_robust(
                RecyclablesDeal,
                instance=instance,
                status=serializer.data.get("status").get("label"),
            )

        return Response(serializer.data)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_anonymous and user.role == UserRole.LOGIST:
            qs = qs.filter(
                transport_applications__approved_logistics_offer__logist=user
            )
        return qs


class ReviewViewSet(
    NestedViewSetMixin,
    GenericViewSet,
    generics.CreateAPIView,
    generics.UpdateAPIView,
):
    queryset = Review.objects.all()
    serializer_class = CreateReviewSerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    parent_lookup_kwargs = {"object_pk": "object_id"}


class EquipmentDealFilterSet(FilterSet):
    status = MultipleChoiceFilter(choices=DealStatus.choices)
    is_my = BooleanFilter(method="is_my_filter")

    def is_my_filter(self, queryset, value, *args, **kwargs):
        user = self.request.user
        if args[0] and user.is_authenticated:
            if user.role == UserRole.COMPANY_ADMIN:
                queryset = queryset.filter(
                    Q(supplier_company=user.company)
                    | Q(buyer_company=user.company)
                )
            if user.role == UserRole.MANAGER:
                queryset = queryset.filter(
                    Q(supplier_company__manager=user)
                    | Q(buyer_company__manager=user)
                )
        return queryset

    class Meta:
        model = EquipmentDeal
        fields = {
            "application__equipment": ["exact"],
            "application__equipment__category": ["exact"],
            "shipping_city": ["exact"],
            "delivery_city": ["exact"],
            "supplier_company": ["exact"],
            "buyer_company": ["exact"],
            "created_at": ["gte", "lte"],
            "price": ["gte", "lte"],
        }


class EquipmentDealViewSet(
    DealDocumentGeneratorMixin,
    DocumentsMixin,
    MultiSerializerMixin,
    viewsets.ModelViewSet,
):
    queryset = EquipmentDeal.objects.select_related(
        "application",
        "application__equipment",
        "supplier_company",
        "buyer_company",
    ).prefetch_related("reviews")
    serializer_classes = {
        "list": EquipmentDealSerializer,
        "retrieve": EquipmentDealSerializer,
        "create": CreateEquipmentDealSerializer,
    }
    default_serializer_class = UpdateEquipmentDealSerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    search_fields = (
        "supplier_company__name",
        "supplier_company__inn",
        "buyer_company__name",
        "buyer_company__inn",
        "application__equipment__name",
    )
    ordering_fields = "__all__"
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = EquipmentDealFilterSet

    def update(self, request, *args, **kwargs):
        """
        Overriding in order to send signal when changing deal status
        """

        instance: EquipmentDeal = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if old_status != instance.status:
            # Passing status as key-word arg because status in instance has int value
            equipment_deal_status_changed.send_robust(
                EquipmentDeal,
                instance=instance,
                status=serializer.data.get("status").get("label"),
            )

        return Response(serializer.data)
