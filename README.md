# 🐱 TypeCat — Competitive Typing Platform

> A real-time competitive typing practice platform built with a production-grade microservices architecture. Practice typing through thematic levels, earn credits based on your speed and accuracy, and compete on a global daily leaderboard.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Microservices](#-microservices)
  - [Auth Service](#auth-service)
  - [Level Service](#level-service)
  - [Balance Service](#balance-service)
  - [Leaderboard Service](#leaderboard-service)
- [Frontend](#-frontend)
- [Infrastructure](#-infrastructure)
- [Observability](#-observability)
- [API Reference](#-api-reference)
- [Event-Driven Architecture](#-event-driven-architecture)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Development Guide](#-development-guide)
- [Project Structure](#-project-structure)

---

## 🌟 Overview

TypeCat is a full-stack web application where users can:

- **Register & Login** using JWT-based authentication
- **Choose Levels** from a catalog of typing exercises (standard and cat-running mode)
- **Practice Typing** and earn credits based on speed (WPM) and accuracy relative to a level goal
- **Track Balance** — view current credits and full transaction history
- **Compete** on a real-time global daily leaderboard, reset at midnight UTC

The system is designed for scale: each domain is an independent service, data flows asynchronously via Kafka, and no user-facing action blocks on inter-service HTTP calls.

---

## 🏗️ Architecture

The system uses a **Security-First DMZ** approach. Only Traefik is exposed to the internet. All microservices and data stores live in an isolated internal network. Every protected request passes through the auth service before reaching any downstream service.

```
User Browser
     │
     ▼ :8000
┌──────────────────────────────────────────────────────┐
│                   Traefik Proxy                       │
│          (DMZ — only public entry point)             │
└──────────────────────────────────────────────────────┘
     │          │           │              │
     ▼          ▼           ▼              ▼
 /auth       /level      /balance     /leaderboard
Auth Svc   Level Svc  Balance Svc  Leaderboard Svc
 (PG)       (PG)        (PG)          (Redis)

Event Bus (Kafka):
  auth_service  ──► user.registered  ──► balance_service
  level_service ──► submit.rewarded  ──► balance_service
                                     └──► leaderboard_service

Debezium CDC:
  postgres_auth (users table) ──► dbz.public.users ──► balance_service
```

### Request Identity Flow

```
Client ──► Authorization: Bearer <token>
Traefik ──► GET /auth/verify  (ForwardAuth)
Auth Svc returns ──► 200 + X-User-Id + X-Username headers
Traefik forwards ──► downstream service with injected headers
Service reads ──► request.headers["X-User-Id"]  (no JWT parsing needed)
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | Django 5 + Django REST Framework 3.15 |
| WSGI Server | Gunicorn (4 workers, 60s timeout) |
| Databases | PostgreSQL 16 (auth, level, balance), Redis 7 (leaderboard) |
| ORM | Django ORM with psycopg3 |
| Message Queue | Apache Kafka (Confluent Platform 7.6.0) |
| CDC | Debezium 2.6 (PostgreSQL → Kafka) |
| Proxy / Gateway | Traefik v2 |
| Object Storage | MinIO (S3-compatible, for profile images) |
| Auth | JWT via `djangorestframework-simplejwt` |
| Config | `python-decouple` (`.env`-based, no hardcoded values) |
| Testing | `pytest-django`, `factory-boy`, `fakeredis` |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Angular 17 |
| Language | TypeScript 5.4 |
| Styling | SCSS |
| HTTP Client | Angular HttpClient + RxJS |
| Routing | Angular Router (lazy-loaded components) |
| Build | Angular CLI / Webpack |
| Container | Nginx (production static serving) |

---

## 📦 Microservices

### Auth Service

**Purpose**: Central identity provider for the entire platform.

**Responsibilities**:
- User registration and login
- JWT access token issuance (5-minute lifetime) and refresh token management (7-day lifetime)
- Token verification endpoint for Traefik ForwardAuth middleware
- User profile retrieval
- Profile image management via Django Admin + MinIO/S3

**Database**: PostgreSQL 16

**Kafka Role**: Producer — publishes `user.registered` on successful registration

**Key Design Decisions**:
- All other services trust the `X-User-Id` / `X-Username` headers injected by Traefik. No service other than auth issues or validates JWTs.
- Profile images are admin-only uploads; users pick from pre-existing images at registration.
- Debezium CDC also monitors the `users` table as a fallback event source.

**Domain Model**:
```
UserEntity
  id            : UUID
  username      : str (unique)
  email         : str (unique)
  password_hash : str (bcrypt via Django make_password)
  created_at    : datetime
  updated_at    : datetime
  profile_image : ProfileImageEntity | None

ProfileImageEntity
  id        : UUID
  image_url : str  (S3 key resolved via django-storages)
```

**Database Schema**:
```sql
CREATE TABLE profile_images (
    id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image TEXT NOT NULL
);

CREATE TABLE users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username   VARCHAR(150) UNIQUE NOT NULL,
    email      VARCHAR(254) UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    profile_id UUID REFERENCES profile_images(id) ON DELETE SET NULL,
    is_active  BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### Level Service

**Purpose**: Manages all typing level content and records user attempts.

**Responsibilities**:
- Listing and paginating available levels
- Returning individual level details
- Accepting typed submissions and scoring them
- Publishing reward events to Kafka when a submission earns credits

**Database**: PostgreSQL 16

**Kafka Role**: Producer — publishes `submit.rewarded` when `rewarded_credits > 0`

**Level Types**:
- `default` — standard paragraph typing (20 seed levels)
- `cat_running` — cat-themed typing exercises (10 seed levels)

**Reward Calculation**:
```
rewarded_credits = floor( min(1.0, user_wpm / goal_wpm) * level_cost )
```
- If `user_wpm >= goal_wpm` → full `level_cost` awarded
- If `user_wpm < goal_wpm` → proportional fraction of `level_cost`
- If user has **already submitted this level** → `rewarded_credits = 0` (anti-farming)

**Domain Model**:
```
LevelEntity
  id         : UUID
  text       : str        — the passage the user types
  cost       : int        — maximum credits this level can award
  goal_wpm   : int        — target words-per-minute
  level_type : str        — "default" | "cat_running"
  created_at : datetime
  updated_at : datetime

SubmitEntity
  id               : UUID
  level_id         : UUID
  user_id          : UUID  — cross-service reference (not a DB FK)
  wpm              : int
  rewarded_credits : int   — computed and stored after calculation
  created_at       : datetime
```

---

### Balance Service

**Purpose**: Acts as each user's credit wallet.

**Responsibilities**:
- Creating a zero-balance wallet when a new user registers (via Kafka)
- Crediting rewards when a submission is rewarded (via Kafka)
- Serving a user's current balance over HTTP
- Serving paginated transaction history over HTTP

**Database**: PostgreSQL 16

**Kafka Role**: Consumer — listens to `user.registered` and `submit.rewarded`

**Key Design Decisions**:
- **No HTTP write endpoints** — all balance mutations arrive exclusively via Kafka. This prevents accidental or malicious balance manipulation.
- **Atomic balance updates** — uses Django ORM `F()` expressions to translate to a single SQL `UPDATE balance = balance + N`. No read-then-write race condition.
- **Idempotency** — `event_id` has a `UNIQUE` constraint in the DB. Duplicate Kafka messages are caught at the `IntegrityError` level and committed without reprocessing.

**Domain Model**:
```
BalanceEntity
  id         : UUID
  user_id    : UUID  (UNIQUE)
  balance    : int   — always >= 0, never negative
  updated_at : datetime

TransactionEntity
  id         : UUID
  event_id   : UUID  — idempotency key from Kafka message
  balance_id : UUID
  amount     : int   — always positive
  type       : "CREDIT" | "DEBIT"
  created_at : datetime
```

**Consumer Logic**:
1. Poll Kafka for messages
2. Deserialize JSON payload and route by `event` field
3. If use case succeeds → commit Kafka offset
4. If `IntegrityError` on duplicate `event_id` → log INFO, commit offset (idempotent skip)
5. Any other exception → log ERROR, do NOT commit (message retried)

---

### Leaderboard Service

**Purpose**: Maintains a real-time daily leaderboard of users ranked by credits earned today.

**Responsibilities**:
- Consuming `submit.rewarded` events and updating Redis ZSET scores
- Serving top-N users and the requesting user's rank in a single response
- Atomically resetting the leaderboard at midnight UTC, archiving the previous day

**Database**: Redis 7 only (no PostgreSQL — Redis is the source of truth)

**Kafka Role**: Consumer — listens to `submit.rewarded`

**Redis Data Structure**:
```redis
# Active leaderboard key
leaderboard:daily   (ZSET: member=user_id, score=cumulative_credits_today)

# Increment on each reward event
ZINCRBY leaderboard:daily 80 "550e8400-e29b-41d4-a716-446655440000"

# Get top 10 (descending)
ZREVRANGE leaderboard:daily 0 9 WITHSCORES

# Get user's rank (0-based, descending)
ZREVRANK leaderboard:daily "550e8400-e29b-41d4-a716-446655440000"

# Idempotency dedup set
SADD processed_events:daily "<event_id>"
EXPIRE processed_events:daily 86400
```

**Daily Reset Strategy** (atomic, zero-downtime):
```python
pipe = redis.pipeline()
pipe.rename("leaderboard:daily", f"leaderboard:archive:{today}")
pipe.expire(f"leaderboard:archive:{today}", 60 * 60 * 24 * 7)  # 7-day archive
pipe.execute()
```
`RENAME` is atomic — there is never a window where the leaderboard is empty. After rename, the next `ZINCRBY` creates a fresh `leaderboard:daily` automatically.

---

## 🖥️ Frontend

Built with **Angular 17** using standalone components and lazy loading.

### Pages & Routes

| Route | Component | Auth Required |
|---|---|---|
| `/` | Redirects to `/dashboard` | — |
| `/login` | `LoginComponent` | No |
| `/register` | `RegisterComponent` | No |
| `/dashboard` | `DashboardComponent` | ✅ Yes |
| `/leaderboard` | `LeaderboardComponent` | No |
| `/play/:id` | `GamePlayComponent` | ✅ Yes |

### Core Modules

- **`guards/`** — `authGuard` to protect routes requiring login
- **`interceptors/`** — HTTP interceptor for attaching JWT tokens to outbound requests
- **`services/`** — `AuthService` (login, register, token management), `GameService` (level data and submit)
- **`models/`** — TypeScript interfaces for API response shapes
- **`utils/`** — Shared utility functions

### Features

- **auth/** — Login and registration forms
- **dashboard/** — Level catalog with pagination
- **game/** — Interactive typing game view with WPM tracking
- **leaderboard/** — Real-time leaderboard display

### Frontend Configuration

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/          # Guards, interceptors, services, models, utils
│   │   └── features/      # auth, dashboard, game, leaderboard
│   ├── environments/      # environment.ts / environment.prod.ts
│   ├── styles.scss        # Global styles
│   └── index.html
├── nginx.conf             # Production Nginx config (reverse proxy to backend)
├── Dockerfile             # Multi-stage: build → nginx serve
└── angular.json
```

---

## 🏛️ Infrastructure

All services run as Docker containers orchestrated by Docker Compose with modular fragment files.

### Compose Structure

```
backend/
├── docker-compose.yml          # Root: includes all fragments
└── compose/
    ├── networks-volumes.yml    # Network and volume definitions
    ├── proxy.yml               # Traefik reverse proxy
    ├── infrastructure.yml      # Databases, Kafka, MinIO, monitoring stack
    └── services.yml            # Application microservices
```

### Infrastructure Services

| Container | Image | Purpose |
|---|---|---|
| `traefik` | traefik:v2 | Reverse proxy, ForwardAuth, TLS termination |
| `postgres_auth` | postgres:16-alpine | Auth service database |
| `postgres_level` | postgres:16-alpine | Level service database |
| `postgres_balance` | postgres:16-alpine | Balance service database |
| `redis` | redis:7-alpine | Leaderboard ZSET store |
| `zookeeper` | confluentinc/cp-zookeeper:7.6.0 | Kafka coordination |
| `kafka` | confluentinc/cp-kafka:7.6.0 | Event bus |
| `kafka-init` | cp-kafka | Topic initialization script |
| `debezium` | debezium/connect:2.6 | CDC from PostgreSQL to Kafka |
| `minio` | minio/minio | S3-compatible object storage for profile images |
| `minio-init` | minio/mc | Bucket initialization |
| `kafka-ui` | provectuslabs/kafka-ui | Kafka topic inspection UI |
| `dockadmin` | demlabz/dockadmin | Lightweight Docker container manager |

### Admin Interface URLs

| URL | Tool |
|---|---|
| `http://localhost:8000/admin/traefik/` | Traefik dashboard |
| `http://localhost:8000/admin/kafka/` | Kafka UI (topic inspection, consumer groups) |
| `http://localhost:8000/admin/minio/` | MinIO Console (object storage) |
| `http://localhost:8000/admin/grafana/` | Grafana (metrics, logs, traces) |
| `http://localhost:8000/admin/docker/` | Dockadmin (container management) |
| `http://localhost:8000/auth/admin/` | Django Admin — Users & Profiles |
| `http://localhost:8000/level/admin/` | Django Admin — Levels & Submits |
| `http://localhost:8000/balance/admin/` | Django Admin — Balances & Transactions |
| `http://localhost:8000/leaderboard/admin/` | Django Admin — Leaderboard state |

---

## 📊 Observability

A full-spectrum monitoring stack is included out of the box.

| Tool | Role |
|---|---|
| **Prometheus** | Scrapes metrics from all services via `django-prometheus`. 15-day retention. |
| **Loki** | Aggregates container logs from all services |
| **Promtail** | Log shipping agent (reads Docker container logs) |
| **Tempo** | Distributed request tracing |
| **Grafana** | Unified visualization dashboard for metrics, logs, and traces |
| **redis-exporter** | Exports Redis metrics to Prometheus |
| **kafka-exporter** | Exports Kafka metrics to Prometheus |
| **postgres-exporter** × 3 | Exports PostgreSQL metrics (one per service DB) |

All tools are accessible through the Grafana dashboard at `/admin/grafana`.

---

## 📡 API Reference

All routes are prefixed via Traefik. Protected routes require `Authorization: Bearer <access_token>`.

### Auth & Identity (`/auth`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/registration` | No | Register a new account |
| `POST` | `/auth/login` | No | Exchange credentials for JWT pair |
| `POST` | `/auth/refresh` | No | Refresh an expired access token |
| `GET` | `/auth/users/{user_id}` | ✅ | Retrieve user profile |
| `GET` | `/auth/verify` | Internal | ForwardAuth endpoint used by Traefik only |

**Login Request/Response**:
```json
// POST /auth/login
{ "login": "username_or_email", "password": "plaintextpassword" }

// 200 OK
{ "user_id": "uuid", "access_token": "eyJ...", "refresh_token": "eyJ..." }
```

**Registration Request/Response**:
```json
// POST /auth/registration
{ "username": "alice", "email": "alice@example.com", "password": "min8chars", "profile_image": "uuid-or-null" }

// 201 Created — returns full user object without password
```

---

### Typing & Levels (`/level`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/level?start=N&limit=M` | ✅ | List levels with pagination |
| `GET` | `/level/{uuid}` | ✅ | Get a specific level's content |
| `POST` | `/level` | ✅ | Submit a typing attempt |

**Submit Request/Response**:
```json
// POST /level
{ "level_id": "uuid", "wpm": 72 }

// 201 Created
{ "id": "uuid", "level_id": "uuid", "user_id": "uuid", "wpm": 72, "rewarded_credits": 100, "created_at": "..." }
```

---

### Economy (`/balance`, `/transactions`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/balance/{user_id}` | ✅ | Get current credit balance |
| `GET` | `/transactions/{user_id}?start=N&limit=M` | ✅ | Get paginated transaction history |

---

### Social (`/leaderboard`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/leaderboard` | ✅ | Get top 10 + requesting user's rank |

**Response**:
```json
{
  "top": [
    { "place": 1, "user_id": "uuid", "score": 840 },
    { "place": 2, "user_id": "uuid", "score": 720 }
  ],
  "user_place": 14
}
```
`user_place` is `null` if the requesting user has no score today.

---

## ⚡ Event-Driven Architecture

### Core Kafka Events

#### `user.registered`
- **Producer**: `auth_service` (also captured by Debezium CDC as a fallback)
- **Consumer**: `balance_service` — creates an empty wallet with `balance = 0`

```json
{ "event": "user.registered", "user_id": "uuid", "username": "alice" }
```

#### `submit.rewarded`
- **Producer**: `level_service` — published only when `rewarded_credits > 0`
- **Consumers**: `balance_service` (credits the wallet) + `leaderboard_service` (updates ranking)

```json
{
  "event": "submit.rewarded",
  "event_id": "submit-uuid",
  "user_id": "uuid",
  "username": "alice",
  "amount": 80
}
```

### Idempotency Guarantees

| Service | Event | Strategy |
|---|---|---|
| `balance_service` | `user.registered` | `UNIQUE(user_id)` on balances table — skip if exists |
| `balance_service` | `submit.rewarded` | `UNIQUE(event_id)` on transactions — catch `IntegrityError`, commit offset |
| `leaderboard_service` | `submit.rewarded` | Redis `SET processed_events:daily` — `SISMEMBER` check before `ZINCRBY` |

### Debezium CDC

Debezium monitors the `users` table in `postgres_auth` via PostgreSQL logical replication (pgoutput plugin). Every `INSERT` produces an event on the `dbz.public.users` topic, giving balance service a secondary reliable source for wallet initialization.

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose v2
- (For local frontend dev) Node.js 18+ and Angular CLI 17

### 1. Clone & Configure

```bash
git clone <repository-url>
cd WebDev26Project

# Copy and fill in root env
cp .env.example .env
# Copy and fill in backend env
cp backend/.env.example backend/.env
# Copy env for each service
cp backend/auth_service/.env.example backend/auth_service/.env
cp backend/level_service/.env.example backend/level_service/.env
```

### 2. Start the Full Stack

```bash
cd backend
docker compose up -d
```

### 3. Apply Migrations

```bash
docker compose exec auth_service python manage.py migrate
docker compose exec level_service python manage.py migrate
docker compose exec balance_service python manage.py migrate
# leaderboard_service has no DB migrations
```

### 4. Register Debezium Connector

Run once after `postgres_auth` and `debezium` containers are healthy:

```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "users-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres_auth",
      "database.port": "5432",
      "database.user": "auth_user",
      "database.password": "auth_pass",
      "database.dbname": "auth_db",
      "database.server.name": "auth",
      "table.include.list": "public.users",
      "topic.prefix": "dbz",
      "plugin.name": "pgoutput"
    }
  }'
```

### 5. Verify Health

Open `http://localhost:8000/admin/traefik/` — all services should appear healthy.

### 6. Run Frontend (Development)

```bash
cd frontend
npm install
npm start
# App available at http://localhost:4200
```

---

## 🔧 Environment Variables

### Root `.env`

```env
POSTGRES_DB=typecat
POSTGRES_USER=typecat_user
POSTGRES_PASSWORD=typecat_secret
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_DEBUG=True
CORS_ALLOWED_ORIGINS=http://localhost:4200
```

### Auth Service

```env
DJANGO_ENV=development
SECRET_KEY=
ALLOWED_HOSTS=*
POSTGRES_DB=auth_db
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=
POSTGRES_HOST=postgres_auth
POSTGRES_PORT=5432
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
```

### Level Service

```env
DJANGO_ENV=development
SECRET_KEY=
ALLOWED_HOSTS=*
POSTGRES_DB=level_db
POSTGRES_USER=level_user
POSTGRES_PASSWORD=
POSTGRES_HOST=postgres_level
POSTGRES_PORT=5432
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Balance Service

```env
DJANGO_ENV=development
SECRET_KEY=
ALLOWED_HOSTS=*
POSTGRES_DB=balance_db
POSTGRES_USER=balance_user
POSTGRES_PASSWORD=
POSTGRES_HOST=postgres_balance
POSTGRES_PORT=5432
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_GROUP_ID=balance-service
KAFKA_TOPIC_USER_REGISTERED=user.registered
KAFKA_TOPIC_SUBMIT_REWARDED=submit.rewarded
```

### Leaderboard Service

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

---

## 👨‍💻 Development Guide

### Code Architecture (all backend services)

Every backend service follows **Domain-Driven Design (DDD)** layering:

```
src/
└── <app>/
    ├── domain/           # Pure Python entities (frozen dataclasses), abstract repositories
    ├── application/      # DTOs, use cases, application-level exceptions
    ├── infrastructure/   # Django models, ORM repositories, Kafka producers/consumers
    └── presentation/     # DRF views, serializers, URL routing, exception handler
```

**Rules**:
- Inner layers never import from outer layers (`domain` ← `application` ← `infrastructure` ← `presentation`)
- Use cases depend on abstract repositories (dependency inversion), not ORM models
- Views do exactly three things: validate input, call use case, serialize output

### Running Tests

```bash
# Auth service
cd backend/auth_service
pytest src/users/tests/ -v

# Level service
cd backend/level_service
pytest src/levels/tests/ -v

# Balance service
cd backend/balance_service
pytest src/balances/tests/ -v

# Leaderboard service (uses fakeredis, no real Redis needed)
cd backend/leaderboard_service
pytest src/leaderboard/tests/ -v
```

### Adding a New Microservice

1. Initialize a new Django service using the DDD pattern (`domain/`, `application/`, `infrastructure/`, `presentation/`)
2. Add a new `.yml` fragment in `backend/compose/` or extend `compose/services.yml`
3. Configure Traefik routing labels on the service container
4. If auth is required, add the `auth-verify@file` middleware label
5. Use `KafkaEventConsumer` or `SubmitEventProducer` patterns for Kafka integration

### Token Mechanics

| Token | Lifetime | Storage Recommendation |
|---|---|---|
| Access token | 5 minutes | Memory (JS variable), do not persist |
| Refresh token | 7 days | HttpOnly cookie or secure storage |

---

## 📁 Project Structure

```
WebDev26Project/
├── .env                          # Root environment variables
├── .env.example                  # Template for environment setup
├── .gitignore
├── LICENSE
├── README.md                     # ← You are here
│
├── backend/
│   ├── docker-compose.yml        # Main compose entry point (includes fragments)
│   ├── .env                      # Backend-level environment variables
│   ├── overview.md               # Architecture overview with Mermaid diagrams
│   │
│   ├── compose/
│   │   ├── networks-volumes.yml  # Shared Docker networks and volumes
│   │   ├── proxy.yml             # Traefik proxy definition
│   │   ├── infrastructure.yml    # Databases, Kafka, MinIO, monitoring
│   │   └── services.yml          # Application microservices
│   │
│   ├── traefik/                  # Traefik static + dynamic config
│   ├── monitoring/               # Prometheus, Loki, Promtail, Tempo, Grafana configs
│   ├── scripts/                  # init-kafka-topics.sh and helpers
│   │
│   ├── auth_service/             # Identity & JWT service
│   ├── level_service/            # Typing levels & scoring service
│   ├── balance_service/          # Credit wallet service
│   └── leaderboard_service/      # Daily ranking service (Redis-based)
│
└── frontend/
    ├── Dockerfile                # Multi-stage Angular build + Nginx
    ├── nginx.conf                # Production reverse proxy config
    ├── angular.json
    ├── package.json
    └── src/
        ├── app/
        │   ├── core/             # Guards, interceptors, services, models, utils
        │   └── features/         # auth, dashboard, game, leaderboard pages
        ├── environments/
        ├── styles.scss
        └── index.html
```

---

## 📄 License

This project is licensed under the terms in the [LICENSE](./LICENSE) file.
