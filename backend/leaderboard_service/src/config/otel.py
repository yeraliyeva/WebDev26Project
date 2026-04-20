from __future__ import annotations

import os

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider


def setup_otel(service_name: str) -> None:
    endpoint = os.getenv("OTLP_ENDPOINT", "http://tempo:4317")
    endpoint = endpoint.replace("https://", "").replace("http://", "")

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    set_tracer_provider(provider)

    DjangoInstrumentor().instrument()

