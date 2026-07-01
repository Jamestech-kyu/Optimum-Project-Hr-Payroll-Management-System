from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CurrentUserView,
    ApproveUserView,
    UpdateProfileView,
    ChangePasswordView,
)

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # User Profile
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("profile/", UpdateProfileView.as_view(), name="update_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Administration
    path("approve/<int:user_id>/", ApproveUserView.as_view(), name="approve_user"),
]