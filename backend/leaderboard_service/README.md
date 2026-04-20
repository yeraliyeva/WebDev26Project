# Leaderboard Service — Complete Service Documentation

## Purpose

Maintains a real-time daily leaderboard of users ranked by credits earned today.
Responsible for:
- Consuming `submit.rewarded` events and updating Redis ZSET scores
- Serving the top N users and the requesting user's rank in one response
- Resetting the leaderboard atomically at midnight UTC, archiving the previous day's data

This service is **read-heavy and latency-sensitive**. Redis serves all ranking queries —
no database queries during reads. The consumer is the only write path.

---

## Technology Stack

| Concern          | Choice                      | Reason                                                     |
|------------------|-----------------------------|-------------------------------------------------------------|
| Framework        | Django 5 + DRF 3.15         | Consistent with other services                              |
| Primary store    | Redis 7 (ZSET)              | O(log N) writes, O(log N + M) reads; purpose-built for ranking |
| Database         | None                        | No persistent state needed; Redis is the source of truth    |
| Event consuming  | confluent-kafka             | Consumes `submit.rewarded`                                  |
| Consumer runner  | Django management command   | Long-running process alongside Gunicorn                     |
| Leaderboard reset| Django management command   | Run via cron / Celery Beat at midnight UTC                  |
| Config           | python-decouple             |                                                             |
| Testing          | pytest + fakeredis          | In-memory Redis for unit and integration tests              |
| WSGI server      | Gunicorn                    |                                                             |

---

## Directory Structure

```
leaderboard_service/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── pytest.ini
├── .env
└── src/
    ├── manage.py
    ├── config/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── wsgi.py
    │   ├── urls.py
    │   └── settings/
    │       ├── __init__.py
    │       ├── base.py
    │       ├── development.py
    │       └── production.py
    └── leaderboard/
        ├── admin.py
        ├── apps.py
        ├── domain/
        │   ├── entities.py         # LeaderboardEntry, LeaderboardResult
        │   └── repositories.py     # AbstractLeaderboardRepository
        ├── application/
        │   ├── dto.py              # LeaderboardResponseDTO
        │   ├── exceptions.py       # (minimal; Redis rarely throws domain exceptions)
        │   └── use_cases/
        │       ├── get_leaderboard.py      # GetLeaderboardUseCase
        │       ├── record_reward.py        # RecordRewardUseCase — called by consumer
        │       └── reset_leaderboard.py    # ResetLeaderboardUseCase — called by cron
        ├── infrastructure/
        │   ├── redis_client.py             # Redis connection factory
        │   ├── repositories.py             # RedisLeaderboardRepository
        │   └── kafka/
        │       └── consumer.py             # LeaderboardEventConsumer (management command)
        ├── management/
        │   └── commands/
        │       ├── run_leaderboard_consumer.py
        │       └── reset_leaderboard.py
        ├── presentation/
        │   ├── serializers.py
        │   ├── views.py
        │   ├── urls.py
        │   └── exception_handler.py
        └── tests/
            ├── conftest.py             # fakeredis fixture
            ├── test_repository.py      # RedisLeaderboardRepository with fakeredis
            ├── test_use_cases.py
            └── test_views.py
```

---

## Domain Model

```
LeaderboardEntry (frozen dataclass)
  place       : int
  user_id     : UUID
  score       : int

LeaderboardResult (frozen dataclass)
  top         : list[LeaderboardEntry]
  user_place  : int | None     — None if the requesting user is not on the board
```

No database models. No Django ORM in this service. Redis is the only persistence layer.

---

## Redis Data Structure

### Active leaderboard key

```
leaderboard:daily
```

ZSET where:
- **member** = user_id as string (UUID)
- **score** = cumulative credits earned today

Operations:

```redis
# Add/increment score (called on each submit.rewarded event)
ZINCRBY leaderboard:daily 80 "550e8400-e29b-41d4-a716-446655440000"

# Get top 10 with scores (descending)
ZREVRANGE leaderboard:daily 0 9 WITHSCORES

# Get user's rank (0-based, descending)
ZREVRANK leaderboard:daily "550e8400-e29b-41d4-a716-446655440000"
```

`ZINCRBY` is atomic — concurrent consumers writing different users' scores never conflict.
Same user appearing in multiple Kafka partitions is safe: increments accumulate correctly.

### Why store user_id and not username?

ZSET members must be stable keys. Usernames can theoretically change.
UUIDs are permanent. The API response that needs `username` fetches it
from the `X-Username` header for the requesting user's own entry,
and for the top-N list it returns `user_id` only (frontend can resolve if needed,
or a future enhancement calls auth service internally).

---

## Daily Reset

### Strategy: RENAME + TTL

At midnight UTC, `ResetLeaderboardUseCase` runs:

```python
pipe = redis.pipeline()
pipe.rename("leaderboard:daily", f"leaderboard:archive:{today}")
pipe.expire(f"leaderboard:archive:{today}", 60 * 60 * 24 * 7)  # 7-day archive
pipe.execute()
```

