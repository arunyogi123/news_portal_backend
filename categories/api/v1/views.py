from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser

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
