from __future__ import annotations

import redis
from decouple import config


def get_redis_client() -> redis.Redis:
    """Create and return a Redis client from the REDIS_URL environment variable."""
    url: str = config("REDIS_URL", default="redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=False)
