"""Pytest configuration and shared fixtures."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """Returns an unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def auth_client(api_client: APIClient, db) -> APIClient:
    """Returns an authenticated DRF test client."""
    from users.tests.factories import UserFactory

    user = UserFactory()
    from rest_framework_simplejwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
