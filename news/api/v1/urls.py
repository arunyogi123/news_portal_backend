from django.urls import path

from .views import (
    ArticleListAPIView,
    ArticleDetailAPIView,
    ArticleCreateAPIView,
    ArticleManageAPIView,
)

urlpatterns = [
    # List all published articles
    path("", ArticleListAPIView.as_view(), name="article-list"),

    # Create a new article
    path("create/", ArticleCreateAPIView.as_view(), name="article-create"),

    # Retrieve a published article by slug
    path("<slug:slug>/", ArticleDetailAPIView.as_view(), name="article-detail"),

    # Update or delete an article by slug
    path(
        "<slug:slug>/manage/",
        ArticleManageAPIView.as_view(),
        name="article-manage",
    ),
]
