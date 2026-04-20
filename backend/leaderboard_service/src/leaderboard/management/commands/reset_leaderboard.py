import logging

import redis as redis_lib
from django.core.management.base import BaseCommand

from leaderboard.application.use_cases.reset_leaderboard import ResetLeaderboardUseCase
from leaderboard.infrastructure.redis_client import get_redis_client
from leaderboard.infrastructure.repositories import RedisLeaderboardRepository

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command that archives today's leaderboard at midnight."""

    help = "Archive leaderboard:daily → leaderboard:archive:YYYY-MM-DD"

    def handle(self, *args, **options) -> None:
        """Run the reset use case; exit cleanly if the key does not exist."""
        client = get_redis_client()
        repository = RedisLeaderboardRepository(client=client)
        use_case = ResetLeaderboardUseCase(repository=repository)

        try:
            use_case.execute()
            self.stdout.write(self.style.SUCCESS("Leaderboard reset complete."))
        except redis_lib.ResponseError:
            logger.info("leaderboard:daily does not exist — nothing to reset.")
            self.stdout.write("No active leaderboard to reset.")
