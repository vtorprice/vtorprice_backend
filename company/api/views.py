import django_filters
from django.db import models
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from djangorestframework_camel_case.parser import (
    CamelCaseFormParser,
    CamelCaseMultiPartParser,
)
from drf_yasg import openapi as api
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.viewsets import GenericViewSet
from rest_framework_nested.viewsets import NestedViewSetMixin

from common.filters import FavoriteFilterBackend
from common.utils import (
    get_search_terms_from_request,
    str2bool,
    get_grouped_qs,
    get_nds_tax,
)
from common.views import (
    BulkCreateMixin,
    MultiSerializerMixin,
    CompanyOwnerQuerySetMixin,
    NestedRouteQuerySetMixin,
    FavoritableMixin,
)
from company.api.serializers import (
    CompanySerializer,
    CompanyDocumentSerializer,
    CompanyRecyclablesSerializer,
    CompanyAdditionalContactSerializer,
    CompanyVerificationRequestSerializer,
    CreateCompanySerializer,
    CreateCompanyDocumentSerializer,
    CreateCompanyAdditionalContactSerializer,
    CreateCompanyRecyclablesSerializer,
    NonExistCompanySerializer,
    CompanyAdvantageSerializer,
    RecyclingCollectionTypeSerializer,
    CreateCompanyActivityTypeSerializer,
    CompanyActivityTypeSerializer,
    CreateCompanyVerificationRequestSerializer,
    SetOwnerCompanySerializer,
    UpdateCompanyVerificationRequestSerializer,
    ListCompanySerializer,
    CitySerializer,
    RegionSerializer,
)
from company.models import (
    Company,
    CompanyDocument,
    CompanyRecyclables,
    CompanyAdditionalContact,
    CompanyVerificationRequest,
    CompanyAdvantage,
    RecyclingCollectionType,
    CompanyActivityType,
    City,
    CompanyVerificationRequestStatus,
    ActivityType,
    Region,
)
from company.services.company_data.get_data import get_companies
from exchange.api.serializers import DealReviewSerializer
from exchange.models import Review
from user.models import UserRole


