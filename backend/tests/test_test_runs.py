"""
Phase 7 — Test Run and Test Result API tests.

Each test class is self-contained: creates its own project, suite, test cases, and runs.
No seed-data dependency. No ordering dependency.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, ProjectStatus, TestCaseStatus, TestCasePriority
from app.models.project import Project
from app.models.test_suite import TestSuite
from app.models.test_case import TestCase
from tests.conftest import make_user, auth_headers


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_project(db: Session, key: str, status: ProjectStatus = ProjectStatus.ACTIVE) -> Project:
    owner = make_user(db, f"owner_{key.lower()}@example.com", role=UserRole.ADMIN)
    p = Project(name=f"Project {key}", key=key, created_by=owner.id, status=status)
    db.add(p)
    db.flush()
    return p


def _make_suite(db: Session, project: Project) -> TestSuite:
    owner = make_user(db, f"suite_{project.key.lower()}@example.com", role=UserRole.ADMIN)
    s = TestSuite(project_id=project.id, name="Suite", created_by=owner.id)
    db.add(s)
    db.flush()
    return s


def _make_ready_case(db: Session, suite: TestSuite, suffix: str = "") -> TestCase:
    owner = make_user(db, f"tc_{suite.id}_{suffix}@example.com", role=UserRole.ADMIN)
    tc = TestCase(
        suite_id=suite.id,
        title=f"Ready Case {suffix}",
        expected_result="Pass",
        priority=TestCasePriority.MEDIUM,
        status=TestCaseStatus.READY,
        created_by=owner.id,
    )
    db.add(tc)
    db.flush()
    return tc


def _make_draft_case(db: Session, suite: TestSuite, suffix: str = "") -> TestCase:
    owner = make_user(db, f"draft_{suite.id}_{suffix}@example.com", role=UserRole.ADMIN)
    tc = TestCase(
        suite_id=suite.id,
        title=f"Draft Case {suffix}",
        expected_result="Pass",
        priority=TestCasePriority.LOW,
        status=TestCaseStatus.DRAFT,
        created_by=owner.id,
    )
    db.add(tc)
    db.flush()
    return tc


def _make_deprecated_case(db: Session, suite: TestSuite, suffix: str = "") -> TestCase:
    owner = make_user(db, f"dep_{suite.id}_{suffix}@example.com", role=UserRole.ADMIN)
    tc = TestCase(
        suite_id=suite.id,
        title=f"Deprecated Case {suffix}",
        expected_result="Pass",
        priority=TestCasePriority.LOW,
        status=TestCaseStatus.DEPRECATED,
        created_by=owner.id,
    )
    db.add(tc)
    db.flush()
    return tc


def _create_run(client: TestClient, headers: dict, project_id: int, tc_ids: list[int],
                name: str = "Run", env: str = "QA") -> dict:
    resp = client.post(
        f"/api/projects/{project_id}/runs",
        json={"name": name, "environment": env, "test_case_ids": tc_ids},
        headers=headers,
    )
    return resp


def _start_run(client: TestClient, headers: dict, run_id: int):
    return client.post(f"/api/runs/{run_id}/start", headers=headers)


def _record(client: TestClient, headers: dict, run_id: int, result_id: int,
            status: str = "PASSED", actual: str | None = "Looks good"):
    return client.put(
        f"/api/runs/{run_id}/results/{result_id}",
        json={"status": status, "actual_result": actual},
        headers=headers,
    )


# ===========================================================================
# Test Run Creation
# ===========================================================================

class TestRunCreation:
    def test_admin_creates_run(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "a")
        resp = _create_run(client, auth_headers(admin), p.id, [tc.id])
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "NOT_STARTED"
        assert body["project_id"] == p.id

    def test_qa_engineer_creates_run(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_cr2@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "CR2")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "b")
        resp = _create_run(client, auth_headers(qa), p.id, [tc.id])
        assert resp.status_code == 201

    def test_viewer_cannot_create_run(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_cr3@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "CR3")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "c")
        resp = _create_run(client, auth_headers(viewer), p.id, [tc.id])
        assert resp.status_code == 403

    def test_archived_project_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr4@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR4", status=ProjectStatus.ARCHIVED)
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "d")
        resp = _create_run(client, auth_headers(admin), p.id, [tc.id])
        assert resp.status_code == 400

    def test_missing_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr5@example.com", role=UserRole.ADMIN)
        resp = _create_run(client, auth_headers(admin), 999999, [1])
        assert resp.status_code == 404

    def test_missing_test_case_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr6@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR6")
        resp = _create_run(client, auth_headers(admin), p.id, [999999])
        assert resp.status_code == 400

    def test_test_case_from_another_project_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr7@example.com", role=UserRole.ADMIN)
        p_a = _make_project(db, "CR7A")
        p_b = _make_project(db, "CR7B")
        s_b = _make_suite(db, p_b)
        tc_b = _make_ready_case(db, s_b, "x")
        # Try to add project B's test case to project A's run
        resp = _create_run(client, auth_headers(admin), p_a.id, [tc_b.id])
        assert resp.status_code == 400

    def test_draft_test_case_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr8@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR8")
        s = _make_suite(db, p)
        tc = _make_draft_case(db, s, "e")
        resp = _create_run(client, auth_headers(admin), p.id, [tc.id])
        assert resp.status_code == 400

    def test_deprecated_test_case_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr9@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR9")
        s = _make_suite(db, p)
        tc = _make_deprecated_case(db, s, "f")
        resp = _create_run(client, auth_headers(admin), p.id, [tc.id])
        assert resp.status_code == 400

    def test_duplicate_test_case_ids_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr10@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR10")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "g")
        resp = _create_run(client, auth_headers(admin), p.id, [tc.id, tc.id])
        assert resp.status_code == 422

    def test_empty_test_case_list_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr11@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR11")
        resp = client.post(
            f"/api/projects/{p.id}/runs",
            json={"name": "Empty", "environment": "QA", "test_case_ids": []},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_initial_not_run_results_created(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr12@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR12")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "h1")
        tc2 = _make_ready_case(db, s, "h2")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id]).json()
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        assert results["total"] == 2
        for r in results["items"]:
            assert r["status"] == "NOT_RUN"
            assert r["executed_by"] is None
            assert r["executed_at"] is None

    def test_created_by_from_authenticated_user(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr13@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR13")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "i")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        assert run["created_by"] == admin.id

    def test_atomic_rollback_on_invalid_case(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_cr14@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "CR14")
        s = _make_suite(db, p)
        tc_good = _make_ready_case(db, s, "j1")
        # Mix valid + invalid — entire request must fail
        resp = _create_run(client, auth_headers(admin), p.id, [tc_good.id, 999998])
        assert resp.status_code == 400
        # No run should exist for this project
        runs = client.get(f"/api/projects/{p.id}/runs", headers=auth_headers(admin)).json()
        assert runs["total"] == 0


# ===========================================================================
# State Transitions
# ===========================================================================

class TestRunStateTransitions:
    def _setup(self, db: Session, key: str, admin_email: str):
        admin = make_user(db, admin_email, role=UserRole.ADMIN)
        p = _make_project(db, key)
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, key.lower())
        return admin, p, s, tc

    def test_not_started_to_in_progress(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST1", "admin_st1@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        resp = _start_run(client, auth_headers(admin), run["id"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"
        assert resp.json()["started_at"] is not None

    def test_in_progress_to_completed(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST2", "admin_st2@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        _record(client, auth_headers(admin), run["id"], results["items"][0]["id"])
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETED"
        assert resp.json()["completed_at"] is not None

    def test_in_progress_to_aborted(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST3", "admin_st3@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        resp = client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ABORTED"

    def test_cannot_complete_not_started(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST4", "admin_st4@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 409

    def test_cannot_start_in_progress(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST5", "admin_st5@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        resp = _start_run(client, auth_headers(admin), run["id"])
        assert resp.status_code == 409

    def test_cannot_start_completed(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST6", "admin_st6@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        _record(client, auth_headers(admin), run["id"], results["items"][0]["id"])
        client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        resp = _start_run(client, auth_headers(admin), run["id"])
        assert resp.status_code == 409

    def test_cannot_abort_not_started(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST7", "admin_st7@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        resp = client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(admin))
        assert resp.status_code == 409

    def test_cannot_restart_aborted(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST8", "admin_st8@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(admin))
        resp = _start_run(client, auth_headers(admin), run["id"])
        assert resp.status_code == 409

    def test_cannot_complete_aborted(self, client: TestClient, db: Session):
        admin, p, s, tc = self._setup(db, "ST9", "admin_st9@example.com")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(admin))
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 409


# ===========================================================================
# Test Results
# ===========================================================================

class TestResultRecording:
    def _run_in_progress(self, client, db, key, email):
        admin = make_user(db, email, role=UserRole.ADMIN)
        p = _make_project(db, key)
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, key.lower())
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        return admin, run, results["items"][0]

    def test_record_passed(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR1", "admin_rr1@example.com")
        resp = _record(client, auth_headers(admin), run["id"], result["id"], "PASSED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "PASSED"

    def test_record_failed(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR2", "admin_rr2@example.com")
        resp = _record(client, auth_headers(admin), run["id"], result["id"], "FAILED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "FAILED"

    def test_record_blocked(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR3", "admin_rr3@example.com")
        resp = _record(client, auth_headers(admin), run["id"], result["id"], "BLOCKED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "BLOCKED"

    def test_executed_by_set_from_auth_user(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR4", "admin_rr4@example.com")
        resp = _record(client, auth_headers(admin), run["id"], result["id"])
        assert resp.json()["executed_by"] == admin.id

    def test_executed_at_set_by_server(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR5", "admin_rr5@example.com")
        resp = _record(client, auth_headers(admin), run["id"], result["id"])
        assert resp.json()["executed_at"] is not None

    def test_viewer_cannot_update_result(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR6", "admin_rr6@example.com")
        viewer = make_user(db, "viewer_rr6@example.com", role=UserRole.VIEWER)
        resp = _record(client, auth_headers(viewer), run["id"], result["id"])
        assert resp.status_code == 403

    def test_result_cannot_be_updated_after_completion(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR7", "admin_rr7@example.com")
        _record(client, auth_headers(admin), run["id"], result["id"], "PASSED")
        client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        resp = _record(client, auth_headers(admin), run["id"], result["id"], "FAILED")
        assert resp.status_code == 409

    def test_result_cannot_be_updated_after_abort(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR8", "admin_rr8@example.com")
        client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(admin))
        resp = _record(client, auth_headers(admin), run["id"], result["id"], "PASSED")
        assert resp.status_code == 409

    def test_invalid_status_rejected(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR9", "admin_rr9@example.com")
        resp = client.put(
            f"/api/runs/{run['id']}/results/{result['id']}",
            json={"status": "UNKNOWN"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_not_run_status_rejected(self, client: TestClient, db: Session):
        admin, run, result = self._run_in_progress(client, db, "RR10", "admin_rr10@example.com")
        resp = client.put(
            f"/api/runs/{run['id']}/results/{result['id']}",
            json={"status": "NOT_RUN"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_result_belongs_to_different_run_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_rr11@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "RR11")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "r11a")
        tc2 = _make_ready_case(db, s, "r11b")
        run1 = _create_run(client, auth_headers(admin), p.id, [tc1.id]).json()
        run2 = _create_run(client, auth_headers(admin), p.id, [tc2.id]).json()
        _start_run(client, auth_headers(admin), run1["id"])
        _start_run(client, auth_headers(admin), run2["id"])
        # Get result from run2
        results2 = client.get(f"/api/runs/{run2['id']}/results", headers=auth_headers(admin)).json()
        result2_id = results2["items"][0]["id"]
        # Try to update run2's result via run1's endpoint
        resp = _record(client, auth_headers(admin), run1["id"], result2_id)
        assert resp.status_code == 404


# ===========================================================================
# Completion Rules
# ===========================================================================

class TestCompletionRules:
    def test_cannot_complete_with_not_run_results(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_comp1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "COMP1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "c1")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        # Do NOT record result — still NOT_RUN
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 409

    def test_completes_when_all_results_terminal(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_comp2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "COMP2")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "c2a")
        tc2 = _make_ready_case(db, s, "c2b")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        for r in results["items"]:
            _record(client, auth_headers(admin), run["id"], r["id"], "PASSED")
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETED"

    def test_partial_results_block_completion(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_comp3@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "COMP3")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "c3a")
        tc2 = _make_ready_case(db, s, "c3b")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        # Record only one of two
        _record(client, auth_headers(admin), run["id"], results["items"][0]["id"], "PASSED")
        resp = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin))
        assert resp.status_code == 409


# ===========================================================================
# Summary
# ===========================================================================

class TestRunSummary:
    def test_summary_calculates_totals(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_sum1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "SUM1")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "s1a")
        tc2 = _make_ready_case(db, s, "s1b")
        tc3 = _make_ready_case(db, s, "s1c")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id, tc3.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        ids = [r["id"] for r in results["items"]]
        _record(client, auth_headers(admin), run["id"], ids[0], "PASSED")
        _record(client, auth_headers(admin), run["id"], ids[1], "FAILED")
        _record(client, auth_headers(admin), run["id"], ids[2], "BLOCKED")
        summary = client.get(f"/api/runs/{run['id']}/summary", headers=auth_headers(admin)).json()
        assert summary["total"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["blocked"] == 1
        assert summary["not_run"] == 0

    def test_summary_calculates_pass_rate(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_sum2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "SUM2")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "s2a")
        tc2 = _make_ready_case(db, s, "s2b")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        ids = [r["id"] for r in results["items"]]
        _record(client, auth_headers(admin), run["id"], ids[0], "PASSED")
        _record(client, auth_headers(admin), run["id"], ids[1], "FAILED")
        summary = client.get(f"/api/runs/{run['id']}/summary", headers=auth_headers(admin)).json()
        assert summary["pass_rate"] == 50.0

    def test_summary_not_run_included(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_sum3@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "SUM3")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "s3a")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        summary = client.get(f"/api/runs/{run['id']}/summary", headers=auth_headers(admin)).json()
        assert summary["total"] == 1
        assert summary["not_run"] == 1
        assert summary["pass_rate"] == 0.0

    def test_summary_zero_total_no_division_error(self, client: TestClient, db: Session):
        # Edge case: run with results all NOT_RUN, pass_rate should be 0.0 not error
        admin = make_user(db, "admin_sum4@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "SUM4")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "s4a")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        summary = client.get(f"/api/runs/{run['id']}/summary", headers=auth_headers(admin)).json()
        assert summary["pass_rate"] == 0.0

    def test_viewer_can_read_summary(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_sum5@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_sum5@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "SUM5")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "s5a")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        resp = client.get(f"/api/runs/{run['id']}/summary", headers=auth_headers(viewer))
        assert resp.status_code == 200


# ===========================================================================
# List, Detail, RBAC
# ===========================================================================

class TestRunListAndDetail:
    def test_list_runs_for_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_lst1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "LST1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "l1")
        _create_run(client, auth_headers(admin), p.id, [tc.id], name="Run A")
        _create_run(client, auth_headers(admin), p.id, [tc.id], name="Run B")
        resp = client.get(f"/api/projects/{p.id}/runs", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert "items" in body
        assert "pages" in body

    def test_list_runs_filter_by_status(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_lst2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "LST2")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "l2")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        resp = client.get(f"/api/projects/{p.id}/runs?status=IN_PROGRESS", headers=auth_headers(admin))
        assert resp.status_code == 200
        for r in resp.json()["items"]:
            assert r["status"] == "IN_PROGRESS"

    def test_list_runs_search_by_name(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_lst3@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "LST3")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "l3")
        _create_run(client, auth_headers(admin), p.id, [tc.id], name="Regression Run")
        _create_run(client, auth_headers(admin), p.id, [tc.id], name="Smoke Run")
        resp = client.get(f"/api/projects/{p.id}/runs?search=Regression", headers=auth_headers(admin))
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["items"]]
        assert "Regression Run" in names
        assert "Smoke Run" not in names

    def test_get_run_detail(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_det1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DET1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "d1")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id], name="Detail Run", env="STAGING").json()
        resp = client.get(f"/api/runs/{run['id']}", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Detail Run"
        assert body["environment"] == "STAGING"
        assert body["project_id"] == p.id

    def test_get_nonexistent_run_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_det2@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/runs/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_viewer_can_list_runs(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_rbac1@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_rbac1@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "RBAC1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "rb1")
        _create_run(client, auth_headers(admin), p.id, [tc.id])
        resp = client.get(f"/api/projects/{p.id}/runs", headers=auth_headers(viewer))
        assert resp.status_code == 200

    def test_viewer_cannot_start_run(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_rbac2@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_rbac2@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "RBAC2")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "rb2")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        resp = _start_run(client, auth_headers(viewer), run["id"])
        assert resp.status_code == 403

    def test_viewer_cannot_abort_run(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_rbac3@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_rbac3@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "RBAC3")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "rb3")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        resp = client.post(f"/api/runs/{run['id']}/abort", headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_unauthenticated_get_run_returns_401(self, client: TestClient, db: Session):
        resp = client.get("/api/runs/1")
        assert resp.status_code == 401

    def test_list_results_includes_test_case_info(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_res1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "RES1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "res1")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        assert results["total"] == 1
        item = results["items"][0]
        assert item["test_case"] is not None
        assert item["test_case"]["id"] == tc.id
        assert "title" in item["test_case"]

    def test_list_results_filter_by_status(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_res2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "RES2")
        s = _make_suite(db, p)
        tc1 = _make_ready_case(db, s, "res2a")
        tc2 = _make_ready_case(db, s, "res2b")
        run = _create_run(client, auth_headers(admin), p.id, [tc1.id, tc2.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        ids = [r["id"] for r in results["items"]]
        _record(client, auth_headers(admin), run["id"], ids[0], "PASSED")
        # Filter for PASSED only
        resp = client.get(f"/api/runs/{run['id']}/results?status=PASSED", headers=auth_headers(admin))
        assert resp.status_code == 200
        for r in resp.json()["items"]:
            assert r["status"] == "PASSED"

    def test_started_at_server_generated(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_ts1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "TS1")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "ts1")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        assert run["started_at"] is None
        started = _start_run(client, auth_headers(admin), run["id"]).json()
        assert started["started_at"] is not None

    def test_completed_at_server_generated(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_ts2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "TS2")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "ts2")
        run = _create_run(client, auth_headers(admin), p.id, [tc.id]).json()
        _start_run(client, auth_headers(admin), run["id"])
        results = client.get(f"/api/runs/{run['id']}/results", headers=auth_headers(admin)).json()
        _record(client, auth_headers(admin), run["id"], results["items"][0]["id"], "PASSED")
        completed = client.post(f"/api/runs/{run['id']}/complete", headers=auth_headers(admin)).json()
        assert completed["completed_at"] is not None
