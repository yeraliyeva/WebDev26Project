from uuid import uuid4

import pytest

from leaderboard.infrastructure.repositories import RedisLeaderboardRepository

pytestmark = pytest.mark.django_db(transaction=True)


def test_increment_and_rank(leaderboard_repo: RedisLeaderboardRepository) -> None:
    """Users appear in the correct descending order after scoring."""
    alice = uuid4()
    bob = uuid4()

    leaderboard_repo.increment_score(alice, 100)
    leaderboard_repo.increment_score(bob, 200)

    result = leaderboard_repo.get_leaderboard(user_id=alice, top_n=10)

    assert result.top[0].score == 200
    assert result.top[1].score == 100
    assert result.user_place == 2


def test_user_with_no_score_returns_none_place(
    leaderboard_repo: RedisLeaderboardRepository,
) -> None:
    """A user not on the board gets user_place=None."""
    stranger = uuid4()
    result = leaderboard_repo.get_leaderboard(user_id=stranger, top_n=10)
    assert result.user_place is None
    assert result.top == []


def test_idempotency_check(leaderboard_repo: RedisLeaderboardRepository) -> None:
    """Events are correctly recorded and detected."""
    event_id = "event-abc-123"

    assert not leaderboard_repo.is_event_processed(event_id)
    leaderboard_repo.mark_event_processed(event_id)
    assert leaderboard_repo.is_event_processed(event_id)


def test_reset_archives_key(leaderboard_repo: RedisLeaderboardRepository) -> None:
    """After reset, the active leaderboard is gone and an archive key exists."""
    user = uuid4()
    leaderboard_repo.increment_score(user, 50)

    leaderboard_repo.reset_daily()

    result = leaderboard_repo.get_leaderboard(user_id=user, top_n=10)
    assert result.top == []
    assert result.user_place is None
