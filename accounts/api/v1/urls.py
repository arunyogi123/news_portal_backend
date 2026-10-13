from django.urls import path

from .views import (
    RegisterAPIView,
    VerifyEmailAPIView,
    ResendOTPAPIView,
    UserProfileAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPAPIView.as_view(), name="resend-otp"),
    path("me/", UserProfileAPIView.as_view(), name="my-profile"),
]
