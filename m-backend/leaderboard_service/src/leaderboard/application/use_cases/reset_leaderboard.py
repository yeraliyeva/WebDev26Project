from leaderboard.domain.repositories import AbstractLeaderboardRepository


class ResetLeaderboardUseCase:
    """Archive today's leaderboard and prepare a clean slate for tomorrow."""

    def __init__(self, repository: AbstractLeaderboardRepository) -> None:
        self._repository = repository

    def execute(self) -> None:
        """Rename the active ZSET to an archive key and set a 7-day TTL."""
        self._repository.reset_daily()
