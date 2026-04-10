"""Pytest configuration and shared fixtures for the levels service."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """Returns a DRF test client with Traefik identity headers pre-set."""
    client = APIClient()
    client.credentials(
        HTTP_X_USER_ID="550e8400-e29b-41d4-a716-446655440000",
        HTTP_X_USERNAME="testuser",
    )
    return client
