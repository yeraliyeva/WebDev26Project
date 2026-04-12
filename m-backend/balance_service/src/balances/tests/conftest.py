import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def api_client() -> APIClient:
    """DRF test client with no authentication overhead."""
    return APIClient()
