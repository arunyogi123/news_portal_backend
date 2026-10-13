from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser

from news.models import Article
from .serializers import ArticleSerializer


# List published articles and allow users to retrieve a single article
class ArticleListAPIView(generics.ListAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]

    # Only show published articles to public users
    queryset = Article.objects.filter(is_published=True)


# Retrieve one published article using its slug
class ArticleDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    queryset = Article.objects.filter(is_published=True)


# Allow staff users to create articles
class ArticleCreateAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminUser]

    # Automatically assign the logged-in staff user as the author
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# Allow staff users to update or delete articles
class ArticleManageAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "slug"
