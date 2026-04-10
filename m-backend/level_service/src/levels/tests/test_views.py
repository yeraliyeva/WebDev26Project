"""Integration tests for the levels presentation layer."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from levels.tests.factories import LevelFactory, SubmitFactory

USER_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.mark.django_db
class TestLevelListView:
    """Tests for GET /level."""

    def test_returns_paginated_levels(self, api_client: APIClient) -> None:
        """Should return a list and total count of levels."""
        LevelFactory.create_batch(5)

        response = api_client.get("/level?start=0&limit=3")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        assert len(response.data["results"]) == 3

    def test_returns_empty_list_when_no_levels(self, api_client: APIClient) -> None:
        """Should return count=0 and empty results when no levels exist."""
        response = api_client.get("/level")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []


@pytest.mark.django_db
class TestLevelDetailView:
    """Tests for GET /level/{uuid}."""

    def test_returns_level_data(self, api_client: APIClient) -> None:
        """Should return level data for a valid uuid."""
        level = LevelFactory()

        response = api_client.get(f"/level/{level.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(level.id)
        assert response.data["cost"] == level.cost

    def test_returns_404_for_unknown_level(self, api_client: APIClient) -> None:
        """Should return 404 for a UUID that does not exist."""
        response = api_client.get(f"/level/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestLevelSubmitView:
    """Tests for POST /level."""

    @patch("levels.presentation.views._event_producer")
    def test_first_submit_awards_credits(
        self, mock_producer_factory: MagicMock, api_client: APIClient
    ) -> None:
        """Should award credits on a first-time submit at or above goal WPM."""
        mock_producer_factory.return_value = MagicMock()
        level = LevelFactory(goal_wpm=50, cost=100)

        response = api_client.post(
            "/level/submit",
            {"level_id": str(level.id), "wpm": 60},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rewarded_credits"] == 100

    @patch("levels.presentation.views._event_producer")
    def test_repeat_submit_awards_zero_credits(
        self, mock_producer_factory: MagicMock, api_client: APIClient
    ) -> None:
        """Should award 0 credits when user has already submitted this level."""
        mock_producer_factory.return_value = MagicMock()
        level = LevelFactory(goal_wpm=50, cost=100)
        SubmitFactory(level=level, user_id=uuid.UUID(USER_ID), rewarded_credits=100)

        response = api_client.post(
            "/level/submit",
            {"level_id": str(level.id), "wpm": 80},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rewarded_credits"] == 0

    def test_returns_404_for_unknown_level(self, api_client: APIClient) -> None:
        """Should return 404 when the submitted level_id does not exist."""
        response = api_client.post(
            "/level/submit",
            {"level_id": str(uuid.uuid4()), "wpm": 60},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_400_for_invalid_wpm(self, api_client: APIClient) -> None:
        """Should return 400 for wpm values below 1."""
        level = LevelFactory()

        response = api_client.post(
            "/level/submit",
            {"level_id": str(level.id), "wpm": 0},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
