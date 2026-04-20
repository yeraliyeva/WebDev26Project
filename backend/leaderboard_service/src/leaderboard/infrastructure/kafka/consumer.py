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
    """Long-running Kafka consumer that processes submit.rewarded events.

    Runs with enable.auto.commit=false. Offsets are committed only after
    the event has been fully processed or identified as a duplicate.

    Args:
        use_case: RecordRewardUseCase wired with a real Redis repository.
        bootstrap_servers: Comma-separated Kafka broker addresses.
        group_id: Consumer group identifier.
        topic: Kafka topic to subscribe to.
    """

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
                    if message.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        logger.warning("Topic not yet available, retrying... %s", message.error())
                        continue
                    raise KafkaException(message.error())

                self._handle(message)
                self._consumer.commit(message=message, asynchronous=False)
        except KeyboardInterrupt:
            logger.info("Leaderboard consumer stopping.")
        finally:
            self._consumer.close()

    def _handle(self, message) -> None:
        """Deserialise a single message and delegate to the use case.

        After processing, broadcast the updated leaderboard snapshot to all
        connected WebSocket clients via the Django Channels Redis layer.

        Args:
            message: A confluent_kafka Message object.
        """
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

            # ── Broadcast live update to all WebSocket subscribers ────────
            try:
                self._broadcast_snapshot(payload["user_id"])
            except Exception:  # noqa: BLE001
                logger.exception("Failed to broadcast leaderboard snapshot via WebSocket")

        except Exception:
            logger.exception("Failed to process leaderboard message: %s", message.value())

    def _broadcast_snapshot(self, triggering_user_id: str) -> None:
        """Push the current leaderboard state to the 'leaderboard' channel group.

        Called synchronously from the Kafka consumer thread. Uses
        ``async_to_sync`` so the async channel layer can be invoked from a
        regular thread without an event loop.

        Args:
            triggering_user_id: UUID string of the user whose score changed.
        """
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from decouple import config as env_config
        from leaderboard.infrastructure.redis_client import get_redis_client
        from leaderboard.infrastructure.repositories import RedisLeaderboardRepository
        from leaderboard.application.use_cases.get_leaderboard import GetLeaderboardUseCase
        from django.conf import settings
        from uuid import UUID, uuid4

        use_case = GetLeaderboardUseCase(
            repository=RedisLeaderboardRepository(client=get_redis_client()),
            top_n=settings.LEADERBOARD_TOP_N,
        )
        try:
            user_id = UUID(triggering_user_id)
        except ValueError:
            user_id = uuid4()

        dto = use_case.execute(user_id=user_id)
        snapshot = {
            "top": [
                {"place": e.place, "user_id": str(e.user_id), "score": e.score}
                for e in dto.top
            ],
            "user_place": dto.user_place,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "leaderboard",
            {"type": "leaderboard.update", "data": snapshot},
        )


def build_consumer() -> LeaderboardEventConsumer:
    """Wire up the consumer with production dependencies.

    Returns:
        A fully configured LeaderboardEventConsumer.
    """
    redis_client = get_redis_client()
    repository = RedisLeaderboardRepository(client=redis_client)
    use_case = RecordRewardUseCase(repository=repository)

    return LeaderboardEventConsumer(
        use_case=use_case,
        bootstrap_servers=config("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092"),
        group_id=config("KAFKA_GROUP_ID", default="leaderboard-service"),
        topic=config("KAFKA_TOPIC_SUBMIT_REWARDED", default="submit.rewarded"),
    )
