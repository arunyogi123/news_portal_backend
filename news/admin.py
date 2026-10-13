from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "is_featured",
        "is_published",
        "created_at",
    )

    list_filter = ("category", "is_featured", "is_published")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_featured", "is_published")
    readonly_fields = ("created_at", "updated_at")
