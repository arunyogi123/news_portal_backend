from django.db.models import ProtectedError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from categories.models import Category
from .serializers import CategorySerializer


# Allow anyone to view categories, but only staff users to create them.
class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    # Public users can view categories.
    # Only staff users can create categories.
    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]


# Allow anyone to view a category, but only staff users to modify it.
class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    # Public users can retrieve categories.
    # Only staff users can update or delete categories.
    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            article_count = (
                instance.articles.count()
                if hasattr(instance, "articles")
                else len(e.protected_objects)
            )
            return Response(
                {
                    "detail": (
                        f"Cannot delete category '{instance.name}' because "
                        f"{article_count} article(s) are assigned to it. "
                        "Reassign or delete these articles first."
                    ),
                    "code": "category_protected",
                    "article_count": article_count,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
