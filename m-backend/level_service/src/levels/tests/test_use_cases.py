"""Unit tests for levels application use cases."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from levels.application.dto import SubmitLevelDTO
from levels.application.exceptions import InvalidWpmError, LevelNotFoundError
from levels.application.use_cases.submit_level import SubmitLevelUseCase
from levels.domain.entities import LevelEntity, SubmitEntity
from levels.domain.services import RewardCalculator


def _make_level(goal_wpm: int = 60, cost: int = 100) -> LevelEntity:
    now = datetime.now(tz=timezone.utc)
    return LevelEntity(
        id=uuid.uuid4(),
        text="sample text",
        cost=cost,
        goal_wpm=goal_wpm,
        created_at=now,
        updated_at=now,
    )


def _make_submit_entity(level_id: uuid.UUID, user_id: uuid.UUID, credits: int) -> SubmitEntity:
    return SubmitEntity(
        id=uuid.uuid4(),
        level_id=level_id,
        user_id=user_id,
        wpm=70,
        rewarded_credits=credits,
        created_at=datetime.now(tz=timezone.utc),
    )


class TestSubmitLevelUseCase:
    """Tests for SubmitLevelUseCase."""

    def _make_use_case(
        self,
        level_repo: MagicMock,
        submit_repo: MagicMock,
        calculator: RewardCalculator | None = None,
        producer: MagicMock | None = None,
    ) -> SubmitLevelUseCase:
        return SubmitLevelUseCase(
            level_repository=level_repo,
            submit_repository=submit_repo,
            reward_calculator=calculator or RewardCalculator(),
            event_producer=producer or MagicMock(),
        )

    def test_raises_for_nonpositive_wpm(self) -> None:
        """Should raise InvalidWpmError when wpm is zero or negative."""
        use_case = self._make_use_case(MagicMock(), MagicMock())
        dto = SubmitLevelDTO(
            level_id=uuid.uuid4(), user_id=uuid.uuid4(), username="u", wpm=0
        )
        with pytest.raises(InvalidWpmError):
            use_case.execute(dto)

    def test_raises_when_level_not_found(self) -> None:
        """Should raise LevelNotFoundError when level does not exist."""
        level_repo = MagicMock()
        level_repo.get_by_id.return_value = None
        submit_repo = MagicMock()

        use_case = self._make_use_case(level_repo, submit_repo)
        dto = SubmitLevelDTO(
            level_id=uuid.uuid4(), user_id=uuid.uuid4(), username="u", wpm=50
        )
        with pytest.raises(LevelNotFoundError):
            use_case.execute(dto)

    def test_gives_zero_credits_on_repeat_submit(self) -> None:
        """Should award 0 credits if user has already submitted this level."""
        level = _make_level()
        level_repo = MagicMock()
        level_repo.get_by_id.return_value = level

        submit_repo = MagicMock()
        submit_repo.has_prior_submit.return_value = True
        submit_repo.save.side_effect = lambda s: s

        producer = MagicMock()
        use_case = self._make_use_case(level_repo, submit_repo, producer=producer)

        dto = SubmitLevelDTO(
            level_id=level.id, user_id=uuid.uuid4(), username="u", wpm=80
        )
        result = use_case.execute(dto)

        assert result.rewarded_credits == 0
        producer.publish_submit_rewarded.assert_not_called()

    def test_publishes_event_when_credits_awarded(self) -> None:
        """Should publish a Kafka event when the user earns credits."""
        level = _make_level(goal_wpm=60, cost=100)
        user_id = uuid.uuid4()

        level_repo = MagicMock()
        level_repo.get_by_id.return_value = level

        submit_repo = MagicMock()
        submit_repo.has_prior_submit.return_value = False
        saved = _make_submit_entity(level.id, user_id, credits=100)
        submit_repo.save.return_value = saved

        producer = MagicMock()
        use_case = self._make_use_case(level_repo, submit_repo, producer=producer)

        dto = SubmitLevelDTO(
            level_id=level.id, user_id=user_id, username="alice", wpm=60
        )
        use_case.execute(dto)

        producer.publish_submit_rewarded.assert_called_once_with(
            event_id=saved.id,
            user_id=saved.user_id,
            username="alice",
            amount=100,
        )

    def test_does_not_publish_event_when_zero_credits(self) -> None:
        """Should not publish Kafka event when rewarded_credits is 0."""
        level = _make_level()
        level_repo = MagicMock()
        level_repo.get_by_id.return_value = level

        submit_repo = MagicMock()
        submit_repo.has_prior_submit.return_value = True
        submit_repo.save.side_effect = lambda s: s

        producer = MagicMock()
        use_case = self._make_use_case(level_repo, submit_repo, producer=producer)

        dto = SubmitLevelDTO(
            level_id=level.id, user_id=uuid.uuid4(), username="u", wpm=50
        )
        use_case.execute(dto)

        producer.publish_submit_rewarded.assert_not_called()
