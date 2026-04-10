"""Pure unit tests for the RewardCalculator domain service."""

import pytest

from levels.domain.services import RewardCalculator


class TestRewardCalculator:
    """Tests for RewardCalculator.calculate."""

    def setup_method(self) -> None:
        self.calculator = RewardCalculator()

    def test_full_reward_when_wpm_meets_goal(self) -> None:
        """Should return full cost when user WPM exactly meets goal."""
        result = self.calculator.calculate(user_wpm=60, goal_wpm=60, level_cost=100)
        assert result == 100

    def test_full_reward_when_wpm_exceeds_goal(self) -> None:
        """Should cap reward at full cost even when user WPM exceeds goal."""
        result = self.calculator.calculate(user_wpm=90, goal_wpm=60, level_cost=100)
        assert result == 100

    def test_proportional_reward_when_below_goal(self) -> None:
        """Should return proportional reward when user WPM is below goal."""
        result = self.calculator.calculate(user_wpm=30, goal_wpm=60, level_cost=100)
        assert result == 50

    def test_reward_is_floored(self) -> None:
        """Should floor the result to the nearest integer."""
        result = self.calculator.calculate(user_wpm=1, goal_wpm=3, level_cost=100)
        assert result == 33

    def test_zero_reward_for_very_low_wpm(self) -> None:
        """Should return 0 when WPM is extremely low relative to cost."""
        result = self.calculator.calculate(user_wpm=1, goal_wpm=100, level_cost=1)
        assert result == 0
