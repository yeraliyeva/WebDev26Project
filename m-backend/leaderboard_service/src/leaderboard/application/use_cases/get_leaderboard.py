from __future__ import annotations

from uuid import UUID

from leaderboard.application.dto import LeaderboardEntryDTO, LeaderboardResponseDTO
from leaderboard.domain.repositories import AbstractLeaderboardRepository


class GetLeaderboardUseCase:
    """Return the top-N leaderboard and the requesting user's position."""

    def __init__(self, repository: AbstractLeaderboardRepository, top_n: int) -> None:
        self._repository = repository
        self._top_n = top_n

    def execute(self, user_id: UUID) -> LeaderboardResponseDTO:
        """Fetch and return leaderboard data."""
        result = self._repository.get_leaderboard(user_id=user_id, top_n=self._top_n)
        return LeaderboardResponseDTO(
            top=[
                LeaderboardEntryDTO(
                    place=entry.place,
                    user_id=entry.user_id,
                    score=entry.score,
                )
                for entry in result.top
            ],
            user_place=result.user_place,
        )
