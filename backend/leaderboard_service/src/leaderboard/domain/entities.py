from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LeaderboardEntry:
    """A single ranked entry on the leaderboard.

    Args:
        place: 1-based rank position.
        user_id: Unique identifier of the user.
        score: Total credits earned today.
    """

    place: int
    user_id: UUID
    score: int


@dataclass(frozen=True)
class LeaderboardResult:
    """Composite result returned to the API caller.

    Args:
        top: Ordered list of top-N entries (place 1 first).
        user_place: The requesting user's rank, or None if they have no score today.
        user_score: The requesting user's current score today (0 if none).
    """

    top: list[LeaderboardEntry]
    user_place: int | None
    user_score: int
