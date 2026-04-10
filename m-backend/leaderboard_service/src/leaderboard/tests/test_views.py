from unittest.mock import patch
from uuid import uuid4

import fakeredis
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from leaderboard.infrastructure.repositories import RedisLeaderboardRepository

pytestmark = pytest.mark.django_db


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=False)


def test_leaderboard_returns_200(api_client: APIClient, fake_redis) -> None:
    """GET /leaderboard returns 200 with correct structure."""
    user_id = uuid4()
    repo = RedisLeaderboardRepository(client=fake_redis)
    repo.increment_score(user_id, 100)

    with patch(
        "leaderboard.presentation.views.get_redis_client", return_value=fake_redis
    ):
        response = api_client.get(
            "/leaderboard", HTTP_X_USER_ID=str(user_id)
        )

    assert response.status_code == 200
    data = response.json()
    assert "top" in data
    assert "user_place" in data
    assert data["top"][0]["score"] == 100
    assert data["user_place"] == 1


def test_leaderboard_user_not_on_board(api_client: APIClient, fake_redis) -> None:
    """User with no score today gets user_place=null."""
    user_id = uuid4()

    with patch(
        "leaderboard.presentation.views.get_redis_client", return_value=fake_redis
    ):
        response = api_client.get(
            "/leaderboard", HTTP_X_USER_ID=str(user_id)
        )

    assert response.status_code == 200
    assert response.json()["user_place"] is None
