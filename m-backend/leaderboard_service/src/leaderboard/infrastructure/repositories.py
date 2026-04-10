from __future__ import annotations

from datetime import date
from uuid import UUID

import redis

from leaderboard.domain.entities import LeaderboardEntry, LeaderboardResult
from leaderboard.domain.repositories import AbstractLeaderboardRepository

_DAILY_KEY = b"leaderboard:daily"
_PROCESSED_KEY = b"processed_events:daily"
_ARCHIVE_TTL = 60 * 60 * 24 * 7  # 7 days in seconds
_PROCESSED_TTL = 60 * 60 * 24  # 1 day


class RedisLeaderboardRepository(AbstractLeaderboardRepository):
    """Redis-backed implementation of the leaderboard repository."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def get_leaderboard(self, user_id: UUID, top_n: int) -> LeaderboardResult:
        """Return top-N entries and the caller's rank in a single round-trip pair."""
        member = str(user_id).encode()
        pipe = self._client.pipeline()
        pipe.zrevrange(_DAILY_KEY, 0, top_n - 1, withscores=True)
        pipe.zrevrank(_DAILY_KEY, member)
        raw_top, raw_rank = pipe.execute()

        top = [
            LeaderboardEntry(
                place=idx + 1,
                user_id=UUID(m.decode()),
                score=int(score),
            )
            for idx, (m, score) in enumerate(raw_top)
        ]

        user_place = int(raw_rank) + 1 if raw_rank is not None else None
        return LeaderboardResult(top=top, user_place=user_place)

    def increment_score(self, user_id: UUID, amount: int) -> None:
        """Atomically increment user's ZSET score."""
        self._client.zincrby(_DAILY_KEY, amount, str(user_id).encode())

    def is_event_processed(self, event_id: str) -> bool:
        """Return True if event_id is present in the processed-events SET."""
        return bool(self._client.sismember(_PROCESSED_KEY, event_id.encode()))

    def mark_event_processed(self, event_id: str) -> None:
        """Add event_id to the processed-events SET and (re)set its TTL."""
        pipe = self._client.pipeline()
        pipe.sadd(_PROCESSED_KEY, event_id.encode())
        pipe.expire(_PROCESSED_KEY, _PROCESSED_TTL)
        pipe.execute()

    def reset_daily(self) -> None:
        """Atomically rename the active leaderboard to a dated archive key."""
        archive_key = f"leaderboard:archive:{date.today()}".encode()
        pipe = self._client.pipeline()
        pipe.rename(_DAILY_KEY, archive_key)
        pipe.expire(archive_key, _ARCHIVE_TTL)
        pipe.execute()
