from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LeaderboardEntryDTO:
    """Wire representation of a single leaderboard entry.

    Args:
        place: 1-based rank.
        user_id: User's UUID.
        score: Credits earned today.
    """

    place: int
    user_id: UUID
    score: int


@dataclass(frozen=True)
class LeaderboardResponseDTO:
    """Full response payload for GET /leaderboard.

    Args:
        top: Ordered top-N entries.
        user_place: Requesting user's rank, or None.
        user_score: Requesting user's score today (0 if none).
    """

    top: list[LeaderboardEntryDTO]
    user_place: int | None
    user_score: int
