"""Integration tests for auth presentation layer."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestLoginView:
    """Tests for POST /login."""

    def test_returns_token_pair_on_valid_credentials(self, api_client: APIClient) -> None:
        """Should return access and refresh tokens on correct credentials."""
        UserFactory(username="testuser", password=None)
        user = UserFactory.__factory__.build()

        user = UserFactory(username="loginuser")
        user.set_password("securepass")
        user.save()

        response = api_client.post(
            "/login", {"login": "loginuser", "password": "securepass"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_returns_401_on_wrong_password(self, api_client: APIClient) -> None:
        """Should return 401 for incorrect password."""
        UserFactory(username="anotheruser")

        response = api_client.post(
            "/login", {"login": "anotheruser", "password": "wrongpass"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_401_for_nonexistent_user(self, api_client: APIClient) -> None:
        """Should return 401 when user does not exist."""
        response = api_client.post(
            "/login", {"login": "ghost", "password": "anything"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRegisterView:
    """Tests for POST /registration."""

    def test_creates_user_and_returns_201(self, api_client: APIClient) -> None:
        """Should create a user and return their profile."""
        response = api_client.post(
            "/registration",
            {"username": "brand_new", "email": "brand@test.com", "password": "password123"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "brand_new"
        assert "password" not in response.data

    def test_returns_409_on_duplicate_username(self, api_client: APIClient) -> None:
        """Should return 409 when username is already taken."""
        UserFactory(username="dupuser")

        response = api_client.post(
            "/registration",
            {"username": "dupuser", "email": "other@test.com", "password": "password123"},
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestUserDetailView:
    """Tests for GET /users/{user_id}."""

    def test_returns_user_profile(self, auth_client: APIClient) -> None:
        """Should return user profile for authenticated request."""
        target = UserFactory()

        response = auth_client.get(f"/users/{target.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(target.id)

    def test_returns_401_for_unauthenticated(self, api_client: APIClient) -> None:
        """Should return 401 for unauthenticated requests."""
        target = UserFactory()

        response = api_client.get(f"/users/{target.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
