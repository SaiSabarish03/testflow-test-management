# TestFlow Defect Report — ICSR SDET Assignment

**Review/build baseline:** source commit `abe32fe` and docs-only follow-up `5535601`; the remediation is present in pushed commit `e41c5b6`.
**Review date:** 22 October 2026
**Environment:** Windows local review; TestFlow local app; README/config source inspection and focused Playwright tests
**Scope:** Full Playwright report (67 configured instances) plus current focused logout and API checks. This report covers confirmed documentation/configuration defects. No application behavior defect was observed in the passing test scope. This is not a claim that the application is defect-free.

## Summary

| Severity | Confirmed | Fixed in working tree | Open |
|---|---:|---:|---:|
| Critical | 0 | 0 | 0 |
| High | 0 | 0 | 0 |
| Medium | 4 | 4 | 0 |
| Low | 1 | 1 | 0 |
| **Total** | **5** | **5** | **0** |

| Status | Count |
|---|---:|
| Fixed in commit `e41c5b6`; static retest passed | 5 |
| Open product defects | 0 |
| Unverified product findings | 0 |

Severity describes user/evaluator impact: High means a core workflow cannot be completed; Medium means a documented setup or verification command is misleading or fails; Low means the discrepancy is limited to test-planning claims. Priority describes fix order before submission: P1 blocks setup or test execution; P2 is a consistency correction.

These defects were confirmed by comparing repository files and command discovery. They are documentation/configuration defects, not failures reproduced in TestFlow product behavior. Their original reproduction observed mismatches in the committed `5535601` content; remediation is present in commit `e41c5b6` and was statically checked. A clean-checkout setup was not repeated after edits.

## Confirmed findings

### DOC-001 — Seed account emails in README do not match the seed script

- **Module:** Setup documentation / seeded test accounts
- **Preconditions:** Repository at `5535601`; inspect the README and seed script.
- **Reproduction:** Read the Seed Data table in `README.md`; compare the email domains with `backend/seed/seed.py`.
- **Expected:** README account emails match the accounts created by the seed script.
- **Actual:** README listed `@testflow.dev`; the seed script creates `@testflow.local`. The documented accounts therefore did not match the generated accounts.
- **Severity:** Medium
- **Priority:** P1
- **Environment/build:** Windows local checkout, source `5535601`.
- **Status:** Fixed in commit `e41c5b6`; static retest passed. Clean database setup retest remains pending.
- **Evidence:** `README.md` Seed Data; `backend/seed/seed.py` `_get_or_create_user` calls.
- **Recommended action / retest:** Keep README values aligned with seed source; run seed on a disposable DB and verify each documented account can log in without publishing passwords in defect records.

### DOC-002 — Docker JWT secret example used a variable Compose ignores

- **Module:** Root environment example / Docker Compose / CI
- **Preconditions:** Copy root `.env.example` and start services with the documented Docker command.
- **Reproduction:** Compare the root `.env.example` variable with `docker-compose.yml` backend `JWT_SECRET_KEY` interpolation and `backend/app/core/config.py`.
- **Expected:** The example and CI pass the variable consumed by the backend and Docker Compose.
- **Actual:** Root example and workflow set `SECRET_KEY`; Compose and backend read `JWT_SECRET_KEY`, so the supplied value was ignored and the Compose fallback was used.
- **Severity:** Medium
- **Priority:** P1
- **Environment/build:** Docker configuration at `5535601`.
- **Status:** Fixed in commit `e41c5b6`; static retest passed. Docker startup retest remains pending.
- **Evidence:** `.env.example`, `.github/workflows/playwright.yml`, `docker-compose.yml`, `backend/app/core/config.py`.
- **Recommended action / retest:** Use `JWT_SECRET_KEY` consistently and verify Compose receives a generated local value without recording the value in logs or this report.

### DOC-003 — Chromium README and npm script selected a nonexistent project

