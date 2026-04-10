from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from balances.domain.entities import BalanceEntity, TransactionEntity


class AbstractBalanceRepository(ABC):
    """Port for balance persistence operations."""

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> BalanceEntity | None:
        """Return the balance for a user, or None if it does not exist."""

    @abstractmethod
    def create(self, user_id: UUID) -> BalanceEntity:
        """Persist a new zero-balance wallet for a user."""

    @abstractmethod
    def increment(self, user_id: UUID, amount: int) -> None:
        """Atomically add credits to a user's balance."""


class AbstractTransactionRepository(ABC):
    """Port for transaction persistence operations."""

    @abstractmethod
    def create(
        self,
        event_id: UUID,
        balance_id: UUID,
        amount: int,
        transaction_type: str,
    ) -> TransactionEntity:
        """Persist a new transaction record."""

    @abstractmethod
    def list_by_user_id(
        self,
        user_id: UUID,
        start: int,
        limit: int,
    ) -> tuple[int, list[TransactionEntity]]:
        """Return a page of transactions and the total count for a user."""
