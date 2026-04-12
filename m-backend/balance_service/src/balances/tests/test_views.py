from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from balances.tests.factories import BalanceFactory, TransactionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


def test_get_balance_returns_200(api_client: APIClient) -> None:
    """GET /balance/{user_id} returns 200 with correct payload."""
    balance = BalanceFactory(balance=420)

    response = api_client.get(
        f"/balance/{balance.user_id}",
        HTTP_X_USER_ID=str(balance.user_id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 420
    assert str(data["user_id"]) == str(balance.user_id)


def test_get_balance_returns_404_for_unknown_user(api_client: APIClient) -> None:
    """GET /balance/{user_id} returns 404 when no wallet exists."""
    response = api_client.get(
        f"/balance/{uuid4()}",
        HTTP_X_USER_ID=str(uuid4()),
    )
    assert response.status_code == 404


def test_list_transactions_returns_paginated_results(api_client: APIClient) -> None:
    """GET /transactions/{user_id} returns count and results."""
    balance = BalanceFactory(balance=160)
    TransactionFactory(balance=balance, amount=80)
    TransactionFactory(balance=balance, amount=80)

    response = api_client.get(
        f"/transactions/{balance.user_id}",
        HTTP_X_USER_ID=str(balance.user_id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["type"] == "CREDIT"


def test_list_transactions_respects_limit(api_client: APIClient) -> None:
    """GET /transactions/{user_id}?limit=1 returns only one result."""
    balance = BalanceFactory()
    TransactionFactory.create_batch(3, balance=balance)

    response = api_client.get(
        f"/transactions/{balance.user_id}?limit=1",
        HTTP_X_USER_ID=str(balance.user_id),
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["count"] == 3


def test_list_transactions_empty_for_new_user(api_client: APIClient) -> None:
    """GET /transactions/{user_id} returns count=0 for a user with no transactions."""
    balance = BalanceFactory()

    response = api_client.get(
        f"/transactions/{balance.user_id}",
        HTTP_X_USER_ID=str(balance.user_id),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []
