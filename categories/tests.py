from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from categories.models import Category
from news.models import Article

User = get_user_model()


class CategoryAPITests(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff_user",
            email="staff@example.com",
            password="testpassword123",
            is_staff=True,
            is_active=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="testpassword123",
            is_staff=False,
            is_active=True,
        )
        self.category = Category.objects.create(
            name="Climate & Environment",
            slug="climate-environment",
            description="Stories on climate and sustainability",
        )
        self.list_create_url = reverse("category-list-create")
        self.detail_url = reverse(
            "category-detail",
            kwargs={"slug": self.category.slug},
        )

    def test_anonymous_and_regular_users_can_list_categories(self):
        # Anonymous
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(c["slug"] == self.category.slug for c in response.data))

        # Regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_category(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            self.list_create_url,
            {"name": "Sports", "description": "Sports news"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_create_category_with_auto_slug(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            self.list_create_url,
            {"name": "Artificial Intelligence", "description": "AI developments"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Artificial Intelligence")
        self.assertEqual(response.data["slug"], "artificial-intelligence")

    def test_staff_user_can_update_category(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(
            self.detail_url,
            {"description": "Updated description for climate stories"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(
            self.category.description, "Updated description for climate stories"
        )

    def test_staff_user_can_delete_unlinked_category(self):
        empty_cat = Category.objects.create(
            name="Empty Topic",
            slug="empty-topic",
            description="No articles yet",
        )
        url = reverse("category-detail", kwargs={"slug": empty_cat.slug})

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(slug="empty-topic").exists())

    def test_deleting_protected_category_with_articles_returns_helpful_error(self):
        # Create an article linked to self.category
        Article.objects.create(
            title="Renewable Transition",
            slug="renewable-transition",
            summary="Solar surge.",
            content="Full renewable transition content.",
            category=self.category,
            author=self.staff_user,
            is_published=True,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(self.detail_url)

        # Deletion must be safely blocked and return friendly 400 with details
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertIn("Cannot delete category", response.data["detail"])
        self.assertIn(self.category.name, response.data["detail"])
        # Category must still exist in the database
        self.assertTrue(Category.objects.filter(slug=self.category.slug).exists())
