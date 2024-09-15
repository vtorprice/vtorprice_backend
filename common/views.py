from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.serializers import EmptySerializer
from exchange.api.serializers import (
    CreateImageModelSerializer,
    CreateDocumentModelSerializer,
)
from exchange.models import ImageModel, DocumentModel
from user.models import UserRole, Favorite
from drf_yasg import openapi as api


class BaseQuerySetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class MultiSerializerMixin:
    """
    Overridden to support several serializers for actions
    """

    serializer_classes = dict()
    default_serializer_class = None

    def get_serializer_class(self):
        return self.serializer_classes.get(
            self.action, self.default_serializer_class
        )


class BulkCreateMixin:
    """
    Overridden to support bulk creation
    """

    create_with_removal = False

    def get_serializer(self, *args, **kwargs):
        if self.action == "create":
            if isinstance(kwargs.get("data", {}), list):
                kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "create":
            # To support bulk creation with preliminary
            # deletion of existing objects
            context["with_removal"] = self.create_with_removal
        return context


class CompanyOwnerQuerySetMixin:
    """
    Filter the queryset by owner's company
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated and user.role == UserRole.COMPANY_ADMIN:
            qs = qs.filter(company=user.my_company)

        return qs


class NestedRouteQuerySetMixin:
    """
    Implements filtering by nested route

    f.e.: /companies/{company_pk}/documents/{pk} --> filter the queryset by company_pk
    source: https://github.com/alanjds/drf-nested-routers
    """

    nested_route_lookup_field = None

    def get_queryset(self):
        qs = super().get_queryset()

        if self.nested_route_lookup_field in self.kwargs:
            lookup = self.nested_route_lookup_field.replace("pk", "id")
            qs = qs.filter(
                **{lookup: self.kwargs[self.nested_route_lookup_field]}
            )

        return qs


class ImagesMixin:
    """
    Implements methods for adding and removing images
    for models that are related with the ImageModel model
    via a GenericRelation
    """

    @staticmethod
    def create_instance_images(images, instance):
        content_type = ContentType.objects.get_for_model(instance._meta.model)
        to_create = []

        for image in images:
            to_create.append(
                ImageModel(
                    image=image,
                    content_type=content_type,
                    object_id=instance.id,
                )
            )
        # instance.images.clear()
        instance.images.bulk_create(to_create)

    @swagger_auto_schema(
        request_body=CreateImageModelSerializer,
    )
    @action(methods=["POST"], detail=True)
    def add_images(self, request, *args, **kwargs):
        instance = self.get_object()
        images = request.FILES.getlist("image")
        self.create_instance_images(images=images, instance=instance)
        return super().retrieve(request, *args, **kwargs)

    @action(
        methods=["DELETE"],
        detail=True,
        url_path="delete_image/(?P<image_pk>[^/.]+)",
    )
    def delete_image(self, request, image_pk=None, *args, **kwargs):
        instance = self.get_object()
        instance.images.filter(pk=image_pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentsMixin:
    """
    Implements methods for adding and removing documents
    for models that are related with the DocumentModel
    via a GenericRelation
    """

    @staticmethod
    def create_instance_documents(
        documents, instance, name, company, document_type
    ):
        content_type = ContentType.objects.get_for_model(instance)
        to_create = []

        for document in documents:
            to_create.append(
                DocumentModel(
                    document=document,
                    content_type=content_type,
                    object_id=instance.pk,
                    name=name,
                    company=company,
                    document_type=document_type,
                )
            )

        DocumentModel.objects.bulk_create(to_create)

    @swagger_auto_schema(
        request_body=CreateDocumentModelSerializer,
    )
    @action(methods=["POST"], detail=True)
    def add_documents(self, request, *args, **kwargs):
        instance = self.get_object()
        company = request.user.company
        documents = request.FILES.getlist("document")
        name = request.POST.get("name")
        document_type = request.POST.get("document_type")
        self.create_instance_documents(
            documents=documents,
            instance=instance,
            name=name,
            company=company,
            document_type=document_type,
        )
        return super().retrieve(request, *args, **kwargs)

    @action(
        methods=["DELETE"],
        detail=True,
        url_path="delete_document/(?P<document_pk>[^/.]+)",
    )
    def delete_document(self, request, document_pk=None, *args, **kwargs):
        instance = self.get_object()
        instance.documents.filter(pk=document_pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoritableMixin:
    """
    Implements logic of liking and disliking some objects.
    Adds additional API endpoint /objects/<id>/favorite that marks and unmarks given as favorite.
    Also, when requesting this objects, adds fields isFavorite representing whether this object marked as favorite or not
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        requested_user: "user.models.User" = self.request.user

        if requested_user.is_anonymous:
            return queryset

        return queryset.annotate(
            is_favorite=Exists(
                Favorite.objects.filter(
                    user=requested_user,
                    content_type=ContentType.objects.get_for_model(
                        self.queryset.model
                    ),
                    object_id=OuterRef("id"),
                )
            )
        )

    @swagger_auto_schema(
        request_body=EmptySerializer,
    )
    @action(
        detail=True,
        methods=["PATCH"],
        description="Mark or unmarks given Recyclable as favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, *args, **kwargs):

        obj = self.get_object()
        requested_user = request.user
        content_type = ContentType.objects.get_for_model(obj)
        favorite_object, created = Favorite.objects.get_or_create(
            user=requested_user,
            content_type=content_type,
            object_id=obj.id,
        )

        if not created:
            favorite_object.delete()
        return self.retrieve(request, *args, **kwargs)


class ExcludeMixin:
    """
    Implements the logic to exclude objects in the list
    method via the passed query parameter, which accepts
    a list of object ids to be excluded
    """

    def get_queryset(self):
        qs = super().get_queryset()

        exclude = self.request.query_params.getlist("exclude", [])

        if exclude:
            qs = qs.exclude(pk__in=exclude)

        return qs

    @swagger_auto_schema(
        manual_parameters=[
            api.Parameter(
                "exclude",
                api.IN_QUERY,
                type=api.TYPE_INTEGER,
                required=False,
                description="ID объекта(ов), который(ые) необходимо исключить",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
