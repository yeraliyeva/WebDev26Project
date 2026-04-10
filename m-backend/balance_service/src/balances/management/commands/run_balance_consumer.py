from django.core.management.base import BaseCommand

from balances.infrastructure.kafka.consumer import build_consumer


class Command(BaseCommand):
    """Django management command that starts the Kafka consumer loop."""

    help = "Start the balance Kafka consumer (blocking)."

    def handle(self, *args, **options) -> None:
        """Instantiate and run the consumer until interrupted."""
        consumer = build_consumer()
        consumer.run()
