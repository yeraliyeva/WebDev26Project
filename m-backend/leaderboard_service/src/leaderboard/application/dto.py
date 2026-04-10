from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LeaderboardEntryDTO:
    """Wire representation of a single leaderboard entry."""

    place: int
    user_id: UUID
    score: int


@dataclass(frozen=True)
class LeaderboardResponseDTO:
    """Full response payload for GET /leaderboard."""

    top: list[LeaderboardEntryDTO]
    user_place: int | None
