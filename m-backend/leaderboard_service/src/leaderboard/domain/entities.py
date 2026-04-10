from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LeaderboardEntry:
    """A single ranked entry on the leaderboard."""

    place: int
    user_id: UUID
    score: int


@dataclass(frozen=True)
class LeaderboardResult:
    """Composite result returned to the API caller."""

    top: list[LeaderboardEntry]
    user_place: int | None
