import uuid
from django.db import models


class Balance(models.Model):
    """Persistent credit wallet for a single user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)
    balance = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "balances"

    def __str__(self) -> str:
        return f"Balance(user={self.user_id}, balance={self.balance})"


class Transaction(models.Model):
    """Immutable record of a single balance mutation."""

    class TransactionType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(unique=True)
    balance = models.ForeignKey(Balance, on_delete=models.PROTECT, related_name="transactions")
    amount = models.PositiveIntegerField()
    type = models.CharField(max_length=6, choices=TransactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Transaction(event={self.event_id}, amount={self.amount}, type={self.type})"
