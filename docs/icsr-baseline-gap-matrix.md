# ICSR Baseline Gap Matrix — TestFlow

**Review date:** 22 October 2026
**Repository revision:** `e41c5b6` (`main` and local `origin/main` at final audit; current working tree has uncommitted audit updates)
**Detailed matrix:** [docs/icsr-assessment.md](icsr-assessment.md) contains individual F1–F13, U1–U14, A1–A12, D1–D9, B1–B8, and L1–L12 statuses.

This file replaces the stale archive-based baseline. The prior archive notes referred to commit `e2c6d43` and blocked test execution; those observations do not describe the current checkout.

## Current evidence

| Area | Current evidence | Status and remaining gap |
|---|---|---|
| Source revision | `e41c5b6` is HEAD and equals local `origin/main`; current working tree has uncommitted audit edits. | It is not the revision for all current checks. The updated working tree remains uncommitted. |
| Prior Playwright full run | Embedded report data: 67 total, 67 expected, 0 unexpected, 0 flaky, 0 skipped; 261,433 ms. | Prior-run evidence only. Current configured discovery reports 69 instances; 58 unique source test titles. |
| Current focused checks | Logout: 1 scenario passed plus 3 auth setup cases. Read-only API project-list and page-size boundary: 2 passed. | Current working-tree focused runs; no current full-run report was generated. |
| Backend suite | 320 passed, 31 warnings in 132.25 seconds. | In-memory SQLite fixtures; does not test MySQL reconciliation. |
| Browser scope | Chromium broad UI suite; Firefox and WebKit each have four authentication/route smoke scenarios in the full run. | Firefox/WebKit are not full regression coverage. |
| API scope | Nine API scenarios are currently configured; the current focused run covered project-list shape and page-size boundary. | A single-request timing assertion was removed as an unstable performance gate. |
| POM/fixtures/data | Page classes, shared page fixtures, auth setup, and unique data generators exist and are exercised. | Use an isolated test database; a fresh full current suite execution is still needed. |
| Report artifact | `automation/playwright-report/index.html` embeds prior report data; tracked `TestFlow-Playwright-Report.zip` contains that self-contained HTML file. | Prior-run report only; focused runs did not regenerate it. ZIP contains no separate failure screenshot/trace files. |
| Defect report | `docs/defect-report.md` documents five confirmed README/config/test-doc defects with repro, expected/actual, severity, priority, status, evidence and recommendations. | Fixes are in committed `e41c5b6`; clean-checkout setup retest remains outstanding. |
| Functional test inventory | `docs/test-cases.md` maps scenarios to test names and evidence. | DB-001 through DB-004 remain not verified or partial as marked there. |
| Database checks | `docs/database-validation.md` records partial read-only MySQL checks (750 point-in-time rows, selected constraints/duplicates/NULLs/relationships/timestamps). | No direct UI/API-to-SQL create/update/delete reconciliation; raw query output is not attached. |
| Setup/test docs | README, root `.env.example`, CI variable, package scripts, trace config and test strategy corrected in the working tree. | Prior setup/config edits are in `e41c5b6`; the latest audit documentation updates remain uncommitted. |

## Priority gaps

| Priority | Gap | Action |
|---|---|---|
| P0 | Current full suite has not been rerun; effective DB is populated `testflow` | Provision/verify an isolated disposable DB, point services to it, then run full suite and generate a fresh report. |
| P0 | The tracked report ZIP is stale (prior 67-instance run) | Generate a current report after full safe regression and confirm evaluator accessibility. |
| P0 | UI/API/MySQL reconciliation is incomplete | Compare representative create/update/delete responses and UI values with read-only SQL on a dedicated database. |
| P1 | Firefox/WebKit coverage is auth/route smoke only | Keep scope explicit or extend if time permits. |
| P1 | Boundary scope is limited to API page size | Add representative UI and additional API boundary cases if time permits. |
| P1 | API response time is measured under local conditions | Keep the threshold context explicit; do not label it an SLO. |
| P2 | Frontend build/lint and warning review are prior evidence | Re-run only if source changes require it; document the existing warnings accurately. |

## Scoring note

The ICSR email supplies no numerical weights. No updated overall compliance percentage is asserted here. Use the detailed assessment matrix and distinguish verified execution from partial implementation.
