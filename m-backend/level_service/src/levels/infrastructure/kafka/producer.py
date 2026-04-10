"""Kafka event producer for submit reward events."""

from __future__ import annotations

import json
import uuid

from confluent_kafka import Producer
from django.conf import settings


class SubmitEventProducer:
    """Publishes submit reward events so balance and leaderboard services can react."""

    def __init__(self) -> None:
        self._producer = Producer(
            {"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS}
        )

    def publish_submit_rewarded(
        self,
        event_id: uuid.UUID,
        user_id: uuid.UUID,
        username: str,
        amount: int,
    ) -> None:
        """Publishes a submit.rewarded event.

        Args:
            event_id: The Submit's UUID; used as idempotency key by consumers.
            user_id: UUID of the user who earned the reward.
            username: Display name of the user.
            amount: Credits awarded.
        """
        payload = json.dumps(
            {
                "event": "submit.rewarded",
                "event_id": str(event_id),
                "user_id": str(user_id),
                "username": username,
                "amount": amount,
            }
        ).encode()

        self._producer.produce(
            topic=settings.KAFKA_TOPIC_SUBMIT_REWARDED,
            key=str(user_id).encode(),
            value=payload,
        )
        self._producer.flush()
