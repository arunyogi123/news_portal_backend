from django.urls import path

from .views import (
    BookmarkListCreateAPIView,
    BookmarkDestroyAPIView,
)

urlpatterns = [
    path(
        "",
        BookmarkListCreateAPIView.as_view(),
        name="bookmark-list-create",
    ),
    path(
        "<int:bookmark_id>/",
        BookmarkDestroyAPIView.as_view(),
        name="bookmark-delete",
    ),
]
