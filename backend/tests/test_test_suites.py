import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, ProjectStatus
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_result import TestResult
from app.models.enums import TestCasePriority, TestCaseStatus, TestResultStatus
from tests.conftest import make_user, auth_headers


@pytest.fixture
def active_project(db: Session) -> Project:
    admin = make_user(db, "proj_owner@example.com", role=UserRole.ADMIN)
    p = Project(name="Suite Project", key="SUITEPROJ", created_by=admin.id, status=ProjectStatus.ACTIVE)
    db.add(p)
    db.flush()
    return p


@pytest.fixture
def archived_project(db: Session) -> Project:
    admin = make_user(db, "proj_arch_owner@example.com", role=UserRole.ADMIN)
    p = Project(name="Arch Project", key="ARCHPROJ", created_by=admin.id, status=ProjectStatus.ARCHIVED)
    db.add(p)
    db.flush()
    return p


# ===========================================================================
# Test Suite Endpoints Tests
# ===========================================================================

class TestTestSuiteCRUD:
    def test_admin_creates_suite_returns_201(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_suite@example.com", role=UserRole.ADMIN)
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Smoke Suite", "description": "Smoke tests"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Smoke Suite"
        assert body["description"] == "Smoke tests"
        assert body["project_id"] == active_project.id
        assert body["created_by"] == admin.id
        assert "id" in body

    def test_qa_engineer_creates_suite(self, client: TestClient, db: Session, active_project: Project):
        qa = make_user(db, "qa_suite@example.com", role=UserRole.QA_ENGINEER)
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "QA Suite"},
            headers=auth_headers(qa),
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "QA Suite"

    def test_viewer_cannot_create(self, client: TestClient, db: Session, active_project: Project):
        viewer = make_user(db, "viewer_suite@example.com", role=UserRole.VIEWER)
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Viewer Suite"},
            headers=auth_headers(viewer),
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_returns_401(self, client: TestClient, active_project: Project):
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "No Auth Suite"},
        )
        assert resp.status_code == 401

    def test_viewer_can_read_suite_details(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_read_suite@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_read_suite@example.com", role=UserRole.VIEWER)
        
        # Create a suite
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Read Suite"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        # Read as viewer
        r_resp = client.get(f"/api/suites/{suite_id}", headers=auth_headers(viewer))
        assert r_resp.status_code == 200
        assert r_resp.json()["name"] == "Read Suite"

    def test_suite_retrieval_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_suite_404@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/suites/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_admin_updates_suite(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_up_suite@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Old Suite"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        # Update
        u_resp = client.put(
            f"/api/suites/{suite_id}",
            json={"name": "New Suite", "description": "Updated"},
            headers=auth_headers(admin),
        )
        assert u_resp.status_code == 200
        body = u_resp.json()
        assert body["name"] == "New Suite"
        assert body["description"] == "Updated"

    def test_qa_engineer_updates_suite(self, client: TestClient, db: Session, active_project: Project):
        qa = make_user(db, "qa_up_suite@example.com", role=UserRole.QA_ENGINEER)
        admin = make_user(db, "admin_up_suite2@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Old QA Suite"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        u_resp = client.put(
            f"/api/suites/{suite_id}",
            json={"name": "Updated QA Suite"},
            headers=auth_headers(qa),
        )
        assert u_resp.status_code == 200
        assert u_resp.json()["name"] == "Updated QA Suite"

    def test_viewer_cannot_update(self, client: TestClient, db: Session, active_project: Project):
        viewer = make_user(db, "viewer_no_up@example.com", role=UserRole.VIEWER)
        admin = make_user(db, "admin_no_up@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "Fixed Suite"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        u_resp = client.put(
            f"/api/suites/{suite_id}",
            json={"name": "Hacked Name"},
            headers=auth_headers(viewer),
        )
        assert u_resp.status_code == 403

    def test_delete_behavior(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_del_suite@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "To Delete"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        # Delete
        d_resp = client.delete(f"/api/suites/{suite_id}", headers=auth_headers(admin))
        assert d_resp.status_code == 204

        # Verify gone
        get_resp = client.get(f"/api/suites/{suite_id}", headers=auth_headers(admin))
        assert get_resp.status_code == 404

    def test_delete_blocked_when_test_cases_have_history(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_del_block@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "History Suite"},
            headers=auth_headers(admin),
        )
        suite_id = c_resp.json()["id"]

        # Add a test case and a test result (historical data) to block deletion
        tc = TestCase(
            suite_id=suite_id,
            title="TestCase with History",
            expected_result="Pass",
            priority=TestCasePriority.MEDIUM,
            status=TestCaseStatus.READY,
            created_by=admin.id,
        )
        db.add(tc)
        db.flush()

        # Create a valid TestRun to satisfy FK constraints
        from app.models.test_run import TestRun
        trun = TestRun(
            project_id=active_project.id,
            name="Block Delete Run",
            environment="staging",
            created_by=admin.id,
        )
        db.add(trun)
        db.flush()

        tr = TestResult(
            test_run_id=trun.id,
            test_case_id=tc.id,
            status=TestResultStatus.PASSED,
            executed_by=admin.id,
        )
        db.add(tr)
        db.flush()

        # Delete should be blocked with 409 Conflict
        d_resp = client.delete(f"/api/suites/{suite_id}", headers=auth_headers(admin))
        assert d_resp.status_code == 409
        assert "historical test results" in d_resp.json()["detail"]


# ===========================================================================
# Validation & Filtering Tests
# ===========================================================================

class TestTestSuiteValidation:
    def test_missing_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_mproj@example.com", role=UserRole.ADMIN)
        resp = client.post(
            "/api/projects/999999/suites",
            json={"name": "Invalid Project Suite"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_archived_project_returns_400(self, client: TestClient, db: Session, archived_project: Project):
        admin = make_user(db, "admin_archp@example.com", role=UserRole.ADMIN)
        resp = client.post(
            f"/api/projects/{archived_project.id}/suites",
            json={"name": "Archived Suite"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400
        assert "archived project" in resp.json()["detail"]

    def test_missing_name_returns_422(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_noname_s@example.com", role=UserRole.ADMIN)
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"description": "No Name"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_blank_name_returns_422(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_blankname_s@example.com", role=UserRole.ADMIN)
        resp = client.post(
            f"/api/projects/{active_project.id}/suites",
            json={"name": "   "},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422


class TestTestSuiteListFiltering:
    def test_list_suites_by_project(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_lsuites@example.com", role=UserRole.ADMIN)
        
        # Create suites
        client.post(f"/api/projects/{active_project.id}/suites", json={"name": "Suite A"}, headers=auth_headers(admin))
        client.post(f"/api/projects/{active_project.id}/suites", json={"name": "Suite B"}, headers=auth_headers(admin))

        resp = client.get(f"/api/projects/{active_project.id}/suites", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        names = [s["name"] for s in body["items"]]
        assert "Suite A" in names
        assert "Suite B" in names

    def test_list_suites_pagination(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_pgsuites@example.com", role=UserRole.ADMIN)
        for i in range(5):
            client.post(f"/api/projects/{active_project.id}/suites", json={"name": f"Suite {i}"}, headers=auth_headers(admin))

        resp = client.get(f"/api/projects/{active_project.id}/suites?page=1&page_size=3", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 3
        assert body["page_size"] == 3
        assert body["page"] == 1

    def test_list_suites_search(self, client: TestClient, db: Session, active_project: Project):
        admin = make_user(db, "admin_srchsuite@example.com", role=UserRole.ADMIN)
        client.post(f"/api/projects/{active_project.id}/suites", json={"name": "Target Search Suite"}, headers=auth_headers(admin))
        client.post(f"/api/projects/{active_project.id}/suites", json={"name": "Other Suite"}, headers=auth_headers(admin))

        resp = client.get(f"/api/projects/{active_project.id}/suites?search=Target Search", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        names = [s["name"] for s in body["items"]]
        assert "Target Search Suite" in names
        assert "Other Suite" not in names
