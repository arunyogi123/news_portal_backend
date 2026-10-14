from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models


class EmailVerification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email verification"
        verbose_name_plural = "Email verifications"

    def __str__(self):
        return f"Email verification for {self.user.username}"

class PasswordReset(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset",
    )
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    reset_token_hash = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )
    reset_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Password reset"
        verbose_name_plural = "Password resets"

    def __str__(self):
        return f"Password reset for {self.user.username}"
