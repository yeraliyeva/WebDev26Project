from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from balances.application.exceptions import BalanceNotFoundError
from balances.application.use_cases.create_balance import CreateBalanceUseCase
from balances.application.use_cases.credit_balance import CreditBalanceUseCase
from balances.application.use_cases.get_balance import GetBalanceUseCase
from balances.application.use_cases.list_transactions import ListTransactionsUseCase
from balances.domain.entities import BalanceEntity, TransactionEntity
from datetime import datetime, timezone


def _make_balance(user_id=None, balance=0):
    return BalanceEntity(
        id=uuid4(),
        user_id=user_id or uuid4(),
        balance=balance,
        updated_at=datetime.now(timezone.utc),
    )


def test_create_balance_skips_existing_user() -> None:
    """CreateBalanceUseCase must not call create if balance already exists."""
    repo = MagicMock()
    repo.get_by_user_id.return_value = _make_balance()

    use_case = CreateBalanceUseCase(balance_repository=repo)
    use_case.execute(user_id=uuid4())

    repo.create.assert_not_called()


def test_create_balance_creates_for_new_user() -> None:
    """CreateBalanceUseCase calls create when no balance exists."""
    repo = MagicMock()
    repo.get_by_user_id.return_value = None
    user_id = uuid4()

    use_case = CreateBalanceUseCase(balance_repository=repo)
    use_case.execute(user_id=user_id)

    repo.create.assert_called_once_with(user_id=user_id)


def test_credit_balance_raises_when_wallet_missing() -> None:
    """CreditBalanceUseCase raises BalanceNotFoundError for unknown users."""
    balance_repo = MagicMock()
    balance_repo.get_by_user_id.return_value = None
    tx_repo = MagicMock()

    use_case = CreditBalanceUseCase(
        balance_repository=balance_repo,
        transaction_repository=tx_repo,
    )

    with pytest.raises(BalanceNotFoundError):
        use_case.execute(event_id=uuid4(), user_id=uuid4(), amount=80)

    balance_repo.increment.assert_not_called()
    tx_repo.create.assert_not_called()


def test_credit_balance_increments_and_records() -> None:
    """CreditBalanceUseCase calls increment and creates a transaction."""
    user_id = uuid4()
    balance = _make_balance(user_id=user_id, balance=0)
    balance_repo = MagicMock()
    balance_repo.get_by_user_id.return_value = balance
    tx_repo = MagicMock()
    event_id = uuid4()

    use_case = CreditBalanceUseCase(
        balance_repository=balance_repo,
        transaction_repository=tx_repo,
    )
    use_case.execute(event_id=event_id, user_id=user_id, amount=80)

    balance_repo.increment.assert_called_once_with(user_id=user_id, amount=80)
    tx_repo.create.assert_called_once_with(
        event_id=event_id,
        balance_id=balance.id,
        amount=80,
        transaction_type="CREDIT",
    )


def test_get_balance_raises_when_not_found() -> None:
    """GetBalanceUseCase raises BalanceNotFoundError for unknown user."""
    repo = MagicMock()
    repo.get_by_user_id.return_value = None

    use_case = GetBalanceUseCase(balance_repository=repo)
    with pytest.raises(BalanceNotFoundError):
        use_case.execute(user_id=uuid4())


def test_list_transactions_returns_dto() -> None:
    """ListTransactionsUseCase maps repository results to a TransactionListDTO."""
    user_id = uuid4()
    tx = TransactionEntity(
        id=uuid4(),
        event_id=uuid4(),
        balance_id=uuid4(),
        amount=80,
        type="CREDIT",
        created_at=datetime.now(timezone.utc),
    )
    repo = MagicMock()
    repo.list_by_user_id.return_value = (1, [tx])

    use_case = ListTransactionsUseCase(transaction_repository=repo)
    dto = use_case.execute(user_id=user_id, start=0, limit=20)

    assert dto.count == 1
    assert dto.results[0].amount == 80
    assert dto.results[0].type == "CREDIT"
