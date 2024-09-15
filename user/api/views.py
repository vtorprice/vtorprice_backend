from django.contrib.auth import get_user_model, logout
from django_filters import FilterSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import UpdateModelMixin
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from user.api.serializers import (
    CreateUserSerializer,
    UserSerializer,
    PhoneConfirmSerializer,
    UserObtainTokenSerializer,
    UpdateUserSerializer,
    UpdateUserRoleSerializer,
)
from user.models import UserRole
from user.services.sms_ru import make_phone_call

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == "make_call":
            return CreateUserSerializer
        elif self.action == "phone_confirm":
            return PhoneConfirmSerializer
        else:
            return self.serializer_class

    @action(methods=["POST"], detail=False)
    def make_call(self, request, *args, **kwargs):
        data = request.data
        is_created = False

        try:
            user = User.objects.get(phone=data.get("phone"))
        except User.DoesNotExist:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            is_created = True

        try:
            code = make_phone_call(
                user.phone.raw_input, request.META.get("REMOTE_ADDR")
            )
            user.code = code
        except Exception as e:
            raise ValidationError(str(e))

        if not user.password:
            user.set_password(user.code)

        user.save()

        setattr(user, "is_created", is_created)
        serializer = self.get_serializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenRefreshSerializer(),
        },
        request_body=PhoneConfirmSerializer,
    )
    @action(methods=["POST"], detail=True)
    def phone_confirm(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        if (
            user.code == serializer.validated_data["code"]
            or serializer.validated_data["code"]
            == "8818"  # FIXME: remove condition after publication
        ):

            jwt_serializer = UserObtainTokenSerializer(
                data={"phone": user.phone.as_e164, "password": user.password},
                context={"request": request},
            )
            jwt_serializer.is_valid(raise_exception=True)

            data = jwt_serializer.validated_data

            # TODO: когда появятся сотрудники компаний, необходимо
            #  предусмотреть для них флоу и переписать этот блок
            if user.role == UserRole.COMPANY_ADMIN:
                data["has_company"] = hasattr(user, "my_company")

            return Response(data, status=status.HTTP_200_OK)

        else:
            raise ValidationError("Введен некорректный код")


class UserFilterSet(FilterSet):
    pass


class UserView(UpdateModelMixin, APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = UpdateUserSerializer
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_object(self):
        return getattr(self.request, "user")

    def get(self, request):
        user = self.request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: UserSerializer(),
        },
        request_body=UpdateUserSerializer,
    )
    @action(methods=["PUT"], detail=False)
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: UserSerializer(),
        },
        request_body=UpdateUserSerializer,
    )
    @action(methods=["PATCH"], detail=False)
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @action(methods=["DELETE"], detail=False)
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        logout(request)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def get(request, pk=None):
    filter_kwargs = {"pk": pk}
    obj = get_object_or_404(User.objects.all(), **filter_kwargs)
    serializer = UserSerializer(obj)
    return Response(serializer.data)


@swagger_auto_schema(methods=["PATCH"], request_body=UpdateUserRoleSerializer)
@api_view(["PATCH"])
def update_user_role(request, pk=None):
    filter_kwargs = {"pk": pk}
    obj = get_object_or_404(User.objects.all(), **filter_kwargs)
    serializer = UpdateUserRoleSerializer(
        data=request.data, instance=obj, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
