# Test Execution Summary

**Execution date:** 22 October 2026 (IST)  
**Repository `HEAD`:** `e41c5b6` (`main`, equal to `origin/main` at final audit); checks below ran against the working tree, with the final API rerun after removal of the timing assertion.  
**Environment:** Windows local checkout; frontend and backend health checks responded successfully. The live backend's effective SQLAlchemy URL resolves to MySQL database `testflow` on localhost.

## Current runs

| Command | Scope | Result | Duration / notes |
|---|---|---|---|
| `python -m pytest -q` from `backend/` | Backend regression; in-memory SQLite fixtures | **320 passed, 0 failed; 31 warnings** | 132.25 seconds |
| `npx.cmd playwright test --list` from `automation/` | Discovery only | **69 configured instances**, 0 executed | Current config; 58 distinct test titles in 10 `.spec.ts` files, plus 3 auth setup tests |
| `npx.cmd playwright test --project=api --grep "authenticated project list\|page size above" --reporter=list --output=test-results/current-api-readonly` from `automation/` | Read-only project-list shape and pagination boundary | **2 passed, 0 failed** | 1.9 seconds total; response contract assertions only, no latency claim |
| `npx.cmd playwright test --project=chromium-noauth --grep "Authenticated user can log out" --reporter=list --output=test-results/current-logout` from `automation/` | Auth setup and logout/protected-route check | **4 passed, 0 failed**: 3 setup + 1 scenario | 12.5 seconds |

The logout and focused API checks perform login/authentication and reads; they do not create application records. The full Playwright suite was not run because it includes mutating UI/API workflows and the active backend targets the populated `testflow` database. No disposable database was available to verify.

## Prior full Playwright evidence

The existing `automation/playwright-report/index.html` records **67 passed, 0 failed, 0 flaky, 0 skipped in 261,433 ms**, from the earlier source baseline `abe32fe`. It is prior-run evidence, not a report for the current working tree. The root `TestFlow-Playwright-Report.zip` contains only that self-contained `index.html`; it contains no separate screenshots or traces. Current focused runs used the list reporter and did not refresh the HTML report. Preserve and label this prior report; do not present it as current full-regression evidence.

## Limitations

- Current full Playwright execution and fresh HTML report are blocked pending an isolated disposable DB and a verified backend connection to it.
- Firefox and WebKit coverage is limited to authentication/route smoke cases.
- Direct UI/API/MySQL create, update, and delete reconciliation is not verified.
- The HTML report is ignored/local; the root ZIP is tracked in `e41c5b6`. Evaluator access and acceptance of that ZIP have not been confirmed.
- No failure artifacts are claimed; the prior full run passed and no current failures were produced.
