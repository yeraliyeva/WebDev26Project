"""Health check endpoint for the leaderboard service."""

from __future__ import annotations

import logging
import time

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from leaderboard.infrastructure.redis_client import get_redis_client

logger = logging.getLogger(__name__)

_START_TIME = time.time()


class HealthView(APIView):
    """GET /health — liveness + readiness probe for leaderboard_service.

    Checks Redis connectivity since that is the only dependency this service has.
    Returns a personality-flavoured status message alongside structured
    health data so monitoring tools can parse it.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        """Return service health status.

        Returns:
            200 when Redis is reachable.
            503 when Redis is unreachable.
        """
        uptime = int(time.time() - _START_TIME)
        checks: dict[str, str] = {}

        # --- Redis check ---
        try:
            client = get_redis_client()
            client.ping()
            checks["redis"] = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.error("Health check: redis unreachable: %s", exc)
            checks["redis"] = "unreachable"

        healthy = all(v == "ok" for v in checks.values())

        payload = {
            "service": "leaderboard_service",
            "status": "healthy" if healthy else "degraded",
            "message": (
                "Leaderboard service is on top — Redis sorted sets spinning, "
                "rankings fresh, glory awaits! 🏆"
                if healthy
                else "Leaderboard service has fallen off the board — Redis is gone. 📉"
            ),
            "uptime_seconds": uptime,
            "checks": checks,
        }

        status_code = 200 if healthy else 503
        return Response(payload, status=status_code)
