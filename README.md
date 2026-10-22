# TestFlow — Test Management System

A realistic web-based Test Management System built as a full-stack portfolio project for QA Automation Engineer / SDET interviews.

TestFlow serves a dual purpose:
- A functional **System Under Test (SUT)** with real business workflows
- A showcase for a professional **Playwright + TypeScript automation framework**

---

## Project Overview

TestFlow allows QA teams to manage the full testing lifecycle:

- Authenticate and manage users with role-based access
- Organize work into Projects
- Define Test Suites and Test Cases
- Create and execute Test Runs
- Record pass/fail/blocked results
- Track Defects from discovery to resolution

---

## Architecture

```
testflow/
├── frontend/        React + TypeScript + Vite + Ant Design
├── backend/         Python + FastAPI + SQLAlchemy + MySQL
├── automation/      Playwright + TypeScript
├── docs/            Architecture and API documentation
├── .github/         GitHub Actions CI/CD
├── docker-compose.yml
└── README.md
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Ant Design, React Router |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 |
| Database | MySQL 8.0 |
| Auth | JWT (python-jose), bcrypt |
| Automation | Playwright, TypeScript, Playwright Test |
| CI/CD | GitHub Actions |
| Local Env | Docker, Docker Compose |

---

## User Roles

| Role | Permissions |
|---|---|
| ADMIN | Full access to all resources including user management |
| QA_ENGINEER | Create/read/update projects, suites, cases, runs, results, defects |
| VIEWER | Read-only access to all resources |

Authorization is enforced by the backend API on every request.

---

## Quick Start (Docker)

### Prerequisites

- Docker Desktop
- Git

### Steps

```bash
git clone https://github.com/SaiSabarish03/testflow-test-management.git
cd testflow
cp .env.example .env
docker compose up --build
```

Services will be available at:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MySQL: localhost:3306

---

## Manual Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit DATABASE_URL and JWT_SECRET_KEY
alembic upgrade head
python seed/seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env             # edit VITE_API_URL if needed
npm run dev
```

---

## Seed Data

The seed script creates the following development accounts:

| Name | Email | Password | Role |
|---|---|---|---|
| Admin User | admin@testflow.local | Admin123! | ADMIN |
| QA Engineer | qa@testflow.local | QaPass123! | QA_ENGINEER |
| Viewer User | viewer@testflow.local | View123! | VIEWER |

Seed data also includes sample projects, test suites, test cases, test runs, and defects.

**These credentials are for local development only. Never use in production.**

---

## Running Playwright Tests

Use a dedicated test database for Playwright. The UI and API workflows create application records; do not point them at production or a shared database.

Before running the full suite, verify the backend's effective `DATABASE_URL` points to an isolated disposable database and confirm `/health/db` succeeds against that target. Do not rely only on changing `automation/.env`: Playwright connects to an already-running backend, whose process may have loaded a different database URL. Backend pytest uses in-memory SQLite fixtures and does not require the populated MySQL database.

### Prerequisites

```bash
cd automation
npm ci
npx playwright install chromium firefox webkit
cp .env.example .env   # set FRONTEND_URL, API_URL, and test credentials
```

### Run all tests

```bash
npx playwright test
```

### Run by suite

```bash
npm run test:auth
npm run test:projects
npm run test:suites
npm run test:cases
npm run test:runs
npm run test:defects
npm run test:users
npm run test:rbac
npm run test:api
```

### Run by browser

```bash
npm run test:chromium
npx playwright test --project=firefox-noauth
npx playwright test --project=webkit-noauth
```

The Chromium command runs `chromium-noauth`, `chromium-admin`, and `chromium-rbac`. Firefox and WebKit currently run authentication and route-protection smoke tests only.

### Run API tests only

```bash
npm run test:api
```

### HTML Report

```bash
npm run report
```

### Trace Viewer

```bash
npx playwright show-trace test-results/<test>/trace.zip
```

---

## CI/CD

GitHub Actions workflow: [.github/workflows/playwright.yml](.github/workflows/playwright.yml)

The pipeline:
1. Starts the full application stack
2. Waits for readiness
3. Runs all Playwright tests
4. Uploads HTML report as artifact
5. Fails the build on test failures

---

## Test Strategy

See [docs/test-strategy.md](docs/test-strategy.md) for the actual test projects, commands, isolation guidance, browser scope, and report configuration.
## Design Decisions

- Backend authorization is the source of truth; frontend role-gating is supplemental
- Repository pattern separates database access from business logic
- Playwright fixtures handle authentication state to avoid repetitive login
- API setup/teardown is preferred over UI setup for test isolation
- Seed data is deterministic and documented for predictable automation

---

## Known Limitations

- Project-level member authorization uses a simplified model in v1
- No real-time updates (no WebSocket)
- Email notifications are not implemented
- The current full Playwright report is from a prior 67-instance run; see [the execution summary](docs/test-execution-summary.md) for current focused results and the database safety blocker.

---

## Future Improvements

- Project-level role assignments
- Test case import/export (CSV, XML)
- Metrics and trend charts
- Email notifications
- Audit log

---

## Repository Structure

```
testflow/
  frontend/src/        React pages, components, API clients, routes, hooks, types
  backend/app/         FastAPI routes, models, schemas, services, repositories
  backend/migrations/  Alembic migrations
  backend/seed/        Development seed data
  backend/tests/       Pytest unit and API tests
  automation/tests/    Playwright UI and API scenarios
  automation/pages/    Page Object Model classes
  automation/fixtures/ Shared Playwright fixtures
  automation/test-data/Unique test data generators
  automation/helpers/  Automation helpers
  automation/config/   Auth state and setup
  docs/                Architecture, API, test, database, defect, and assessment docs
```
