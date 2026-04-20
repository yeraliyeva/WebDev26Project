"""WebSocket URL patterns for the leaderboard service."""

from __future__ import annotations

from django.urls import re_path

from leaderboard.presentation.ws_consumer import LeaderboardWebSocketConsumer

websocket_urlpatterns = [
    re_path(r"^ws$", LeaderboardWebSocketConsumer.as_asgi()),
]
