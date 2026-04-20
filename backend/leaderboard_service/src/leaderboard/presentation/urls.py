from django.urls import path
from leaderboard.presentation.views import LeaderboardView
from leaderboard.presentation.health import HealthView

urlpatterns = [
    path("", LeaderboardView.as_view(), name="leaderboard"),
    path("health", HealthView.as_view(), name="leaderboard-health"),
]
