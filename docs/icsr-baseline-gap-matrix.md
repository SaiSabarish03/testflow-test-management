# ICSR Baseline Gap Matrix — TestFlow

**Review date:** 22 October 2026
**Repository revision:** `5535601` (`main` and local `origin/main`)
**Detailed matrix:** [docs/icsr-assessment.md](icsr-assessment.md) contains individual F1–F13, U1–U14, A1–A12, D1–D9, B1–B8, and L1–L12 statuses.

This file replaces the stale archive-based baseline. The prior archive notes referred to commit `e2c6d43` and blocked test execution; those observations do not describe the current checkout.

## Current evidence

| Area | Current evidence | Status and remaining gap |
|---|---|---|
| Source revision | `5535601` is HEAD and equals local `origin/main`; this commit changes the assessment document only relative to `abe32fe`. | Current application and automation source match the successful full Playwright run on that baseline. Verify the remote branch before submission. |
| Playwright suite | Embedded report data: 67 total, 67 expected, 0 unexpected, 0 flaky, 0 skipped; 261,433 ms. | Configured instances include setup/browser repetitions; 56 distinct test titles existed in that run. Current worktree adds logout and page-size boundary tests; focused runs passed, but the current full suite was not rerun. |
| Current focused checks | Logout: 1 scenario passed plus 3 auth setup cases. API project-list timing and page-size boundary: 2 passed. | No full-run report has been generated after these additions. |
| Backend suite | 320 passed, 31 warnings in the same application source baseline. | Review warnings separately; test execution does not establish UI behavior or MySQL reconciliation. |
| Browser scope | Chromium broad UI suite; Firefox and WebKit each have four authentication/route smoke scenarios in the full run. | Firefox/WebKit are not full regression coverage. |
| API scope | Eight API scenarios were in the full report; current API suite now includes an additional page-size boundary check and response-time assertion. | Response-time threshold is a 2-second local test threshold, not a production SLO. |
| POM/fixtures/data | Page classes, shared page fixtures, auth setup, and unique data generators exist and are exercised. | Use an isolated test database; a fresh full current suite execution is still needed. |
| Report artifact | `automation/playwright-report/index.html` embeds the report data; `TestFlow-Playwright-Report.zip` contains the self-contained HTML file. | The zip and report are local/untracked. The all-passing report has no standalone failure screenshot/trace files. |
| Defect report | `docs/defect-report.md` documents five confirmed README/config/test-doc defects with repro, expected/actual, severity, priority, status, evidence and recommendations. | Fixes are in the working tree; clean-checkout setup retest remains outstanding. |
| Functional test inventory | `docs/test-cases.md` maps scenarios to test names and evidence. | DB-001 through DB-004 remain not verified or partial as marked there. |
| Database checks | `docs/database-validation.md` records partial read-only MySQL checks (750 point-in-time rows, selected constraints/duplicates/NULLs/relationships/timestamps). | No direct UI/API-to-SQL create/update/delete reconciliation; raw query output is not attached. |
| Setup/test docs | README, root `.env.example`, CI variable, package scripts, trace config and test strategy corrected in the working tree. | These edits have not been committed or pushed. |

## Priority gaps

| Priority | Gap | Action |
|---|---|---|
| P0 | Current full suite has not been rerun after test/config edits; prior report is pre-edit | Run all configured projects on a disposable test DB and generate a fresh report. |
| P0 | Report and ZIP are local/untracked | Attach the ZIP or provide an evaluator-accessible report artifact. Do not imply it is in GitHub. |
| P0 | UI/API/MySQL reconciliation is incomplete | Compare representative create/update/delete responses and UI values with read-only SQL on a dedicated database. |
| P1 | Firefox/WebKit coverage is auth/route smoke only | Keep scope explicit or extend if time permits. |
| P1 | Boundary scope is limited to API page size | Add representative UI and additional API boundary cases if time permits. |
| P1 | API response time is measured under local conditions | Keep the threshold context explicit; do not label it an SLO. |
| P2 | Frontend build/lint and warning review are prior evidence | Re-run only if source changes require it; document the existing warnings accurately. |

## Scoring note

The ICSR email supplies no numerical weights. No updated overall compliance percentage is asserted here. Use the detailed assessment matrix and distinguish verified execution from partial implementation.
