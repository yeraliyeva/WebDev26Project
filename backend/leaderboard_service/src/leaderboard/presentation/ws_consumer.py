"""WebSocket consumer for live leaderboard updates.

Clients connect to WS /leaderboard/ws and:
  1. Immediately receive the current leaderboard snapshot.
  2. Receive a pushed update on every submit.rewarded event processed
     by the Kafka consumer.

The consumer joins the ``leaderboard`` channel group. The Kafka consumer
calls ``channel_layer.group_send`` after each successful score write to
Redis, which triggers ``leaderboard_update`` on all connected clients.
"""

from __future__ import annotations

import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)

GROUP_NAME = "leaderboard"


class LeaderboardWebSocketConsumer(AsyncJsonWebsocketConsumer):
    """Async WebSocket consumer that streams live leaderboard updates.

    Authentication: the ``X-User-Id`` header injected by Traefik is read
    from the WebSocket handshake scope headers so the initial snapshot
    can include the connecting user's rank.
    """

    async def connect(self) -> None:
        """Accept the connection, join the broadcast group, send snapshot."""
        await self.channel_layer.group_add(GROUP_NAME, self.channel_name)
        await self.accept()
        logger.info("WebSocket client connected: %s", self.channel_name)

        try:
            snapshot = await self._get_snapshot()
            await self.send_json(snapshot)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to send initial leaderboard snapshot")

    async def disconnect(self, close_code: int) -> None:
        """Remove from group on disconnect."""
        await self.channel_layer.group_discard(GROUP_NAME, self.channel_name)
        logger.info("WebSocket client disconnected (code=%s): %s", close_code, self.channel_name)

    # Called by channel layer when Kafka consumer broadcasts an update
    async def leaderboard_update(self, event: dict) -> None:
        """Forward a broadcast leaderboard snapshot to the client.

        Args:
            event: Channel layer event dict with key ``data``.
        """
        await self.send_json(event["data"])

    # ─── Helpers ─────────────────────────────────────────────────────────────

    @sync_to_async
    def _get_snapshot(self) -> dict:
        """Fetch the current leaderboard snapshot synchronously via Redis.

        Returns:
            Dict with ``top`` list and ``user_place`` field.
        """
        from leaderboard.application.use_cases.get_leaderboard import GetLeaderboardUseCase
        from leaderboard.infrastructure.redis_client import get_redis_client
        from leaderboard.infrastructure.repositories import RedisLeaderboardRepository
        from uuid import UUID

        # Best-effort: extract X-User-Id from WS handshake headers
        headers = dict(self.scope.get("headers", []))
        user_id_bytes = headers.get(b"x-user-id")
        try:
            user_id = UUID(user_id_bytes.decode()) if user_id_bytes else None
        except (ValueError, AttributeError):
            user_id = None

        use_case = GetLeaderboardUseCase(
            repository=RedisLeaderboardRepository(client=get_redis_client()),
            top_n=settings.LEADERBOARD_TOP_N,
        )

        # If we have no user_id, still return the top-N snapshot
        from uuid import uuid4
        dto = use_case.execute(user_id=user_id or uuid4())

        return {
            "top": [
                {"place": e.place, "user_id": str(e.user_id), "score": e.score}
                for e in dto.top
            ],
            "user_place": dto.user_place,
        }
