from django.urls import path

from .views import AdminDashboardStatsAPIView

urlpatterns = [
    path(
        "stats/",
        AdminDashboardStatsAPIView.as_view(),
        name="admin-dashboard-stats",
    ),
]
