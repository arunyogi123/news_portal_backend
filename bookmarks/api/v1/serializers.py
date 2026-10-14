from rest_framework import serializers

from bookmarks.models import Bookmark
from news.models import Article


class BookmarkedArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "image",
            "created_at",
        ]
        read_only_fields = fields


class BookmarkSerializer(serializers.ModelSerializer):
    article = BookmarkedArticleSerializer(read_only=True)
    article_id = serializers.PrimaryKeyRelatedField(
        source="article",
        queryset=Article.objects.filter(is_published=True),
        write_only=True,
    )

    class Meta:
        model = Bookmark
        fields = [
            "id",
            "article",
            "article_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_article_id(self, article):
        user = self.context["request"].user

        if Bookmark.objects.filter(
            user=user,
            article=article,
        ).exists():
            raise serializers.ValidationError(
                "You have already bookmarked this article."
            )

        return article
