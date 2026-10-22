# Functional Test Inventory â€” TestFlow

**Execution status:** The source contains relevant automation scenarios, but actual results in this review remain **Not Run / Unverified** because dependencies could not be installed and no live application was available.

| ID | Area | Scenario | Preconditions | Core steps | Expected result | Actual / status |
|---|---|---|---|---|---|---|
| AUTH-001 | Authentication | Valid admin login | Seeded active admin account | Submit valid email/password | Session established; dashboard visible; role is ADMIN | Not run |
| AUTH-002 | Authentication | Invalid password | Login page available | Submit known email with incorrect password | Authentication rejected; user remains unauthenticated | Not run |
| AUTH-003 | Authentication | Unknown email | Login page available | Submit unregistered email/password | Authentication rejected without session creation | Not run |
| AUTH-004 | Authentication | Protected route without session | No saved auth state | Navigate directly to dashboard | Redirect to login or equivalent unauthenticated response | Not run |
| PROJ-001 | Projects | Create project with valid key | Admin or QA account | Submit unique name and uppercase alphanumeric key | Project created and persisted; returned key matches input | Not run |
| PROJ-002 | Projects | Reject invalid project key | Admin or QA account | Submit lowercase/punctuation-containing key | Validation error; no project created | Not run |
| PROJ-003 | Projects | Reject blank project name | Admin or QA account | Submit project without name | Required-field validation appears; no project created | Not run |
| SUITE-001 | Suites | Create suite under project | Existing active project | Submit valid suite name | Suite is associated with correct project | Not run |
| SUITE-002 | Suites | Reject blank suite name | Existing project | Submit empty suite name | Validation error; no suite created | Not run |
| CASE-001 | Test cases | Create draft case with steps | Existing suite | Submit title, expected result, priority and ordered steps | Case created with correct suite relationship and steps | Not run |
| CASE-002 | Test cases | Reject missing mandatory fields | Existing suite | Submit case without title/expected result | Request rejected or form validation shown; no invalid row | Not run |
| CASE-003 | Test cases | Validate duplicate step ordering | Existing suite; API available | Submit two steps with same order | Request rejected by schema validation | Not run |
| RUN-001 | Execution | Record PASS result | Ready test case and run | Start run, record PASS, complete run | Result and run state persist consistently | Not run |
| RUN-002 | Execution | Prevent completion with NOT_RUN results | Run with unexecuted cases | Attempt to complete run | Business-rule validation prevents invalid completion | Not run |
| DEF-001 | Defects | Create defect with required fields | Existing project; authorized role | Submit title, severity and priority | Defect created with expected status and project link | Not run |
| RBAC-001 | Authorization | Viewer cannot create project | Active VIEWER account | Send authenticated project-create request | Backend returns 403; no project created | Not run |
| RBAC-002 | Authorization | Unauthenticated API request | No bearer token | Request protected resource | Backend returns 401 | Not run |
| USER-001 | User management | Restrict user creation to admin | QA/Viewer account | Submit create-user API request | Non-admin request rejected with 403 | Not run |
| DB-001 | Persistence | Verify UI/API project against MySQL | Dedicated test database | Create project, query row by unique key, compare fields | UI, API and database values agree | Not run |
| DB-002 | Relationships | Verify suite/case foreign keys | Dedicated test database | Create projectâ†’suiteâ†’case and inspect relationships | Each child references the correct parent | Not run |

Use these IDs in the execution log and defect report. Update **Actual / status** only after running the scenario, and attach report paths or sanitized evidence.
