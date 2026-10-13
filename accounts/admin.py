from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import EmailVerification


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "expires_at",
        "attempts",
        "last_sent_at",
        "created_at",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "user",
        "otp_hash",
        "expires_at",
        "attempts",
        "last_sent_at",
        "created_at",
    )
