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

from accounts.models import EmailVerification, PasswordReset
from .serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    ForgotPasswordSerializer,
    VerifyPasswordResetOTPSerializer,
    ResetPasswordSerializer,
)

User = get_user_model()

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
RESET_TOKEN_EXPIRY_MINUTES = 10


def send_verification_code(user, verification):
    """Generate, hash, store, and send an email-verification OTP."""
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


def send_password_reset_code(user, reset):
    """Generate, hash, store, and email a password-reset OTP."""
    code = f"{secrets.randbelow(1_000_000):06d}"

    reset.otp_hash = make_password(code)
    reset.expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    reset.last_sent_at = timezone.now()
    reset.attempts = 0
    reset.reset_token_hash = ""
    reset.reset_token_expires_at = None
    reset.save()

    send_mail(
        subject="Reset your SimpleNews password",
        message=(
            f"Hello {user.username},\n\n"
            f"Your password-reset code is {code}.\n"
            f"It expires in {OTP_EXPIRY_MINUTES} minutes.\n\n"
            "If you did not request this, you can ignore this email."
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
        responses={201: dict},
        description="Register a user and send an email-verification OTP.",
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
                "detail": ("Registration successful. Check your email for the OTP."),
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
            {"detail": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResendOTPSerializer

    @extend_schema(
        request=ResendOTPSerializer,
        responses={200: dict, 400: dict, 429: dict, 503: dict},
        description="Request a replacement email-verification OTP.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "If the account is eligible, a code will be sent."},
                status=status.HTTP_200_OK,
            )

        if user.is_active:
            return Response(
                {"detail": "If the account is eligible, a code will be sent."},
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
            {"detail": "If the account is eligible, a code will be sent."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={200: dict},
        description=(
            "Request a password-reset code. The response does not reveal "
            "whether the email is registered."
        ),
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        generic_response = {
            "detail": (
                "If an eligible account exists, a password-reset code " "will be sent."
            )
        }

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            return Response(generic_response, status=status.HTTP_200_OK)

        reset, _ = PasswordReset.objects.get_or_create(
            user=user,
            defaults={
                "otp_hash": make_password(secrets.token_hex(16)),
                "expires_at": timezone.now(),
                "last_sent_at": timezone.now(),
            },
        )

        elapsed = (timezone.now() - reset.last_sent_at).total_seconds()

        if reset.expires_at > timezone.now() and elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            return Response(generic_response, status=status.HTTP_200_OK)

        try:
            send_password_reset_code(user, reset)
        except Exception:
            return Response(
                {"detail": "Email delivery failed. Try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(generic_response, status=status.HTTP_200_OK)


class VerifyPasswordResetOTPAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyPasswordResetOTPSerializer

    @extend_schema(
        request=VerifyPasswordResetOTPSerializer,
        responses={200: dict, 400: dict, 429: dict},
        description=(
            "Verify the password-reset OTP and return a short-lived " "reset token."
        ),
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            reset = user.password_reset
        except (User.DoesNotExist, PasswordReset.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired reset request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reset.attempts >= OTP_MAX_ATTEMPTS:
            return Response(
                {"detail": "Too many attempts. Request a new code."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if timezone.now() >= reset.expires_at:
            return Response(
                {"detail": "OTP expired. Request a new code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset.attempts += 1
        reset.save(update_fields=["attempts"])

        if not check_password(code, reset.otp_hash):
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_token = secrets.token_urlsafe(32)
        reset.reset_token_hash = make_password(raw_token)
        reset.reset_token_expires_at = timezone.now() + timedelta(
            minutes=RESET_TOKEN_EXPIRY_MINUTES
        )
        reset.save(
            update_fields=[
                "reset_token_hash",
                "reset_token_expires_at",
            ]
        )

        return Response(
            {
                "detail": "Code verified. You may now reset your password.",
                "reset_token": raw_token,
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: dict, 400: dict},
        description="Set a new password using the short-lived reset token.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        raw_token = serializer.validated_data["reset_token"]
        new_password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            reset = user.password_reset
        except (User.DoesNotExist, PasswordReset.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired reset request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not reset.reset_token_hash
            or not reset.reset_token_expires_at
            or timezone.now() >= reset.reset_token_expires_at
            or not check_password(raw_token, reset.reset_token_hash)
        ):
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password"])
            reset.delete()

        return Response(
            {
                "detail": (
                    "Password reset successfully. You can now log in "
                    "with your new password."
                )
            },
            status=status.HTTP_200_OK,
        )


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
