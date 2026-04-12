import uuid
import factory
from balances.infrastructure.models import Balance, Transaction


class BalanceFactory(factory.django.DjangoModelFactory):
    """Create Balance rows with sensible defaults."""

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    balance = 0

    class Meta:
        model = Balance


class TransactionFactory(factory.django.DjangoModelFactory):
    """Create Transaction rows linked to a balance."""

    id = factory.LazyFunction(uuid.uuid4)
    event_id = factory.LazyFunction(uuid.uuid4)
    balance = factory.SubFactory(BalanceFactory)
    amount = 80
    type = "CREDIT"

    class Meta:
        model = Transaction
