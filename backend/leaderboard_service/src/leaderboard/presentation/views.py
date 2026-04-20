from __future__ import annotations

from uuid import UUID

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from leaderboard.application.use_cases.get_leaderboard import GetLeaderboardUseCase
from leaderboard.infrastructure.redis_client import get_redis_client
from leaderboard.infrastructure.repositories import RedisLeaderboardRepository
from leaderboard.presentation.serializers import LeaderboardResponseSerializer


class LeaderboardView(APIView):
    """GET /leaderboard — return today's top-N and the caller's rank."""

    def get(self, request: Request) -> Response:
        """Handle the leaderboard read request.

        Reads X-User-Id injected by Traefik's ForwardAuth middleware.

        Args:
            request: Incoming DRF request.

        Returns:
            200 response with top entries and the requesting user's place.
        """
        user_id_header = request.headers.get("X-User-Id")
        if not user_id_header:
            return Response({"detail": "X-User-Id header missing"}, status=401)
        
        try:
            user_id = UUID(user_id_header)
        except ValueError:
            return Response({"detail": "Invalid X-User-Id format"}, status=400)

        use_case = GetLeaderboardUseCase(
            repository=RedisLeaderboardRepository(client=get_redis_client()),
            top_n=settings.LEADERBOARD_TOP_N,
        )
        dto = use_case.execute(user_id=user_id)

        serializer = LeaderboardResponseSerializer(
            {
                "top": [
                    {"place": e.place, "user_id": e.user_id, "score": e.score}
                    for e in dto.top
                ],
                "user_place": dto.user_place,
                "user_score": dto.user_score,
            }
        )
        return Response(serializer.data)