- **Module:** Playwright execution instructions
- **Preconditions:** Automation dependencies installed.
- **Reproduction:** Run the previously documented `npx playwright test --project=chromium` or `npm run test:chromium`; compare with `automation/playwright.config.ts` project names.
- **Expected:** Documented selectors match actual Playwright project names.
- **Actual:** No project named `chromium` exists; configured names are `chromium-noauth`, `chromium-admin`, and `chromium-rbac`.
- **Severity:** Medium
- **Priority:** P1
- **Environment/build:** Playwright config at `5535601`.
- **Status:** Fixed in commit `e41c5b6`; `npm run test:chromium -- --list` reports the configured Chromium projects.
- **Evidence:** `README.md`, `automation/package.json`, `automation/playwright.config.ts`.
- **Recommended action / retest:** Keep the wildcard selector aligned with configured names and retain test-list output in the final verification log.

### DOC-004 — README and test strategy advertised unregistered suite tags

- **Module:** Test execution guidance
- **Preconditions:** Search the Playwright specs for the listed tags.
- **Reproduction:** Compare README `--grep @...` examples and the suite/tag table in `docs/test-strategy.md` with `automation/tests/**/*.spec.ts`.
- **Expected:** Each documented tag selects at least one test, or the docs use the available package scripts.
- **Actual:** The listed `@smoke`, `@auth`, `@projects`, `@rbac`, and `@api` labels were not applied to the specs. The README tag commands could select zero tests.
- **Severity:** Low
- **Priority:** P2
- **Environment/build:** Test documentation at `5535601`.
- **Status:** Fixed in commit `e41c5b6`; README now lists package scripts and test strategy describes actual suites.
- **Evidence:** `README.md`, `docs/test-strategy.md`, `automation/tests/`, `automation/package.json`.
- **Recommended action / retest:** Use `npm run test:<suite>` commands or add tags only when the suite actually uses them; validate commands with `--list`.

### DOC-005 — Functional test inventory stated that no tests had run

- **Module:** Test-case evidence documentation
- **Preconditions:** Compare `docs/test-cases.md` with the available Playwright report and current execution notes.
- **Reproduction:** Read the original inventory's “Not Run / Unverified” banner and compare it with the generated Playwright report showing 67 passing instances and the focused current runs.
- **Expected:** Test inventory states results that match available execution evidence and separates tests not covered by that evidence.
- **Actual:** The banner said the application was unavailable and all scenarios were unrun, despite the later recorded passing run.
- **Severity:** Medium
- **Priority:** P1
- **Environment/build:** Assessment documentation at `5535601`.
- **Status:** Fixed in commit `e41c5b6`; inventory now separates the prior full run, focused current tests, backend run, and unverified DB cases.
- **Evidence:** `docs/test-cases.md`, `automation/playwright-report/index.html`, `TestFlow-Playwright-Report.zip`.
- **Recommended action / retest:** Keep per-case statuses tied to test names and report scope; rerun full suite after any test changes before replacing the current all-suite evidence.

## Product defects and unverified findings

No product behavior defect was reproduced in the full passing Playwright run or focused current checks. The passing results do not cover the full ICSR scope. UI/API/MySQL reconciliation, MySQL update/delete consistency, exhaustive invalid SQL handling, and comprehensive Firefox/WebKit regression remain unverified requirements, not reported product defects.

No credentials, access tokens, connection strings, personal data, or failure screenshots are included. The all-passing run produced no failed-test screenshots or traces; the report package contains the self-contained HTML report only.

## Recommendations and retest order

1. Verify a clean Docker/manual setup using example files on a disposable database.
2. Execute the updated README test commands and retain the `--list`/run output.
3. Run a current full Playwright suite against an isolated test database after the logout/boundary additions; generate a fresh report.
4. Complete create/update/delete UI/API/MySQL reconciliation and attach sanitized SQL and observed results.
5. Reopen this report if a product defect is observed; record exact environment, test data (no secrets), steps, expected/actual behavior, severity, priority, evidence, fix, and retest result.
