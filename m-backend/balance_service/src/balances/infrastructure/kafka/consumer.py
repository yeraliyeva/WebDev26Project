from __future__ import annotations

import json
import logging
from uuid import UUID

from confluent_kafka import Consumer, KafkaError, KafkaException
from decouple import config
from django.db import IntegrityError

from balances.application.exceptions import BalanceNotFoundError
from balances.application.use_cases.create_balance import CreateBalanceUseCase
from balances.application.use_cases.credit_balance import CreditBalanceUseCase
from balances.infrastructure.repositories import DjangoBalanceRepository, DjangoTransactionRepository

logger = logging.getLogger(__name__)


class BalanceEventConsumer:
    """Long-running Kafka consumer for balance-related events."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
    ) -> None:
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._topics = topics

    def run(self) -> None:
        """Block indefinitely, polling and processing Kafka messages."""
        self._consumer.subscribe(self._topics)
        logger.info("Balance consumer started. Topics: %s", self._topics)

        try:
            while True:
                message = self._consumer.poll(timeout=1.0)
                if message is None:
                    continue
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(message.error())

                self._handle(message)
                self._consumer.commit(message=message, asynchronous=False)
        except KeyboardInterrupt:
            logger.info("Balance consumer stopping.")
        finally:
            self._consumer.close()

    def _handle(self, message) -> None:
        """Deserialise and dispatch a single message to the correct use case."""
        try:
            payload = json.loads(message.value().decode("utf-8"))
            event = payload.get("event")

            if event in ("user.registered",):
                self._handle_user_registered(payload)
            elif event == "submit.rewarded":
                self._handle_submit_rewarded(payload)
            else:
                logger.debug("Ignoring unknown event type: %s", event)

        except IntegrityError:
            # Duplicate user_id or event_id — safe to skip; offset will be committed.
            logger.info("Duplicate event skipped: %s", message.value())
        except BalanceNotFoundError:
            # submit.rewarded arrived before user.registered wallet was created.
            # Do NOT commit offset — let the message retry so ordering resolves.
            logger.warning("Balance not found — will retry: %s", message.value())
            raise
        except Exception:
            logger.exception("Unexpected error processing message: %s", message.value())
            raise

    def _handle_user_registered(self, payload: dict) -> None:
        """Delegate user.registered to CreateBalanceUseCase."""
        use_case = CreateBalanceUseCase(
            balance_repository=DjangoBalanceRepository(),
        )
        use_case.execute(user_id=UUID(payload["user_id"]))

    def _handle_submit_rewarded(self, payload: dict) -> None:
        """Delegate submit.rewarded to CreditBalanceUseCase."""
        use_case = CreditBalanceUseCase(
            balance_repository=DjangoBalanceRepository(),
            transaction_repository=DjangoTransactionRepository(),
        )
        use_case.execute(
            event_id=UUID(payload["event_id"]),
            user_id=UUID(payload["user_id"]),
            amount=int(payload["amount"]),
        )


def build_consumer() -> BalanceEventConsumer:
    """Wire up the consumer with production configuration."""
    return BalanceEventConsumer(
        bootstrap_servers=config("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092"),
        group_id=config("KAFKA_GROUP_ID", default="balance-service"),
        topics=[
            config("KAFKA_TOPIC_USER_REGISTERED", default="user.registered"),
            config("KAFKA_TOPIC_SUBMIT_REWARDED", default="submit.rewarded"),
        ],
    )
