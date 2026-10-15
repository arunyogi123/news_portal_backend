from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from bookmarks.models import Bookmark
from .serializers import BookmarkSerializer


class BookmarkListCreateAPIView(generics.ListCreateAPIView):
    # Serializer used to convert bookmark data into JSON
    # and validate incoming data when creating a bookmark.
    serializer_class = BookmarkSerializer

    # Only authenticated users can access this endpoint.
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only the logged-in user's bookmarks.
        # Exclude bookmarks whose articles are not published.
        # select_related() fetches the related article efficiently
        # to reduce unnecessary database queries.
        return (
            Bookmark.objects
            .filter(
                user=self.request.user,
                article__is_published=True,
            )
            .select_related("article")
        )

    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the bookmark owner.
        # The client does not need to provide the user ID.
        serializer.save(user=self.request.user)


class BookmarkDestroyAPIView(generics.DestroyAPIView):
    # Serializer associated with the bookmark resource.
    serializer_class = BookmarkSerializer

    # Only authenticated users can delete bookmarks.
    permission_classes = [IsAuthenticated]

    # Use the URL parameter 'bookmark_id' to identify the bookmark.
    lookup_url_kwarg = "bookmark_id"

    def get_queryset(self):
        # Allow users to delete only their own bookmarks.
        # If the bookmark belongs to another user or does not exist,
        # Django REST Framework returns a 404 Not Found response.
        return Bookmark.objects.filter(user=self.request.user)