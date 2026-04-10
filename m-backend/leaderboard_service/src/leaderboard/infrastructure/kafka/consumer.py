from __future__ import annotations

import json
import logging
from uuid import UUID

from confluent_kafka import Consumer, KafkaError, KafkaException
from decouple import config

from leaderboard.application.use_cases.record_reward import RecordRewardUseCase
from leaderboard.infrastructure.redis_client import get_redis_client
from leaderboard.infrastructure.repositories import RedisLeaderboardRepository

logger = logging.getLogger(__name__)


class LeaderboardEventConsumer:
    """Long-running Kafka consumer that processes submit.rewarded events."""

    def __init__(
        self,
        use_case: RecordRewardUseCase,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
    ) -> None:
        self._use_case = use_case
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._topic = topic

    def run(self) -> None:
        """Block indefinitely, consuming and processing messages."""
        self._consumer.subscribe([self._topic])
        logger.info("Leaderboard consumer started. Topic: %s", self._topic)

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
            logger.info("Leaderboard consumer stopping.")
        finally:
            self._consumer.close()

    def _handle(self, message) -> None:
        """Deserialise a single message and delegate to the use case."""
        try:
            payload = json.loads(message.value().decode("utf-8"))
            event = payload.get("event")

            if event != "submit.rewarded":
                return

            self._use_case.execute(
                event_id=payload["event_id"],
                user_id=UUID(payload["user_id"]),
                amount=int(payload["amount"]),
            )
        except Exception:
            logger.exception("Failed to process leaderboard message: %s", message.value())


def build_consumer() -> LeaderboardEventConsumer:
    """Wire up the consumer with production dependencies."""
    redis_client = get_redis_client()
    repository = RedisLeaderboardRepository(client=redis_client)
    use_case = RecordRewardUseCase(repository=repository)

    return LeaderboardEventConsumer(
        use_case=use_case,
        bootstrap_servers=config("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092"),
        group_id=config("KAFKA_GROUP_ID", default="leaderboard-service"),
        topic=config("KAFKA_TOPIC_SUBMIT_REWARDED", default="submit.rewarded"),
    )
