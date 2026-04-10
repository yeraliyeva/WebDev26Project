from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from leaderboard.application.use_cases.record_reward import RecordRewardUseCase
from leaderboard.application.use_cases.get_leaderboard import GetLeaderboardUseCase
from leaderboard.domain.entities import LeaderboardEntry, LeaderboardResult


def test_record_reward_skips_duplicate() -> None:
    """RecordRewardUseCase must not call increment_score for seen event_ids."""
    repo = MagicMock()
    repo.is_event_processed.return_value = True

    use_case = RecordRewardUseCase(repository=repo)
    use_case.execute(event_id="dup", user_id=uuid4(), amount=80)

    repo.increment_score.assert_not_called()
    repo.mark_event_processed.assert_not_called()


def test_record_reward_processes_new_event() -> None:
    """RecordRewardUseCase increments score and marks event for fresh events."""
    repo = MagicMock()
    repo.is_event_processed.return_value = False
    user_id = uuid4()

    use_case = RecordRewardUseCase(repository=repo)
    use_case.execute(event_id="new-evt", user_id=user_id, amount=80)

    repo.increment_score.assert_called_once_with(user_id=user_id, amount=80)
    repo.mark_event_processed.assert_called_once_with(event_id="new-evt")


def test_get_leaderboard_maps_to_dto() -> None:
    """GetLeaderboardUseCase correctly translates domain entities to DTOs."""
    user_id = uuid4()
    entry = LeaderboardEntry(place=1, user_id=user_id, score=300)
    domain_result = LeaderboardResult(top=[entry], user_place=1)

    repo = MagicMock()
    repo.get_leaderboard.return_value = domain_result

    use_case = GetLeaderboardUseCase(repository=repo, top_n=10)
    dto = use_case.execute(user_id=user_id)

    assert len(dto.top) == 1
    assert dto.top[0].score == 300
    assert dto.user_place == 1
