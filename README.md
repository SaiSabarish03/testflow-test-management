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
git clone <repo-url>
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
cp .env.example .env             # edit DATABASE_URL and SECRET_KEY
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
| Admin User | admin@testflow.dev | Admin123! | ADMIN |
| QA Engineer | qa@testflow.dev | QaPass123! | QA_ENGINEER |
| Viewer User | viewer@testflow.dev | View123! | VIEWER |

Seed data also includes sample projects, test suites, test cases, test runs, and defects.

**These credentials are for local development only. Never use in production.**

---

## Running Playwright Tests

### Prerequisites

```bash
cd automation
npm install
npx playwright install
cp .env.example .env   # set FRONTEND_URL and API_URL
```

### Run all tests

```bash
npx playwright test
```

### Run by suite tag

```bash
npx playwright test --grep @smoke
npx playwright test --grep @auth
npx playwright test --grep @projects
npx playwright test --grep @rbac
npx playwright test --grep @api
```

### Run by browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run in parallel

```bash
npx playwright test --workers=4
```

### Run API tests only

```bash
npx playwright test tests/api/
```

### HTML Report

```bash
npx playwright show-report
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

See [docs/test-strategy.md](docs/test-strategy.md) for the full test strategy.

Suites:
- **Smoke** — critical path verification
- **Functional** — feature-level workflows
- **Regression** — full coverage of business rules
- **Negative** — validation and error handling
- **RBAC** — role-based access control
- **API** — REST API contract and behavior
- **Integration** — UI/API state consistency

---

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
├── frontend/
│   └── src/
│       ├── components/     Reusable UI components
│       ├── pages/          Route-level page components
│       ├── layouts/        App shell and layout wrappers
│       ├── services/       API client functions
│       ├── hooks/          Custom React hooks
│       ├── routes/         Route definitions and guards
│       ├── types/          TypeScript interfaces
│       ├── utils/          Utility functions
│       └── constants/      App-wide constants
│
├── backend/
│   └── app/
│       ├── api/            FastAPI routers
│       ├── models/         SQLAlchemy ORM models
│       ├── schemas/        Pydantic request/response schemas
│       ├── services/       Business logic
│       ├── repositories/   Database access layer
│       ├── core/           Config, security, JWT
│       └── dependencies/   FastAPI dependency injection
│   ├── migrations/         Alembic migrations
│   ├── seed/               Seed data scripts
│   └── tests/              Backend unit/integration tests
│
├── automation/
│   ├── tests/              Playwright test specs
│   ├── pages/              Page Object Model classes
│   ├── fixtures/           Playwright fixtures
│   ├── api/                API client classes
│   ├── test-data/          Test data constants
│   ├── utils/              Automation utilities
│   └── config/             Environment configuration
│
└── docs/
    ├── architecture.md
    ├── api.md
    └── test-strategy.md
```
