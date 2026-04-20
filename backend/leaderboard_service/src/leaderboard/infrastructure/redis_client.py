from __future__ import annotations

import redis
from decouple import config


def get_redis_client() -> redis.Redis:
    """Create and return a Redis client from the REDIS_URL environment variable.

    Returns:
        A connected Redis client with decode_responses disabled
        (bytes are used internally so UUIDs remain unambiguous).
    """
    url: str = config("REDIS_URL", default="redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=False)
