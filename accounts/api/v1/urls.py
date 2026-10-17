from django.urls import path

from .views import (
    RegisterAPIView,
    VerifyEmailAPIView,
    ResendOTPAPIView,
    UserProfileAPIView,
    AdminUserListAPIView,
    ForgotPasswordAPIView,
    VerifyPasswordResetOTPAPIView,
    ResetPasswordAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPAPIView.as_view(), name="resend-otp"),
    path("me/", UserProfileAPIView.as_view(), name="my-profile"),
    path("users/", AdminUserListAPIView.as_view(), name="admin-user-list"),
    path(
        "forgot-password/",
        ForgotPasswordAPIView.as_view(),
        name="forgot-password",
    ),
    path(
        "verify-reset-otp/",
        VerifyPasswordResetOTPAPIView.as_view(),
        name="verify-reset-otp",
    ),
    path(
        "reset-password/",
        ResetPasswordAPIView.as_view(),
        name="reset-password",
    ),
]
