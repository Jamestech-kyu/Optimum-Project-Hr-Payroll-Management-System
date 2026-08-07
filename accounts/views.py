try:
    from drf_spectacular.utils import extend_schema
except ImportError:
    def extend_schema(*args, **kwargs):
        def decorator(obj):
            return obj
        return decorator

from rest_framework import status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate

from audit.services import log_activity
from audit.utils import get_client_ip

from .models import CustomUser, Role
from .serializers import (
    RegisterSerializer,
    RoleSerializer,
    ProvisionUserSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsAdminOrSuperAdmin, RequiredPermission


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


@extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Registration successful. Await admin approval.",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses={200: RoleSerializer(many=True)})
class RoleListView(APIView):
    """Assignable roles, used by the client's user-provisioning form.

    Returns a bare list rather than a paginated envelope because the client maps
    over the response directly.
    """

    permission_classes = [RequiredPermission("accounts.manage")]

    def get(self, request):
        roles = Role.objects.all().order_by("name")

        return Response(
            RoleSerializer(roles, many=True).data,
            status=status.HTTP_200_OK,
        )


@extend_schema(responses={200: UserSerializer(many=True)})
class UserListCreateView(APIView):
    """List system users, and provision new ones from the admin screen.

    Provisioned users are approved on creation: an administrator choosing the
    role is the approval step, so there is nothing left to confirm.
    """

    permission_classes = [RequiredPermission("accounts.manage")]

    def get(self, request):
        users = CustomUser.objects.select_related("role").order_by("username")

        return Response(
            UserSerializer(users, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ProvisionUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        log_activity(
            user=request.user,
            action="CREATE",
            module="Accounts",
            description=(
                f"Provisioned user {user.username} "
                f"with role {user.role.name if user.role else 'none'}."
            ),
            object_id=user.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=LoginSerializer)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")

        login_username = username

        if username and "@" in username:
            user_match = CustomUser.objects.filter(
                email__iexact=username,
            ).first()

            if user_match:
                login_username = user_match.username

        user = authenticate(username=login_username, password=password)

        if user is None:
            return Response(
                {"message": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_approved and not user.is_superuser:
            return Response(
                {"message": "Your account is pending admin approval."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {"message": "Your account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        log_activity(
            user=user,
            action="LOGIN",
            module="Accounts",
            description=f"{user.username} logged into the system.",
            object_id=user.id,
            ip_address=get_client_ip(request),
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(responses={200: UserSerializer})
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


@extend_schema(request=UpdateProfileSerializer, responses={200: UserSerializer})
class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully",
                    "user": UserSerializer(request.user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ChangePasswordSerializer)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            if not user.check_password(old_password):
                return Response(
                    {"message": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses={200: UserSerializer})
class ApproveUserView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_approved = True
        user.save()

        return Response(
            {
                "message": "User approved successfully",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            log_activity(
                user=request.user,
                action="LOGOUT",
                module="Accounts",
                description=f"{request.user.username} logged out.",
                object_id=request.user.id,
                ip_address=get_client_ip(request),
            )

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {"message": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
