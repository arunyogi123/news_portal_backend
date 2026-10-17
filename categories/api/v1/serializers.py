from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        required=False,
        max_length=120,
        validators=[UniqueValidator(queryset=Category.objects.all())],
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        slug = attrs.get("slug")
        if not slug or not slug.strip():
            if self.instance and self.instance.slug:
                attrs["slug"] = self.instance.slug
            else:
                name = attrs.get("name", "")
                base_slug = slugify(name) or "category"
                candidate_slug = base_slug
                counter = 1
                qs = Category.objects.all()
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                while qs.filter(slug=candidate_slug).exists():
                    candidate_slug = f"{base_slug}-{counter}"
                    counter += 1
                attrs["slug"] = candidate_slug
        return super().validate(attrs)
