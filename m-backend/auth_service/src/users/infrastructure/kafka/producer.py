"""Kafka event producer for user domain events."""

from __future__ import annotations

import json
import uuid

from confluent_kafka import Producer
from django.conf import settings


class UserEventProducer:
    """Publishes user lifecycle events to Kafka topics."""

    def __init__(self) -> None:
        self._producer = Producer(
            {"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS}
        )

    def publish_user_registered(self, user_id: uuid.UUID, username: str) -> None:
        """Publishes a user.registered event so balance service creates a wallet.

        Args:
            user_id: UUID of the newly registered user.
            username: The user's chosen username.
        """
        payload = json.dumps(
            {"event": "user.registered", "user_id": str(user_id), "username": username}
        ).encode()

        self._producer.produce(
            topic=settings.KAFKA_TOPIC_USER_REGISTERED,
            key=str(user_id).encode(),
            value=payload,
        )
        self._producer.flush()
