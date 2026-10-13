from rest_framework import serializers
from news.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    # Display the category name instead of only its database ID
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    # Display the author's username
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "category",
            "category_name",
            "author",
            "author_username",
            "image",
            "is_featured",
            "is_published",
            "created_at",
            "updated_at",
        ]

        # These fields are generated automatically or assigned by the backend
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
        ]
