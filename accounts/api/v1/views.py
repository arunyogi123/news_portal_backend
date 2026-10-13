import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import EmailVerification
from .serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
)

User = get_user_model()

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


def send_verification_code(user, verification):
    """Generate, hash, store, and send a six-digit OTP."""
    code = f"{secrets.randbelow(1_000_000):06d}"

    verification.otp_hash = make_password(code)
    verification.expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    verification.last_sent_at = timezone.now()
    verification.attempts = 0
    verification.save()

    send_mail(
        subject="Verify your SimpleNews email",
        message=(
            f"Hello {user.username},\n\n"
            f"Your SimpleNews verification code is {code}.\n"
            f"It expires in {OTP_EXPIRY_MINUTES} minutes.\n\n"
            "If you did not register, ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        description="Register a new user and generate an email OTP.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        verification = EmailVerification.objects.create(
            user=user,
            otp_hash=make_password(secrets.token_hex(16)),
            expires_at=timezone.now(),
            last_sent_at=timezone.now(),
        )

        try:
            send_verification_code(user, verification)
        except Exception:
            return Response(
                {
                    "detail": (
                        "Account created but email delivery failed. "
                        "Please try resending the code."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "detail": ("Registration successful. " "Check your email for the OTP."),
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailSerializer

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={200: dict},
        description="Verify the email using a six-digit OTP.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email__iexact=email)
            verification = user.email_verification
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            return Response(
                {"detail": "Invalid verification request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.attempts >= OTP_MAX_ATTEMPTS:
            return Response(
                {"detail": "Too many attempts. Request a new code."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if timezone.now() >= verification.expires_at:
            return Response(
                {"detail": "OTP expired. Request a new code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.attempts += 1
        verification.save(update_fields=["attempts"])

        if not check_password(code, verification.otp_hash):
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=["is_active"])
            verification.delete()

        return Response(
            {"detail": ("Email verified successfully. " "You can now log in.")},
            status=status.HTTP_200_OK,
        )


class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResendOTPSerializer

    @extend_schema(
        request=ResendOTPSerializer,
        responses={200: dict, 400: dict, 429: dict, 503: dict},
        description="Request a replacement email verification OTP.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": ("If the account is eligible, " "a code will be sent.")},
                status=status.HTTP_200_OK,
            )

        if user.is_active:
            return Response(
                {"detail": ("If the account is eligible, " "a code will be sent.")},
                status=status.HTTP_200_OK,
            )

        try:
            verification = user.email_verification
        except EmailVerification.DoesNotExist:
            return Response(
                {"detail": "Verification is unavailable. Contact support."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        elapsed = (timezone.now() - verification.last_sent_at).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            return Response(
                {"detail": "Wait before requesting another code."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            send_verification_code(user, verification)
        except Exception:
            return Response(
                {"detail": "Email delivery failed. Try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"detail": ("If the account is eligible, " "a code will be sent.")},
            status=status.HTTP_200_OK,
        )


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