class CompanyViewSet(
    MultiSerializerMixin,
    FavoritableMixin,
    viewsets.ModelViewSet,
):
    queryset = (
        Company.objects.select_related("city")
        .prefetch_related(
            "documents",
            "recyclables",
            "contacts",
            "activity_types",
            "review_set",
        )
        .annotate(recyclables_count=Count("recyclables"))
        .annotate(monthly_volume=models.Sum("recyclables__monthly_volume"))
    )

    serializer_classes = {
        "list": ListCompanySerializer,
        "set_owner": SetOwnerCompanySerializer,
        "retrieve": CompanySerializer,
    }
    default_serializer_class = CreateCompanySerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
        FavoriteFilterBackend,
    )

    search_fields = ("name", "inn")
    ordering_fields = "__all__"
    filterset_fields = {
        "activity_types__rec_col_types": ["exact"],
        "activity_types__advantages": ["exact"],
        "recyclables__recyclables": ["exact"],
        "status": ["exact"],
        "city": ["exact"],
        "manager": ["exact"],
        "created_at": ["gte", "lte"],
    }

    def get_queryset(self):
        qs = super().get_queryset()

        if self.action in ("put", "patch"):
            if self.request.user.role == UserRole.COMPANY_ADMIN:
                return qs.filter(owner=self.request.user)
            elif self.request.user.role == UserRole.MANAGER:
                return qs.filter(manager=self.request.user)
            elif self.request.user.role in (
                UserRole.ADMIN,
                UserRole.SUPER_ADMIN,
            ):
                return qs
            else:
                return qs.none()
        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "global_search",
                api.IN_QUERY,
                type=api.TYPE_BOOLEAN,
                required=False,
                description="Глобальный поиск компаний",
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
        Overridden to make serialization work correctly when queryset
        contains a company that does not exist in the database
        """
        queryset = self.filter_queryset(self.get_queryset())

        non_exist = False
        if isinstance(queryset, list):
            non_exist = True

        page = self.paginate_queryset(queryset)
        if page is not None:
            if non_exist:
                serializer = NonExistCompanySerializer(page, many=True)
            else:
                serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        """
        Overridden to support retrieving a company that is not in the database
        """
        queryset = super().filter_queryset(queryset)
        search_terms = get_search_terms_from_request(self.request)

        if not search_terms:
            return queryset

        global_search = str2bool(
            self.request.query_params.get("global_search", "false")
        )

        if not queryset and global_search:
            query = search_terms[0]
            queryset = get_companies(query)

        return queryset

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [AllowAny]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    @action(methods=["POST"], detail=True)
    def set_owner(self, request, *args, **kwargs):
        if hasattr(request.user, "my_company"):
            raise PermissionDenied
        company = self.get_object()
        if company.owner:
            raise ValidationError("Компания уже есть в системе")
        company.owner = request.user
        company.save()
        # change action for correct serialization of object
        self.action = "retrieve"
        return self.retrieve(request, *args, **kwargs)

    @action(methods=["GET"], detail=False)
    def nds_tax(self, request, *args, **kwargs):
        return Response(get_nds_tax(), status=status.HTTP_200_OK)


class CompanySettingsViewMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        company_pk = self.request.query_params.get("company")
        if company_pk:
            company = get_object_or_404(Company, pk=company_pk)
            if isinstance(self, CompanyAdvantageViewSet):
                advantages_ids = CompanyActivityType.objects.filter(
                    company=1, advantages__isnull=False
                ).values_list("advantages", flat=True)
                qs = CompanyAdvantage.objects.filter(id__in=advantages_ids)
            else:
                qs = qs.filter(company=company)
        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "company",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CompanyDocumentViewSet(
    CompanyOwnerQuerySetMixin,
    MultiSerializerMixin,
    BulkCreateMixin,
    viewsets.ModelViewSet,
    CompanySettingsViewMixin,
):
    queryset = CompanyDocument.objects.all()
    serializer_classes = {"create": CreateCompanyDocumentSerializer}
    default_serializer_class = CompanyDocumentSerializer
    yasg_parser_classes = [CamelCaseFormParser, CamelCaseMultiPartParser]

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CompanyRecyclablesViewSet(
    NestedRouteQuerySetMixin,
    CompanyOwnerQuerySetMixin,
    MultiSerializerMixin,
    BulkCreateMixin,
    CompanySettingsViewMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    generics.CreateAPIView,
    generics.DestroyAPIView,
    viewsets.GenericViewSet,
):
    queryset = CompanyRecyclables.objects.all()
    serializer_classes = {"create": CreateCompanyRecyclablesSerializer}
    default_serializer_class = CompanyRecyclablesSerializer
    create_with_removal = True
    nested_route_lookup_field = "company_pk"

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "company",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
            )
        ]
    )
    @action(methods=["DELETE"], detail=False)
    def delete_all_recyclables(self, request):
        user = request.user
        if user.is_anonymous:
            raise PermissionDenied
        company_pk = request.query_params.get("company")
        company = self.request.user.company
        if company_pk:
            company = get_object_or_404(Company.objects.all(), pk=company_pk)

        if user.company != company or user.role == UserRole.LOGIST:
            if not (user.role == UserRole.MANAGER and company.manager == user):
                raise PermissionDenied
        if user.role == UserRole.COMPANY_ADMIN and user.company != company:
            raise PermissionDenied

        company.recyclables.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyAdditionalContactViewSet(
    CompanyOwnerQuerySetMixin,
    MultiSerializerMixin,
    BulkCreateMixin,
    viewsets.ModelViewSet,
):
    queryset = CompanyAdditionalContact.objects.all()
    serializer_classes = {"create": CreateCompanyAdditionalContactSerializer}
    default_serializer_class = CompanyAdditionalContactSerializer


class CompanyAdvantageViewSet(generics.ListAPIView, viewsets.GenericViewSet):
    queryset = CompanyAdvantage.objects.all()
    serializer_class = CompanyAdvantageSerializer
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_fields = ("activity",)
    search_fields = ("name",)


class RecyclingCollectionTypeViewSet(
    generics.ListAPIView,
    viewsets.GenericViewSet,
):
    queryset = RecyclingCollectionType.objects.all()
    serializer_class = RecyclingCollectionTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_fields = ("activity",)
    search_fields = ("name",)

    @action(methods=["GET"], detail=False)
    def activity_grouped_list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset().order_by("activity"))
        grouped = get_grouped_qs(qs, "activity")
        result = []

        for k, v in grouped.items():
            data = {
                "id": k,
                "label": ActivityType(k).label,
                "rec_col_types": self.get_serializer(v, many=True).data,
            }
            result.append(data)

        return Response(result, status=status.HTTP_200_OK)


class CompanyVerificationRequestFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        coll_type = request.query_params.get("collection_type")
        if coll_type:
            queryset = queryset.filter(
                company__activity_types__rec_col_types=coll_type
            )

        return queryset


class CompanyVerificationFilterSet(FilterSet):
    class Meta:
        model = CompanyVerificationRequest
        fields = {
            "company__recyclables__recyclables": ["exact"],
            "company__recyclables__recyclables__category": ["exact"],
            "company__activity_types__activity": ["exact"],
            "company__city": ["exact"],
            "created_at": ["gte", "lte"],
            "status": ["exact"],
        }


class CompanyVerificationRequestViewSet(
    MultiSerializerMixin,
    generics.RetrieveAPIView,
    generics.ListAPIView,
    generics.UpdateAPIView,
    generics.CreateAPIView,
    viewsets.GenericViewSet,
):
    queryset = CompanyVerificationRequest.objects.select_related(
        "company", "employee"
    )
    serializer_classes = {
        "create": CreateCompanyVerificationRequestSerializer,
        "list": CompanyVerificationRequestSerializer,
    }
    default_serializer_class = UpdateCompanyVerificationRequestSerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
        CompanyVerificationRequestFilterBackend,
    )
    search_fields = ("company__name", "company__inn")
    ordering_fields = ("created_at", "company__city__name")
    filterset_class = CompanyVerificationFilterSet

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = qs.filter(status=CompanyVerificationRequestStatus.NEW)

        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "collection_type",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CompanyActivityTypeViewSet(
    NestedRouteQuerySetMixin,
    CompanyOwnerQuerySetMixin,
    MultiSerializerMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    generics.CreateAPIView,
    generics.DestroyAPIView,
    viewsets.GenericViewSet,
):
    queryset = CompanyActivityType.objects.all()
    serializer_classes = {"create": CreateCompanyActivityTypeSerializer}
    default_serializer_class = CompanyActivityTypeSerializer
    nested_route_lookup_field = "company_pk"


class CompanyReviewsViewset(
    NestedViewSetMixin, GenericViewSet, generics.ListAPIView
):
    parent_lookup_kwargs = {"company_pk": "company__pk"}
    queryset = Review.objects.get_queryset()
    serializer_class = DealReviewSerializer


class RegionViewSet(generics.ListAPIView, viewsets.GenericViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)


class CityFilter(FilterSet):
    region_pk = django_filters.NumberFilter(field_name="region__pk")

    class Meta:
        model = City
        fields = ("region_pk",)


class CityViewSet(
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ("name",)
    filterset_class = CityFilter

    def retrieve(self, request, *args, **kwargs):
        from services.yandex_geo import YandexGeocoderClient
        from config.settings import YANDEX_GEOCODER_API_KEY

        geocoder_client = YandexGeocoderClient(YANDEX_GEOCODER_API_KEY)
        city = self.get_object()
        if not (city.latitude and city.longitude):
            address_data = geocoder_client.get_coordinates_from_city(city)
            city.latitude, city.longitude = (
                address_data.latitude,
                address_data.longitude,
            )
            city.save()

        return super().retrieve(request, *args, **kwargs)