- `RENAME` is atomic — there is zero window where the leaderboard is empty.
- If `leaderboard:daily` doesn't exist yet (e.g. no submits today), `RENAME` raises
  `ResponseError`. The reset command catches this and exits cleanly.
- After rename, the next `ZINCRBY` creates a fresh `leaderboard:daily` automatically.

### Running the reset

Option A — cron inside the container:
```
0 0 * * * python /app/manage.py reset_leaderboard
```

Option B — Celery Beat (preferred if Celery is already in the stack):
```python
CELERY_BEAT_SCHEDULE = {
    "reset-leaderboard": {
        "task": "leaderboard.tasks.reset_leaderboard",
        "schedule": crontab(hour=0, minute=0),
    }
}
```

Option C — external cron job / Kubernetes CronJob hitting the management command.

---

## Kafka Topics Consumed

### `submit.rewarded`

Triggers `RecordRewardUseCase`.

```json
{
  "event": "submit.rewarded",
  "event_id": "submit-uuid",
  "user_id": "uuid",
  "username": "alice",
  "amount": 80
}
```

Consumer increments the user's ZSET score by `amount`.
`ZINCRBY` is idempotent in the sense that duplicate events would double-count scores.
To prevent this: the consumer stores processed `event_id` values in a Redis SET
with the same TTL as the leaderboard (midnight reset). Before processing, it checks
`SISMEMBER processed_events:daily <event_id>`. If already seen, skip.

```redis
# Idempotency check SET
SADD processed_events:daily "submit-uuid"
EXPIRE processed_events:daily 86400
```

Both the ZINCRBY and the SADD run in a single pipeline for atomicity.

---

## API Endpoints

All endpoints require a valid JWT. `X-User-Id` and `X-Username` injected by Traefik.

---

### `GET /leaderboard`

Returns the top 10 users and the requesting user's rank.

**Response `200`**
```json
{
  "top": [
    { "place": 1, "user_id": "uuid", "score": 840 },
    { "place": 2, "user_id": "uuid", "score": 720 },
    { "place": 3, "user_id": "uuid", "score": 600 }
  ],
  "user_place": 14
}
```

`user_place` is `null` if the requesting user has no score today.
`top` is configurable via `LEADERBOARD_TOP_N` env var, defaults to 10.

---

## Inter-Service Communication

This service **consumes** events. It does not produce any.
It does not make HTTP calls to any other service.

```
level_service → Kafka [submit.rewarded] → leaderboard_service consumer → Redis ZSET

Client → Traefik [auth-verify] → GET /leaderboard
```

---

## Idempotency Strategy

| Scenario                                      | Handling                                          |
|-----------------------------------------------|---------------------------------------------------|
| Duplicate `submit.rewarded` (Kafka retry)     | Check `processed_events:daily` SET before ZINCRBY |
| Consumer crash after Redis write, before commit | Event replayed; SET check prevents double-count  |
| Consumer crash before Redis write              | Event replayed; processed normally                |
| `leaderboard:daily` missing at reset time      | `RENAME` raises ResponseError; caught and ignored |

---

## Testing with fakeredis

Use `fakeredis` to test Redis operations without a running server:

```python
import fakeredis
import pytest

@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=False)

@pytest.fixture
def leaderboard_repo(redis_client):
    return RedisLeaderboardRepository(client=redis_client)
```

All `RedisLeaderboardRepository` tests use this fixture. No real Redis needed in CI.

---

## Code Style & Principles

- **No Django ORM** — this service has no database. Don't add one unless archiving
  leaderboard history to Postgres becomes a requirement.
- **Repository pattern over raw Redis calls in use cases** — use cases call
  `self._repository.add_score(user_id, delta)`, not `redis.zincrby(...)`.
  This makes testing trivial and keeps Redis an infrastructure detail.
- **`TOP_N` is a constant, not hardcoded** — read from settings, change without code deploy.
- **Consumer and HTTP server as separate processes** — `run_leaderboard_consumer` management
  command runs alongside Gunicorn in the same container, or as a sidecar.
- **RENAME not DEL for reset** — DEL creates a brief empty-leaderboard window.
  RENAME is atomic with zero downtime.

---

## CLI Setup Sequence

```bash
mkdir leaderboard_service && cd leaderboard_service
python3.12 -m venv .venv && source .venv/bin/activate

pip install django==5.0.* djangorestframework==3.15.* \
  redis==5.0.* confluent-kafka==2.4.* \
  python-decouple==3.8 pytest-django==4.8.* \
  pytest-mock==3.14.* fakeredis==2.23.* factory-boy==3.3.*
pip freeze > requirements.txt

mkdir src && cd src
django-admin startproject config .
python manage.py startapp leaderboard

# No migrations needed — no database models.

pytest src/leaderboard/tests/ -v
```

---

## Environment Variables

```env
DJANGO_ENV=development
SECRET_KEY=
ALLOWED_HOSTS=*
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_GROUP_ID=leaderboard-service
KAFKA_TOPIC_SUBMIT_REWARDED=submit.rewarded
LEADERBOARD_TOP_N=10
```