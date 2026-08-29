# TestFlow — Architecture

## Overview

TestFlow is a monorepo containing three independent applications that together form a complete test management system and its automation framework.

```
testflow/
├── frontend/     React SPA
├── backend/      FastAPI REST API
├── automation/   Playwright test framework
└── docs/         Documentation
```

---

## Backend Architecture

### Request Flow

```
HTTP Request
  → FastAPI Router (thin — routing only)
  → Authentication middleware (JWT validation)
  → Authorization check (role enforcement)
  → Pydantic schema validation
  → Service layer (business logic)
  → Repository layer (database queries)
  → SQLAlchemy ORM
  → MySQL
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| Router | `app/api/` | HTTP routing, request/response mapping |
| Schema | `app/schemas/` | Input validation, output serialization |
| Service | `app/services/` | Business rules, orchestration |
| Repository | `app/repositories/` | All database access |
| Model | `app/models/` | SQLAlchemy ORM table definitions |
| Core | `app/core/` | Config, JWT, password hashing |
| Dependencies | `app/dependencies/` | FastAPI dependency injection (current user, role guards) |

---

## Frontend Architecture

React SPA communicating with the backend via REST API.

### Key Patterns

- Route-level code splitting via React Router
- Authenticated routes redirect unauthenticated users to `/login`
- Role-based UI visibility (supplemental to backend authorization)
- Centralized API client in `services/`
- Custom hooks abstract data fetching logic from page components

---

## Database Design

MySQL 8.0 with SQLAlchemy 2.0 ORM and Alembic migrations.

### SQLAlchemy Configuration

- Engine created in `app/core/database.py` with `pool_pre_ping=True` (validates connections before use) and `pool_recycle=3600`
- `SessionLocal` is a `sessionmaker` bound to the engine
- `Base` is a `DeclarativeBase` subclass — all ORM models inherit from it
- `get_db()` in `app/dependencies/db.py` yields a session per request and closes it in a `finally` block
- `check_database_connection()` executes `SELECT 1` and returns `bool` — never raises, never fakes success

### Alembic

- Initialized at `backend/migrations/`
- `migrations/env.py` reads `DATABASE_URL` from `app.core.config.settings` — no credentials in `alembic.ini`
- `target_metadata = Base.metadata` enables autogenerate support for future model migrations
- Run migrations: `alembic upgrade head`
- Generate a new migration: `alembic revision --autogenerate -m "description"`

### Health Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness — confirms the process is running |
| `GET /health/db` | Readiness — executes `SELECT 1` against MySQL, returns 503 if unreachable |

### Docker Database Connectivity

Inside Docker Compose, the backend uses the MySQL service name as the hostname:

```
DATABASE_URL=mysql+pymysql://testflow:testflow@mysql:3306/testflow
```

This is set automatically in `docker-compose.yml`. Local development uses `localhost:3306`.

### Entity Relationships

```
User ──< ProjectMember >── Project
Project ──< TestSuite ──< TestCase
Project ──< TestRun ──< TestResult >── TestCase
Project ──< Defect >── TestCase (optional)
Defect >── User (assigned_to, optional)
```

---

## Authentication

- JWT Bearer tokens
- Passwords hashed with bcrypt
- Token expiry configurable via environment variable
- Inactive users rejected at login
- All protected endpoints validate token on every request

---

## Authorization

Three roles enforced at the API layer:

| Role | Level |
|---|---|
| ADMIN | Full CRUD on all resources including users |
| QA_ENGINEER | CRUD on projects, suites, cases, runs, results, defects |
| VIEWER | Read-only on all resources |

Role checks are implemented as FastAPI dependencies injected into route handlers.

---

## Automation Architecture

```
Playwright Test Runner
  → Fixtures (auth state, API clients, test data)
  → Page Objects (locators + actions)
  → API Clients (typed wrappers around APIRequestContext)
  → Tests (business behavior assertions)
```

### Key Patterns

- Authentication state stored per role, reused across tests
- API clients used for test setup/teardown to keep tests fast
- Page Objects expose actions, not implementation details
- Tests are isolated — no shared mutable state between specs
