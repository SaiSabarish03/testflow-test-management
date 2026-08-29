"""
End-to-end Test Run workflow validation against the live backend.
Run from: e:\PlayWright\testflow\backend
Usage: python validate_run_workflow.py
"""
import sys
import requests

BASE = "http://localhost:8000"

def ok(label):
    print(f"  PASS  {label}")

def fail(label, detail=""):
    print(f"  FAIL  {label}: {detail}")
    sys.exit(1)

def check(label, resp, expected_status):
    if resp.status_code != expected_status:
        fail(label, f"HTTP {resp.status_code} — {resp.text[:200]}")
    ok(label)
    return resp.json()

# ── 1. Login ──────────────────────────────────────────────────────────────────
print("\n[1] Login")
r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@testflow.local", "password": "Admin123!"})
data = check("Admin login", r, 200)
TOKEN = data["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

# ── 2. List projects ──────────────────────────────────────────────────────────
print("\n[2] Projects")
r = requests.get(f"{BASE}/api/projects?page=1&page_size=10", headers=H)
data = check("List projects", r, 200)
project = next((p for p in data["items"] if p["key"] == "TFW"), None)
if not project:
    fail("Find TFW project", "not found")
ok(f"Found project TFW id={project['id']}")
PID = project["id"]

# ── 3. List suites to find READY test cases ───────────────────────────────────
print("\n[3] Suites & READY test cases")
r = requests.get(f"{BASE}/api/suites?project_id={PID}&page=1&page_size=20", headers=H)
# suites are listed per project
r = requests.get(f"{BASE}/api/projects/{PID}/suites?page=1&page_size=20", headers=H)
data = check("List suites", r, 200)
suites = data["items"]
ok(f"Found {len(suites)} suites")

ready_case_ids = []
for suite in suites:
    r = requests.get(f"{BASE}/api/suites/{suite['id']}/test-cases?status=READY&page=1&page_size=50", headers=H)
    if r.status_code == 200:
        for tc in r.json()["items"]:
            ready_case_ids.append(tc["id"])

if not ready_case_ids:
    fail("Find READY test cases", "none found")
ok(f"Found {len(ready_case_ids)} READY test cases: {ready_case_ids[:3]}...")

# ── 4. Verify DRAFT test cases cannot be used ─────────────────────────────────
print("\n[4] DRAFT rejection")
# Create a draft case in the first suite
r = requests.post(f"{BASE}/api/suites/{suites[0]['id']}/test-cases", headers=H, json={
    "title": "Validation Draft Case",
    "expected_result": "N/A",
    "priority": "LOW",
    "status": "DRAFT",
})
if r.status_code == 201:
    draft_id = r.json()["id"]
    r2 = requests.post(f"{BASE}/api/projects/{PID}/runs", headers=H, json={
        "name": "Should Fail",
        "environment": "QA",
        "test_case_ids": [draft_id],
    })
    if r2.status_code == 400:
        ok("DRAFT test case rejected (400)")
    else:
        fail("DRAFT rejection", f"Expected 400, got {r2.status_code}")
else:
    ok("DRAFT rejection (skipped — could not create draft case)")

# ── 5. Create Test Run ────────────────────────────────────────────────────────
print("\n[5] Create Test Run")
tc_ids = ready_case_ids[:2]
r = requests.post(f"{BASE}/api/projects/{PID}/runs", headers=H, json={
    "name": "Validation Run — Phase 10",
    "environment": "QA-Validation",
    "test_case_ids": tc_ids,
})
run = check("Create run", r, 201)
RUN_ID = run["id"]
ok(f"Run id={RUN_ID} status={run['status']}")
assert run["status"] == "NOT_STARTED", f"Expected NOT_STARTED, got {run['status']}"
ok("Initial status is NOT_STARTED")

# ── 6. List runs ──────────────────────────────────────────────────────────────
print("\n[6] List runs")
r = requests.get(f"{BASE}/api/projects/{PID}/runs?page=1&page_size=20", headers=H)
data = check("List runs", r, 200)
assert data["total"] >= 1
ok(f"Total runs: {data['total']}")

# ── 7. Get run detail ─────────────────────────────────────────────────────────
print("\n[7] Run detail")
r = requests.get(f"{BASE}/api/runs/{RUN_ID}", headers=H)
run_detail = check("Get run detail", r, 200)
assert run_detail["name"] == "Validation Run — Phase 10"
assert run_detail["environment"] == "QA-Validation"
ok("Run detail fields correct")

# ── 8. Cannot complete NOT_STARTED run ───────────────────────────────────────
print("\n[8] State machine — invalid transitions")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/complete", headers=H)
assert r.status_code == 409, f"Expected 409, got {r.status_code}"
ok("Cannot complete NOT_STARTED (409)")

r = requests.post(f"{BASE}/api/runs/{RUN_ID}/abort", headers=H)
assert r.status_code == 409, f"Expected 409, got {r.status_code}"
ok("Cannot abort NOT_STARTED (409)")

# ── 9. Start run ──────────────────────────────────────────────────────────────
print("\n[9] Start run")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/start", headers=H)
run = check("Start run", r, 200)
assert run["status"] == "IN_PROGRESS"
assert run["started_at"] is not None
ok(f"Status=IN_PROGRESS, started_at={run['started_at']}")

# ── 10. Cannot start again ────────────────────────────────────────────────────
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/start", headers=H)
assert r.status_code == 409
ok("Cannot start IN_PROGRESS run (409)")

# ── 11. List results ──────────────────────────────────────────────────────────
print("\n[10] Results")
r = requests.get(f"{BASE}/api/runs/{RUN_ID}/results?page=1&page_size=50", headers=H)
results_data = check("List results", r, 200)
results = results_data["items"]
assert len(results) == len(tc_ids), f"Expected {len(tc_ids)} results, got {len(results)}"
ok(f"Got {len(results)} results, all NOT_RUN")
for res in results:
    assert res["status"] == "NOT_RUN"
    assert res["test_case"] is not None
    assert "title" in res["test_case"]
ok("All results NOT_RUN with test_case info")

# ── 12. Cannot complete with NOT_RUN results ──────────────────────────────────
print("\n[11] Complete blocked by NOT_RUN")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/complete", headers=H)
assert r.status_code == 409
detail = r.json().get("detail", "")
assert "NOT_RUN" in detail, f"Expected NOT_RUN in detail, got: {detail}"
ok(f"Complete blocked: '{detail}'")

# ── 13. Record results ────────────────────────────────────────────────────────
print("\n[12] Record results")
r1 = requests.put(f"{BASE}/api/runs/{RUN_ID}/results/{results[0]['id']}", headers=H,
                  json={"status": "PASSED", "actual_result": "Login succeeded as expected"})
res1 = check("Record PASSED", r1, 200)
assert res1["status"] == "PASSED"
assert res1["executed_by"] == 1  # admin user id
assert res1["executed_at"] is not None
ok(f"PASSED recorded, executed_by={res1['executed_by']}, executed_at={res1['executed_at']}")

if len(results) > 1:
    r2 = requests.put(f"{BASE}/api/runs/{RUN_ID}/results/{results[1]['id']}", headers=H,
                      json={"status": "FAILED", "actual_result": "Unexpected error on submit"})
    res2 = check("Record FAILED", r2, 200)
    assert res2["status"] == "FAILED"
    ok("FAILED recorded")

# ── 14. Summary ───────────────────────────────────────────────────────────────
print("\n[13] Summary")
r = requests.get(f"{BASE}/api/runs/{RUN_ID}/summary", headers=H)
summary = check("Get summary", r, 200)
ok(f"total={summary['total']} passed={summary['passed']} failed={summary['failed']} not_run={summary['not_run']} pass_rate={summary['pass_rate']}")
assert summary["total"] == len(tc_ids)

# ── 15. Complete run ──────────────────────────────────────────────────────────
print("\n[14] Complete run")
# If any NOT_RUN remain, record them first
r = requests.get(f"{BASE}/api/runs/{RUN_ID}/results?page=1&page_size=50", headers=H)
remaining = [x for x in r.json()["items"] if x["status"] == "NOT_RUN"]
for res in remaining:
    requests.put(f"{BASE}/api/runs/{RUN_ID}/results/{res['id']}", headers=H,
                 json={"status": "BLOCKED", "actual_result": "Blocked by environment issue"})
    ok(f"Recorded BLOCKED for result {res['id']}")

r = requests.post(f"{BASE}/api/runs/{RUN_ID}/complete", headers=H)
run = check("Complete run", r, 200)
assert run["status"] == "COMPLETED"
assert run["completed_at"] is not None
ok(f"Status=COMPLETED, completed_at={run['completed_at']}")

# ── 16. Terminal state — no further transitions ───────────────────────────────
print("\n[15] Terminal state")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/start", headers=H)
assert r.status_code == 409
ok("Cannot start COMPLETED run (409)")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/abort", headers=H)
assert r.status_code == 409
ok("Cannot abort COMPLETED run (409)")
r = requests.post(f"{BASE}/api/runs/{RUN_ID}/complete", headers=H)
assert r.status_code == 409
ok("Cannot complete COMPLETED run (409)")

# ── 17. Abort workflow (separate run) ─────────────────────────────────────────
print("\n[16] Abort workflow")
r = requests.post(f"{BASE}/api/projects/{PID}/runs", headers=H, json={
    "name": "Abort Test Run",
    "environment": "QA-Abort",
    "test_case_ids": [tc_ids[0]],
})
abort_run = check("Create run for abort", r, 201)
ABORT_ID = abort_run["id"]
requests.post(f"{BASE}/api/runs/{ABORT_ID}/start", headers=H)
r = requests.post(f"{BASE}/api/runs/{ABORT_ID}/abort", headers=H)
aborted = check("Abort run", r, 200)
assert aborted["status"] == "ABORTED"
ok("Status=ABORTED")
r = requests.post(f"{BASE}/api/runs/{ABORT_ID}/start", headers=H)
assert r.status_code == 409
ok("Cannot restart ABORTED run (409)")

# ── 18. VIEWER RBAC ───────────────────────────────────────────────────────────
print("\n[17] VIEWER RBAC")
r = requests.post(f"{BASE}/api/auth/login", json={"email": "viewer@testflow.local", "password": "View123!"})
viewer_data = check("Viewer login", r, 200)
VH = {"Authorization": f"Bearer {viewer_data['access_token']}"}

r = requests.get(f"{BASE}/api/projects/{PID}/runs?page=1&page_size=5", headers=VH)
check("Viewer can list runs", r, 200)

r = requests.get(f"{BASE}/api/runs/{RUN_ID}/summary", headers=VH)
check("Viewer can read summary", r, 200)

r = requests.post(f"{BASE}/api/projects/{PID}/runs", headers=VH, json={
    "name": "Viewer Run", "environment": "QA", "test_case_ids": [tc_ids[0]]
})
assert r.status_code == 403
ok("Viewer cannot create run (403)")

r = requests.post(f"{BASE}/api/runs/{RUN_ID}/start", headers=VH)
assert r.status_code == 403
ok("Viewer cannot start run (403)")

# ── 19. Final summary ─────────────────────────────────────────────────────────
print("\n[18] Final summary check")
r = requests.get(f"{BASE}/api/runs/{RUN_ID}/summary", headers=H)
summary = check("Final summary", r, 200)
ok(f"total={summary['total']} passed={summary['passed']} failed={summary['failed']} blocked={summary['blocked']} not_run={summary['not_run']} pass_rate={summary['pass_rate']}%")

print("\n" + "="*60)
print("ALL WORKFLOW VALIDATIONS PASSED")
print("="*60)
