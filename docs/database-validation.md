# TestFlow Database Validation Report (MySQL)

**Status:** Partial execution completed â€” live MySQL validation performed.

**Execution date:** 2026-10-22
**Database:** `testflow`
**Database driver:** `mysql+pymysql`
**Execution method:** SQLAlchemy with read-only SQL queries
**Environment:** Local development environment

## 1. Scope and execution notes

The database validation was executed against the locally configured MySQL database. The connection was confirmed, and read-only queries were used to inspect table counts, duplicate business keys, selected relationships, required fields, foreign-key metadata, and test-run timestamps.

No inserts, updates, or deletes were performed by these validation queries.

The report distinguishes checks actually executed from checks that remain planned. Results apply to the database state observed during this execution; they are not a guarantee of future data integrity.

## 2. Table inventory and row counts

| Table | Observed row count |
|---|---:|
| `users` | 10 |
| `projects` | 254 |
| `project_members` | 3 |
| `test_suites` | 193 |
| `test_cases` | 92 |
| `test_runs` | 62 |
| `test_results` | 76 |
| `defects` | 60 |
| **Total rows across listed tables** | **750** |

These counts describe the observed database state. They do not independently establish that every record is valid or expected.

## 3. Required-field checks â€” executed

The following 11 fields were checked for `NULL` values:

| Field | NULL violations |
|---|---:|
| `users.name` | 0 |
| `users.email` | 0 |
| `projects.name` | 0 |
| `projects.key` | 0 |
| `test_suites.name` | 0 |
| `test_cases.title` | 0 |
| `test_cases.expected_result` | 0 |
| `test_runs.name` | 0 |
| `test_runs.environment` | 0 |
| `test_results.status` | 0 |
| `defects.title` | 0 |

**Result:** PASS for the fields checked.

The original plan also included other required fields, such as password hashes, roles, statuses, creator IDs, priorities, and foreign-key columns. Those fields were not all independently included in the executed `NULL` audit and remain outstanding for this specific check.

## 4. Duplicate business keys and uniqueness â€” executed

| Check | Returned rows | Result |
|---|---:|---|
| Duplicate user emails | 0 | PASS |
| Duplicate project keys | 0 | PASS |
| Duplicate project memberships (`project_id`, `user_id`) | 0 | PASS |
| Duplicate test results (`test_run_id`, `test_case_id`) | 0 | PASS |

The duplicate queries returned no violating groups for the observed database state.

## 5. Relationship integrity â€” executed

| Check | Returned rows | Result |
|---|---:|---|
| Projects referencing missing creator users | 0 | PASS |
| Test cases referencing missing suites | 0 | PASS |
| Test results referencing missing runs or cases | 0 | PASS |
| Test results whose run and case belong to different projects | 0 | PASS |

These queries detected no violations for the relationships and conditions explicitly checked. They do not replace a complete audit of every foreign-key relationship.

## 6. Foreign-key schema verification â€” executed

The MySQL `information_schema.KEY_COLUMN_USAGE` metadata query returned **16 foreign-key constraints**.

| Table | Referenced table | Relationship columns |
|---|---|---|
| `defects` | `users` | `assigned_to`, `created_by` |
| `defects` | `projects` | `project_id` |
| `defects` | `test_cases` | `test_case_id` |
| `project_members` | `projects` | `project_id` |
| `project_members` | `users` | `user_id` |
| `projects` | `users` | `created_by` |
| `test_cases` | `users` | `created_by` |
| `test_cases` | `test_suites` | `suite_id` |
| `test_results` | `users` | `executed_by` |
| `test_results` | `test_cases` | `test_case_id` |
| `test_results` | `test_runs` | `test_run_id` |
| `test_runs` | `users` | `created_by` |
| `test_runs` | `projects` | `project_id` |
| `test_suites` | `users` | `created_by` |
| `test_suites` | `projects` | `project_id` |

**Result:** 16 foreign-key constraints were reported by the metadata query. The output contains 15 table/relationship rows above because the `defects` â†’ `users` relationship has two separate foreign-key columns (`assigned_to` and `created_by`).

## 7. Test-run workflow consistency â€” executed

| Check | Returned rows | Result |
|---|---:|---|
| Completed/passed/failed runs missing `completed_at` | 0 | PASS for the query criteria |
| Runs where `completed_at` precedes `started_at` | 0 | PASS |

The first query treated `COMPLETED`, `PASSED`, and `FAILED` as terminal statuses. This was a provisional query condition; it should be reconciled with the current `TestRunStatus` enum and service implementation before being treated as a complete business-rule validation.

The separate planned check for completed runs containing `NOT_RUN` results has **not yet been executed**.

## 8. UI/API/database reconciliation â€” outstanding

The following end-to-end reconciliation procedure remains planned:

1. Create a uniquely named project through the UI or API and record its returned ID and key.
2. Query `projects` by that key and compare `name`, `status`, and `created_by`.
3. Create a suite and case, then compare API IDs and foreign keys with `test_suites` and `test_cases`.
4. Update a field and verify the API response against the persisted database row.
5. Submit invalid or duplicate inputs and verify that rejected operations do not create extra rows.
6. Create a test run and results, then compare their stored states with the API and UI.
7. Exercise the supported archive/deactivation workflow and verify the stored status.

No results are claimed for these steps until they have been executed and recorded.

## 9. Remaining validation work

- Check all required fields identified in the original plan, including creator IDs, statuses, priorities, and mandatory relationship columns.
- Execute the completed-run/`NOT_RUN` consistency query after confirming the intended workflow rule.
- Audit the remaining relationships not covered by the executed orphan queries.
- Compare additional uniqueness and schema constraints against the ORM models.
- Perform and document the UI/API/database reconciliation procedure.
- Capture sanitized query output and record the database engine/version and execution timestamp for repeatable evidence.

## 10. Conclusion

The live MySQL validation executed on 2026-10-22 found no violations in the duplicate checks, selected relationship checks, cross-project result check, 11 required-field checks, or two test-run timestamp checks. The schema metadata query returned 16 foreign-key constraints.

These results provide evidence of database integrity for the specific checks executed. They do not constitute exhaustive database certification, and the outstanding validation items remain open.

**Security note:** Do not include database passwords, secret keys, or complete connection strings in this report.
