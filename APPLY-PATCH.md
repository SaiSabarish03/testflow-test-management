# TestFlow ICSR targeted patch

This bundle contains targeted source/documentation changes based on static inspection of the uploaded archive. It does not include `.git`, real `.env` files, authentication storage state, browser profiles, local database files, logs, `node_modules`, or generated reports.

## Apply

Extract this ZIP into the root of your existing `testflow` repository, preserving the folder structure. Review the diff before committing. Do not replace or overwrite your real local `.env` files.

## Changes included

- Adds 8 Playwright API scenarios covering authentication, protected endpoints, project list/schema, invalid project keys, duplicate project keys, viewer authorization, and a project → suite → READY test case → run → result → completion workflow.
- Adds `api`, `firefox`, and `webkit` Playwright projects; retains Chromium and no-auth project coverage.
- Retains Playwright traces on failures and ensures `.auth/` is created before auth state is written.
- Adds `test:api` and updates the Chromium test script.
- Aligns the root example JWT secret variable and CI environment variable with `JWT_SECRET_KEY`.
- Aligns README seed account emails and adds functional test inventory, database validation plan, defect-report status, and baseline gap matrix.

## Local validation commands

From the repository root, start the application/database using your verified local configuration first. Then:

```powershell
cd automation
npm ci
npx playwright install
npm run test:api
npm run test:chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
npx playwright show-report
```

Backend regression, from the backend directory with its project dependencies installed and a dedicated test database configured:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

## Validation limitations

- JSON manifests and the Docker Compose / workflow YAML parsed successfully in the review environment.
- The API test file was statically inspected, but TypeScript compilation and Playwright execution were **not verified** because dependencies could not be installed in this environment (package registry DNS/network unavailable).
- No live app or MySQL instance was available here. Do not report any new test as passed until you run it locally and capture the actual output.
- Browser projects are configured but Firefox/WebKit execution is not verified.
- The API workflow creates a test run; the current API has no run-delete endpoint, so the uniquely named run remains in the dedicated test database. Do not run this test against production or a shared database.
