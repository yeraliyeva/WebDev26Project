from __future__ import annotations

from uuid import UUID

from leaderboard.domain.repositories import AbstractLeaderboardRepository


class RecordRewardUseCase:
    """Apply a rewarded-credit event to the daily leaderboard.

    Idempotent: events already recorded in the processed-events SET are skipped.

    Args:
        repository: Leaderboard persistence port.
    """

    def __init__(self, repository: AbstractLeaderboardRepository) -> None:
        self._repository = repository

    def execute(self, event_id: str, user_id: UUID, amount: int) -> None:
        """Increment the user's daily score unless the event was already applied.

        Args:
            event_id: Unique submit UUID, used as the idempotency key.
            user_id: User whose score should be incremented.
            amount: Credits earned in this submit.
        """
        if self._repository.is_event_processed(event_id):
            return

        self._repository.increment_score(user_id=user_id, amount=amount)
        self._repository.mark_event_processed(event_id=event_id)
