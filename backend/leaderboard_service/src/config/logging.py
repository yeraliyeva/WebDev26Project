from __future__ import annotations

import os
import logging


class ServiceContextFilter(logging.Filter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self._service_name
        record.env = os.getenv("DJANGO_ENV", "development")
        return True

