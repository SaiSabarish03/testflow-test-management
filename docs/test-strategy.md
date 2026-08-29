# TestFlow — Test Strategy

## Scope

The Playwright automation framework tests the TestFlow application across three layers:

- **UI** — end-to-end browser tests via Page Object Model
- **API** — REST API contract and behavior tests
- **Integration** — cross-layer state consistency

---

## Test Suites

| Suite | Tag | Focus |
|---|---|---|
| Smoke | `@smoke` | Critical path — login, dashboard, core navigation |
| Functional | `@functional` | Feature workflows — CRUD operations |
| Regression | `@regression` | Full business rule coverage |
| Negative | `@negative` | Validation, error handling, edge cases |
| RBAC | `@rbac` | Role-based access control enforcement |
| API | `@api` | REST API contracts, status codes, response bodies |
| Integration | `@integration` | UI action → API state, API setup → UI verification |

---

## Test Isolation Strategy

- Each test creates its own data via API before running
- Unique values (timestamps, UUIDs) prevent collisions in parallel runs
- Cleanup runs after each test where persistent data was created
- No test depends on execution order
- No test relies on seed data records by ID

---

## Authentication in Tests

- Playwright `storageState` saves authenticated sessions per role
- Sessions are created once per worker via global setup
- Tests receive pre-authenticated browser contexts via fixtures
- API tests use bearer tokens obtained via the auth API

---

## Locator Strategy

Priority order:
1. `getByRole` — semantic, accessible
2. `getByLabel` — form fields
3. `getByPlaceholder` — inputs without labels
4. `getByText` — visible text where stable
5. `data-testid` — last resort for complex components

---

## Synchronization

- No `waitForTimeout()` — all waits are condition-based
- Playwright auto-waiting handles most cases
- Explicit `expect(locator).toBeVisible()` for dynamic content
- `waitForURL` after navigation
- `waitForResponse` for API-triggered state changes

---

## Browsers

| Browser | Engine |
|---|---|
| Chromium | Blink |
| Firefox | Gecko |
| WebKit | WebKit |

All three run in CI. Local development defaults to Chromium.

---

## Parallel Execution

- Workers: configurable, default 2 in CI
- Tests are designed for full parallelism
- Isolated data per test prevents race conditions

---

## Reporting

- HTML report with test timeline and screenshots
- Screenshot captured on every failure
- Trace captured on first retry and failure
- Video available for debugging (off by default in CI)
