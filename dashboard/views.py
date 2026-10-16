from django.core.serializers import python
from django.shortcuts import render

# Create your views here.

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import Category
from news.models import Article

User = get_user_model()


class AdminDashboardStatsAPIView(APIView):
    """
    Return dashboard statistics for staff users.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        article_stats = Article.objects.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(is_published=True)),
            drafts=Count("id", filter=Q(is_published=False)),
            featured=Count("id", filter=Q(is_featured=True)),
        )

        stats = {
            "total_articles": article_stats["total"],
            "published_articles": article_stats["published"],
            "draft_articles": article_stats["drafts"],
            "featured_articles": article_stats["featured"],
            "total_categories": Category.objects.count(),
            "total_users": User.objects.count(),
        }

        return Response(stats)
