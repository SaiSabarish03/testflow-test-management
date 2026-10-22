# TestFlow Defect Report â€” ICSR Submission

**Review date:** 22 October 2026
**Environment:** Uploaded source archive reviewed in an isolated execution environment
**Status:** No product defect has been confirmed by a successful reproduction in this review.

## Environment / validation blockers (not product defects)

| ID | Summary | Classification | Evidence | Status |
|---|---|---|---|---|
| ENV-001 | Backend regression collection blocked by missing Python dependency `pymysql` | Review-environment dependency failure | `python -m pytest -q` stopped during import of `backend/app/core/database.py` | Open â€” install project dependencies in the local assessment environment |
| ENV-002 | Backend regression collection with a temporary SQLite URL blocked by missing Python dependency `bcrypt` | Review-environment dependency failure | `DATABASE_URL=sqlite:////tmp/testflow_baseline.db APP_ENV=test python -m pytest -q` stopped during import of `backend/app/core/security.py` | Open â€” install project dependencies in the local assessment environment |
| ENV-003 | Automation dependency installation did not complete; `npm ls --depth=0` reported incomplete/invalid installed packages | Review-environment dependency/network failure | `npm ci --ignore-scripts --no-audit --no-fund` did not complete within the execution window; package registry DNS was unavailable for the Python dependency install | Open â€” run `npm ci` on the user's machine with registry access |

These are not application defects and must not be counted as failed product test cases.

## Product defects

No product defect is listed as confirmed because the application and its tests could not be executed successfully in this review environment. Do not interpret this as proof that the application is defect-free.

For every product defect reproduced later, record:
- Defect ID and concise title
- Module and environment
- Preconditions and test data (no secrets)
- Exact reproduction steps
- Expected and actual results
- Severity and priority
- Screenshot/trace or sanitized API/database evidence
- Root cause only when established
- Regression test and retest status
