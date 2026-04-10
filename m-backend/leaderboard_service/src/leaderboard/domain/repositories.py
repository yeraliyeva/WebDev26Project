from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from leaderboard.domain.entities import LeaderboardResult


class AbstractLeaderboardRepository(ABC):
    """Port for all leaderboard persistence operations."""

    @abstractmethod
    def get_leaderboard(self, user_id: UUID, top_n: int) -> LeaderboardResult:
        """Fetch top-N entries and the requesting user's rank."""

    @abstractmethod
    def increment_score(self, user_id: UUID, amount: int) -> None:
        """Atomically add credits to a user's daily score."""

    @abstractmethod
    def is_event_processed(self, event_id: str) -> bool:
        """Check whether a submit event has already been applied today."""

    @abstractmethod
    def mark_event_processed(self, event_id: str) -> None:
        """Record that a submit event has been applied."""

    @abstractmethod
    def reset_daily(self) -> None:
        """Atomically archive today's leaderboard and start a fresh one."""
