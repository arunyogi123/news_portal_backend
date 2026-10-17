from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserProfileExposureTests(APITestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="testpassword123",
            first_name="Regular",
            last_name="User",
            is_staff=False,
            is_active=True,
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpassword123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
            is_active=True,
        )
        self.profile_url = reverse("my-profile")

    def test_profile_exposes_is_staff_for_regular_user(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("is_staff", response.data)
        self.assertIn("is_superuser", response.data)
        self.assertFalse(response.data["is_staff"])
        self.assertFalse(response.data["is_superuser"])

    def test_profile_exposes_is_staff_for_staff_user(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_staff"])

    def test_regular_user_cannot_elevate_privileges_via_profile(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(
            self.profile_url,
            {"is_staff": True, "is_superuser": True},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reload user from DB to verify no elevation occurred
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)


class AdminUserListPermissionsTests(APITestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="testpassword123",
            is_staff=False,
            is_active=True,
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpassword123",
            is_staff=True,
            is_active=True,
        )
        self.users_url = reverse("admin-user-list")

    def test_anonymous_user_cannot_list_users(self):
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_list_users(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_list_users_safely(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
        # Ensure password hash is not exposed
        first_user = response.data[0]
        self.assertNotIn("password", first_user)
        self.assertNotIn("otp_hash", first_user)
        self.assertIn("username", first_user)
        self.assertIn("email", first_user)
        self.assertIn("is_staff", first_user)

