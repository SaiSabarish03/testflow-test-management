# TestFlow Test Strategy

## Scope

Playwright TypeScript covers browser UI workflows and REST API requests. Backend pytest tests exercise endpoint and service behavior. The project includes UI/API workflows but does not currently verify full UI/API/MySQL reconciliation.

## Available Playwright commands

Run these commands from `automation/`. The specs do not currently use grep tags.

| Command | Scope |
|---|---|
| `npm run test:auth` | Authentication UI scenarios |
| `npm run test:projects` | Project UI scenarios |
| `npm run test:suites` | Test-suite UI scenarios |
| `npm run test:cases` | Test-case UI scenarios |
| `npm run test:runs` | Test-run UI scenarios |
| `npm run test:defects` | Defect UI scenarios |
| `npm run test:users` | User-management UI scenarios |
| `npm run test:rbac` | UI role-based access checks |
| `npm run test:api` | Playwright API scenarios |
| `npm run test:chromium` | Chromium no-auth, admin, and RBAC projects |
| `npx playwright test --project=firefox-noauth` | Firefox auth/route smoke cases |
| `npx playwright test --project=webkit-noauth` | WebKit auth/route smoke cases |

Firefox and WebKit currently have smoke coverage only; they are not full UI regression runs. `npm test` runs all configured projects.

## Test isolation and data

- UI scenarios create project-related records using timestamp-based generators.
- API scenarios use unique values and include cleanup for records where applicable.
- A test workflow may create related run/result records. Use a disposable, dedicated test database rather than production or a shared populated database.
- Playwright is configured with one worker. Parallel mutation is not the documented execution mode.
- Authentication setup and API tests use seeded accounts or matching values from `automation/.env`.

## Authentication

- `auth.setup.ts` logs in as Admin, QA, and Viewer and saves ignored `.auth/` storage-state files.
- UI specs use authenticated projects/contexts where configured.
- API specs obtain bearer tokens from the authentication endpoint.

## Locator and synchronization strategy

Prefer semantic locators in this order:

1. `getByRole`
2. `getByLabel`
3. `getByPlaceholder`
4. `getByText` where text is stable
5. `data-testid` where needed for complex components

Use Playwright auto-waiting and explicit assertions/URL waits for asynchronous UI state. Avoid fixed sleeps.

## Reporting and artifacts

- HTML reporter writes `automation/playwright-report/`; run `npm run report` from `automation/` to open it.
- Screenshots use `only-on-failure`.
- Traces use `retain-on-failure`.
- A passing run normally has no failure screenshots or traces. The HTML report is a local output; package it separately for an evaluator.
- Videos are disabled.

## Coverage limitations

- No dedicated logout or broad boundary suite existed in the original test inventory; a focused logout and page-size boundary check has since been added and run.
- The page-size API assertion uses a 2,000 ms threshold in a local test environment; it is not a production service-level objective.
- UI/API/database create-update-delete reconciliation remains outstanding.
