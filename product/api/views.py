from django_filters.rest_framework import FilterSet
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny

from common.views import BaseQuerySetMixin
from product.api.serializers import (
    RecyclablesSerializer,
    RecyclablesCategorySerializer,
    EquipmentCategorySerializer,
    EquipmentSerializer,
    # RecyclingCodeSerializer,
)
from product.models import (
    Recyclables,
    RecyclablesCategory,
    EquipmentCategory,
    Equipment,
    RecyclingCode,
)


class RecyclablesCategoryViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = RecyclablesCategory.objects.root_nodes().prefetch_related(
        "recyclables"
    )
    serializer_class = RecyclablesCategorySerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"


class RecyclablesFilterSet(FilterSet):
    class Meta:
        model = Recyclables
        fields = {
            "category": ["exact"],
            "category__parent": ["exact"],
            "applications__city": ["exact"],
            "applications__urgency_type": ["exact"],
        }


class RecyclablesViewSet(viewsets.ModelViewSet):
    queryset = Recyclables.objects.all()
    serializer_class = RecyclablesSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"


class EquipmentCategoryViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = EquipmentCategory.objects.root_nodes().prefetch_related(
        "equipments"
    )
    serializer_class = EquipmentCategorySerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"


class RecyclingCodeViewSet(
    BaseQuerySetMixin,
    generics.ListAPIView,
    generics.RetrieveAPIView,
    viewsets.GenericViewSet,
):
    queryset = RecyclingCode.objects.all()
    # serializer_class = RecyclingCodeSerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("name", "gost_name")
    ordering_fields = "__all__"
