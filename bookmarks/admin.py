from django.contrib import admin

# Register your models here.
from .models import Bookmark


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "article", "created_at")
    list_select_related = ("user", "article")
    search_fields = (
        "user__username",
        "user__email",
        "article__title",
    )
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)
