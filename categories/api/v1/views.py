from rest_framework import generics
from categories.models import Category
from .serializers import CategorySerializer


# Handles listing all categories and creating a new category
class CategoryListCreateAPIView(generics.ListCreateAPIView):

    # Fetch all category records from the database
    queryset = Category.objects.all()

    # Use CategorySerializer to convert category data to JSON
    # and validate incoming data when creating a category
    serializer_class = CategorySerializer


# Handles retrieving, updating, and deleting a single category
class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    # Find a category using its slug instead of its numeric ID
    # Example: /api/categories/technology/
    lookup_field = "slug"
