import fakeredis
import pytest

from leaderboard.infrastructure.repositories import RedisLeaderboardRepository


@pytest.fixture()
def redis_client():
    """In-memory Redis substitute — no server required."""
    return fakeredis.FakeRedis(decode_responses=False)


@pytest.fixture()
def leaderboard_repo(redis_client):
    """Repository wired to fakeredis."""
    return RedisLeaderboardRepository(client=redis_client)
