"""ASGI configuration for leaderboard_service.

Exposes the ASGI callable as module-level variable ``application``.
Handles both HTTP (Django) and WebSocket (Django Channels) protocols.
"""

from __future__ import annotations

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.otel import setup_otel  # noqa: E402

setup_otel(service_name="leaderboard_service")
django.setup()

# Import ws_urls after django.setup() so apps are ready.
from leaderboard.presentation.ws_urls import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
