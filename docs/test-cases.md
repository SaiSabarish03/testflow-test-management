# TestFlow Functional Test Inventory

## Execution evidence

- The full configured Playwright run recorded in `automation/playwright-report/index.html` reports **67 passed, 0 failed, 0 flaky, 0 skipped** in 261,433 ms (about 4.36 minutes). The report is from source baseline `abe32fe`; later changes committed in `e41c5b6` added logout/boundary coverage and altered reporting configuration, so this report does not represent current source.
- Current verification on 22 October 2026: backend **320 passed, 31 warnings** in 132.25 seconds using in-memory SQLite; current Playwright API read-only project-list and page-size boundary checks **2 passed**; current logout check **1 passed** plus 3 auth setup cases. The full current Playwright suite was not run because the live backend effective URL points to the populated `testflow` MySQL database.
- The API project-list test checks the response contract only. A single-request latency threshold was removed because it is not a stable performance SLO. A prior focused run observed 616 ms locally; this is an observation, not a performance claim. Direct UI/API/MySQL reconciliation remains unverified.
- Current source inventory has **58 distinct test titles** in `automation/tests/**/*.spec.ts` (plus 3 auth setup tests). The old 67 count is configured test instances, including four Firefox and four WebKit smoke repetitions; it is not the distinct scenario count for the current worktree.
- `automation/playwright-report/index.html` and `TestFlow-Playwright-Report.zip` remain prior-run evidence for the 67-instance run, not current-run evidence. The ZIP contains only the self-contained `index.html`; there are no separate screenshot/trace files. Current focused runs used the list reporter and did not refresh the HTML report.

| ID | Area | Scenario | Preconditions | Core steps | Expected result | Latest actual / evidence |
|---|---|---|---|---|---|---|
| AUTH-001 | Authentication | Valid admin login | Seeded active admin | Submit valid credentials | Dashboard and ADMIN role visible | PASS — full Playwright report; `auth.spec.ts` |
| AUTH-002 | Authentication | Invalid password | Login page available | Submit known email with wrong password | Rejected; user remains unauthenticated | PASS — full Playwright report; `auth.spec.ts` |
| AUTH-003 | Authentication | Unknown email | Login page available | Submit unregistered credentials | Rejected; no session created | PASS — full Playwright report; `auth.spec.ts` |
| AUTH-004 | Authentication | Protected route without session | No authenticated state | Navigate to dashboard/projects | Redirect to login | PASS — full Playwright report; `auth.spec.ts` |
| AUTH-005 | Authentication | Logout and protected-route guard | Test admin account | Log in, open user menu, select Logout, revisit projects | Login page shown; token removed | PASS — focused current run, 1 test + 3 setup; `auth.spec.ts` |
| PROJ-001 | Projects | Create project with valid key | Admin or QA | Submit unique name/key | Project created and shown | PASS — full Playwright report; `projects.spec.ts` |
| PROJ-002 | Projects | Reject invalid project key | Admin or QA | Submit lowercase/punctuation key | Validation error; no project created | PASS — full Playwright report; `projects.spec.ts` |
| PROJ-003 | Projects | Reject blank project name | Admin or QA | Submit without name | Required-field validation | PASS — full Playwright report; `projects.spec.ts` |
| SUITE-001 | Suites | Create, edit and delete suite | Existing project | Perform suite CRUD | Correct suite values and removal | PASS — full Playwright report; `test-suites.spec.ts` |
| SUITE-002 | Suites | Reject blank suite name | Existing project | Submit empty suite name | Validation error; no suite created | PASS — full Playwright report; `test-suites.spec.ts` |
| CASE-001 | Test cases | Create draft with steps and promote | Existing suite | Submit case and mark READY | Case and ordered steps persist | PASS — full Playwright report; `test-cases.spec.ts` |
| CASE-002 | Test cases | Reject missing mandatory fields | Existing suite | Submit empty case form | Title and expected-result errors appear | PASS — full Playwright report; `test-cases.spec.ts` |
| CASE-003 | Test cases | Reject duplicate step ordering | Existing suite; API available | Submit duplicate step order | Request rejected with validation error | PASS — backend `test_duplicate_step_order_returns_422`; 320-test run |
| RUN-001 | Execution | Record PASS result | Ready case and run | Start, record PASS, complete | Result and run state update | PASS — full Playwright report; `test-runs.spec.ts` |
| RUN-002 | Execution | Block completion with NOT_RUN results | Run contains unexecuted case | Attempt completion | Completion rejected with validation message | PASS — full Playwright report; `test-runs.spec.ts` |
| DEF-001 | Defects | Create defect with required fields | Existing project; authorized user | Submit valid defect | Defect detail has expected project/status | PASS — full Playwright report; `defects.spec.ts` |
| RBAC-001 | Authorization | Viewer cannot create project | Viewer token | POST project create | HTTP 403; no project created | PASS — full Playwright report; `api.spec.ts` |
| RBAC-002 | Authorization | Unauthenticated API request | No bearer token | GET `/api/auth/me` | HTTP 401 | PASS — full Playwright report; `api.spec.ts` |
| USER-001 | User management | Restrict user creation to admin | QA/Viewer role | Attempt create-user operation | Non-admin is forbidden | PASS — backend user tests; 320-test run |
| API-001 | API boundary | Reject page size above maximum | QA account | GET projects with `page_size=101` | HTTP 422 with validation details | PASS — focused current API run, 2 tests |
| DB-001 | Persistence | Reconcile project with MySQL | Dedicated test database | Create in UI/API; query matching row | UI, API and DB fields agree | NOT VERIFIED — no cross-layer comparison |
| DB-002 | Relationships | Reconcile suite/case foreign keys | Dedicated test database | Create project/suite/case; query joins | Child rows reference expected parents | NOT VERIFIED — no workflow SQL evidence |
| DB-003 | Persistence | Verify update and delete consistency | Dedicated test database | Update/delete through app; inspect DB | Persisted state matches app/API | NOT VERIFIED — no CRUD reconciliation |
| DB-004 | Database validation | Duplicate/NULL/invalid SQL checks | Dedicated test database | Run read-only integrity queries | Findings match stated constraints | PARTIAL — selected MySQL checks are reported in `database-validation.md`; raw queries/results are not attached |

## Scenario-count rule

Count distinct test titles in source files, not browser-project repetitions or setup tests. A collected or executed scenario count does not imply that the assignment's entire functional scope is covered. The inventory keeps database reconciliation cases separate because they are not covered by the passing UI/API report.
