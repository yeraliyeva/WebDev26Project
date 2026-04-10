from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class BalanceEntity:
    """Represents a user's current credit wallet."""

    id: UUID
    user_id: UUID
    balance: int
    updated_at: datetime


@dataclass(frozen=True)
class TransactionEntity:
    """An immutable record of a single balance change."""

    id: UUID
    event_id: UUID
    balance_id: UUID
    amount: int
    type: Literal["CREDIT", "DEBIT"]
    created_at: datetime
