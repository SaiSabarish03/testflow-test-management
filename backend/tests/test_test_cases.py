import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, ProjectStatus, TestCasePriority, TestCaseStatus
from app.models.project import Project
from app.models.test_suite import TestSuite
from tests.conftest import make_user, auth_headers


@pytest.fixture
def active_project(db: Session) -> Project:
    admin = make_user(db, "tc_proj_owner@example.com", role=UserRole.ADMIN)
    p = Project(name="TC Project", key="TCPROJ", created_by=admin.id, status=ProjectStatus.ACTIVE)
    db.add(p)
    db.flush()
    return p


@pytest.fixture
def archived_project(db: Session) -> Project:
    admin = make_user(db, "tc_arch_owner@example.com", role=UserRole.ADMIN)
    p = Project(name="TC Arch Project", key="TCARCHPROJ", created_by=admin.id, status=ProjectStatus.ARCHIVED)
    db.add(p)
    db.flush()
    return p


@pytest.fixture
def test_suite(db: Session, active_project: Project) -> TestSuite:
    admin = make_user(db, "tc_suite_owner@example.com", role=UserRole.ADMIN)
    s = TestSuite(project_id=active_project.id, name="TC Suite", created_by=admin.id)
    db.add(s)
    db.flush()
    return s


@pytest.fixture
def arch_test_suite(db: Session, archived_project: Project) -> TestSuite:
    admin = make_user(db, "tc_arch_suite_owner@example.com", role=UserRole.ADMIN)
    s = TestSuite(project_id=archived_project.id, name="Arch TC Suite", created_by=admin.id)
    db.add(s)
    db.flush()
    return s


# ===========================================================================
# Test Case CRUD & RBAC Tests
# ===========================================================================

class TestTestCaseCRUD:
    def test_admin_creates_test_case_returns_201(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_tc@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Validate Admin Create",
            "expected_result": "Success",
            "priority": "HIGH",
            "status": "DRAFT",
            "steps": [{"order": 1, "action": "Click login"}],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Validate Admin Create"
        assert body["expected_result"] == "Success"
        assert body["priority"] == "HIGH"
        assert body["status"] == "DRAFT"
        assert body["suite_id"] == test_suite.id
        assert body["created_by"] == admin.id
        assert "id" in body

    def test_qa_engineer_creates_test_case(self, client: TestClient, db: Session, test_suite: TestSuite):
        qa = make_user(db, "qa_tc@example.com", role=UserRole.QA_ENGINEER)
        payload = {
            "title": "Validate QA Create",
            "expected_result": "Works",
            "priority": "LOW",
            "status": "DRAFT",
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(qa),
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Validate QA Create"

    def test_viewer_cannot_create_test_case(self, client: TestClient, db: Session, test_suite: TestSuite):
        viewer = make_user(db, "viewer_tc@example.com", role=UserRole.VIEWER)
        payload = {
            "title": "Hacker title",
            "expected_result": "Hack",
            "priority": "CRITICAL",
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(viewer),
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_returns_401(self, client: TestClient, test_suite: TestSuite):
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "No Auth", "expected_result": "Fail", "priority": "LOW"},
        )
        assert resp.status_code == 401

    def test_viewer_can_read_test_case(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_vread_tc@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_vread_tc@example.com", role=UserRole.VIEWER)
        
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Read Me", "expected_result": "Success", "priority": "MEDIUM"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        r_resp = client.get(f"/api/test-cases/{tc_id}", headers=auth_headers(viewer))
        assert r_resp.status_code == 200
        assert r_resp.json()["title"] == "Read Me"

    def test_nonexistent_test_case_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_tc_404@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/test-cases/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_update_test_case(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_up_tc@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Original Title", "expected_result": "Success", "priority": "MEDIUM"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update
        u_resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"title": "Updated Title", "priority": "CRITICAL"},
            headers=auth_headers(admin),
        )
        assert u_resp.status_code == 200
        body = u_resp.json()
        assert body["title"] == "Updated Title"
        assert body["priority"] == "CRITICAL"

    def test_viewer_cannot_update_test_case(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_vup_tc@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_vup_tc@example.com", role=UserRole.VIEWER)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Protect Me", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"title": "Hacked Title"},
            headers=auth_headers(viewer),
        )
        assert resp.status_code == 403

    def test_delete_deprecation_behavior(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_del_tc@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "To Deprecate", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Delete (should set status = DEPRECATED)
        d_resp = client.delete(f"/api/test-cases/{tc_id}", headers=auth_headers(admin))
        assert d_resp.status_code == 200
        assert d_resp.json()["status"] == "DEPRECATED"

        # Verify still retrievable
        r_resp = client.get(f"/api/test-cases/{tc_id}", headers=auth_headers(admin))
        assert r_resp.status_code == 200
        assert r_resp.json()["status"] == "DEPRECATED"


# ===========================================================================
# Validation Tests
# ===========================================================================

class TestTestCaseValidation:
    def test_valid_draft_without_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_draft@example.com", role=UserRole.ADMIN)
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Draft TC", "expected_result": "Passed", "priority": "LOW", "status": "DRAFT"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "DRAFT"

    def test_valid_ready_with_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_ready_ok@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Ready TC",
            "expected_result": "Success",
            "priority": "HIGH",
            "status": "READY",
            "steps": [{"order": 1, "action": "Click button"}],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "READY"

    def test_invalid_ready_without_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_ready_bad@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Ready TC",
            "expected_result": "Success",
            "priority": "HIGH",
            "status": "READY",
            "steps": [],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_invalid_ready_without_expected_result(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_ready_no_exp@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Ready TC",
            "expected_result": "   ",
            "priority": "HIGH",
            "status": "READY",
            "steps": [{"order": 1, "action": "Step A"}],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_invalid_step_structure_order_negative(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_step_neg@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Invalid Step Order",
            "expected_result": "Fail",
            "priority": "LOW",
            "steps": [{"order": -1, "action": "Negative order"}],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_duplicate_step_order_returns_422(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_step_dup@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Duplicate Step Order",
            "expected_result": "Fail",
            "priority": "LOW",
            "steps": [
                {"order": 1, "action": "First"},
                {"order": 1, "action": "Duplicate"},
            ],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_blank_step_action_returns_422(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_step_blank@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Blank Step Action",
            "expected_result": "Fail",
            "priority": "LOW",
            "steps": [{"order": 1, "action": "   "}],
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_invalid_priority_returns_422(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_bad_prio@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Bad Prio",
            "expected_result": "Fail",
            "priority": "SUPERHIGH",
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_invalid_status_returns_422(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_bad_stat@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Bad Stat",
            "expected_result": "Fail",
            "priority": "LOW",
            "status": "APPROVED",
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_missing_suite_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_msuite@example.com", role=UserRole.ADMIN)
        payload = {"title": "No Suite", "expected_result": "Fail", "priority": "LOW"}
        resp = client.post(
            "/api/suites/999999/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_archived_project_blocks_test_case_creation(self, client: TestClient, db: Session, arch_test_suite: TestSuite):
        admin = make_user(db, "admin_arch_tc@example.com", role=UserRole.ADMIN)
        payload = {"title": "Archived Proj Case", "expected_result": "Fail", "priority": "LOW"}
        resp = client.post(
            f"/api/suites/{arch_test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400
        assert "archived project" in resp.json()["detail"]


# ===========================================================================
# Listing, Filtering & Pagination Tests
# ===========================================================================

class TestTestCaseListAndFiltering:
    def test_list_test_cases_by_suite(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_list_tc@example.com", role=UserRole.ADMIN)
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Case A", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Case B", "expected_result": "Pass", "priority": "HIGH"},
            headers=auth_headers(admin),
        )

        resp = client.get(f"/api/suites/{test_suite.id}/test-cases", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        titles = [tc["title"] for tc in body["items"]]
        assert "Case A" in titles
        assert "Case B" in titles

    def test_search_test_cases(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_srch_tc@example.com", role=UserRole.ADMIN)
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "SearchTarget", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "IgnoredCase", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )

        resp = client.get(f"/api/suites/{test_suite.id}/test-cases?search=SearchTarget", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        titles = [tc["title"] for tc in body["items"]]
        assert "SearchTarget" in titles
        assert "IgnoredCase" not in titles

    def test_filter_by_priority(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_prio_tc@example.com", role=UserRole.ADMIN)
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Critical Case", "expected_result": "Pass", "priority": "CRITICAL"},
            headers=auth_headers(admin),
        )
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Low Case", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )

        resp = client.get(f"/api/suites/{test_suite.id}/test-cases?priority=CRITICAL", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        for tc in body["items"]:
            assert tc["priority"] == "CRITICAL"

    def test_filter_by_status(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_stat_tc@example.com", role=UserRole.ADMIN)
        # Create draft
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Draft Case", "expected_result": "Pass", "priority": "LOW", "status": "DRAFT"},
            headers=auth_headers(admin),
        )
        # Create ready
        client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Ready Case", "expected_result": "Pass", "priority": "LOW", "status": "READY", "steps": [{"order": 1, "action": "A"}]},
            headers=auth_headers(admin),
        )

        resp = client.get(f"/api/suites/{test_suite.id}/test-cases?status=READY", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        for tc in body["items"]:
            assert tc["status"] == "READY"

    def test_pagination(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "admin_pg_tc@example.com", role=UserRole.ADMIN)
        for i in range(4):
            client.post(
                f"/api/suites/{test_suite.id}/test-cases",
                json={"title": f"Case {i}", "expected_result": "Pass", "priority": "LOW"},
                headers=auth_headers(admin),
            )

        resp = client.get(f"/api/suites/{test_suite.id}/test-cases?page=2&page_size=2", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert len(body["items"]) <= 2


# ===========================================================================
# Step Serialization and Status Validation Tests
# ===========================================================================

class TestTestCaseStepsEndToEnd:
    def test_create_test_case_with_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_create@example.com", role=UserRole.ADMIN)
        payload = {
            "title": "Create case with steps",
            "expected_result": "Success",
            "priority": "HIGH",
            "status": "DRAFT",
            "steps": [
                {"order": 1, "action": "Enter valid email and password"},
                {"order": 2, "action": "Click login"}
            ]
        }
        resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["steps"]) == 2
        assert body["steps"][0]["order"] == 1
        assert body["steps"][0]["action"] == "Enter valid email and password"
        assert body["steps"][1]["order"] == 2
        assert body["steps"][1]["action"] == "Click login"

    def test_update_validation_order_greater_than_zero(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_val_order@example.com", role=UserRole.ADMIN)
        # Create a test case first
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Original", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update with order = 0
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": [{"order": 0, "action": "Invalid order"}]},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_update_validation_unique_step_orders(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_val_uniq@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Original", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update with duplicate order
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": [{"order": 1, "action": "Step A"}, {"order": 1, "action": "Step B"}]},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_update_validation_non_blank_actions(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_val_blank@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Original", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update with blank action
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": [{"order": 1, "action": "   "}]},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_update_test_case_with_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_update_ok@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={"title": "Original", "expected_result": "Pass", "priority": "LOW"},
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update with steps
        payload = {
            "steps": [{"order": 1, "action": "Perform initial step"}]
        }
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json=payload,
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["steps"]) == 1
        assert body["steps"][0]["action"] == "Perform initial step"

        # Verify database persistence survives a fresh GET request
        get_resp = client.get(f"/api/test-cases/{tc_id}", headers=auth_headers(admin))
        assert get_resp.status_code == 200
        get_body = get_resp.json()
        assert len(get_body["steps"]) == 1
        assert get_body["steps"][0]["action"] == "Perform initial step"

    def test_update_test_case_without_changing_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_no_change@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={
                "title": "Original", 
                "expected_result": "Pass", 
                "priority": "LOW",
                "steps": [{"order": 1, "action": "Step A"}]
            },
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Update title only
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"title": "New Title"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "New Title"
        assert len(body["steps"]) == 1
        assert body["steps"][0]["action"] == "Step A"

    def test_replace_existing_steps(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_replace@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={
                "title": "Original", 
                "expected_result": "Pass", 
                "priority": "LOW",
                "steps": [{"order": 1, "action": "Step A"}]
            },
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Replace steps
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": [{"order": 1, "action": "Step X"}, {"order": 2, "action": "Step Y"}]},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["steps"]) == 2
        assert body["steps"][0]["action"] == "Step X"
        assert body["steps"][1]["action"] == "Step Y"

        # Verify survival of GET request
        get_resp = client.get(f"/api/test-cases/{tc_id}", headers=auth_headers(admin))
        assert get_resp.status_code == 200
        assert len(get_resp.json()["steps"]) == 2

    def test_remove_all_steps_while_draft(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_remove_draft@example.com", role=UserRole.ADMIN)
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={
                "title": "Original", 
                "expected_result": "Pass", 
                "priority": "LOW",
                "status": "DRAFT",
                "steps": [{"order": 1, "action": "Step A"}]
            },
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Remove steps
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": []},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["steps"] == []

        # Verify survival of GET request
        get_resp = client.get(f"/api/test-cases/{tc_id}", headers=auth_headers(admin))
        assert get_resp.status_code == 200
        assert get_resp.json()["steps"] == []

    def test_reject_ready_status_when_steps_are_missing(self, client: TestClient, db: Session, test_suite: TestSuite):
        admin = make_user(db, "steps_reject_ready@example.com", role=UserRole.ADMIN)
        
        # Test case with steps initially
        c_resp = client.post(
            f"/api/suites/{test_suite.id}/test-cases",
            json={
                "title": "Original", 
                "expected_result": "Pass", 
                "priority": "LOW",
                "status": "DRAFT",
                "steps": [{"order": 1, "action": "Step A"}]
            },
            headers=auth_headers(admin),
        )
        tc_id = c_resp.json()["id"]

        # Try to set status READY and remove steps at the same time
        resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"status": "READY", "steps": []},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422
        assert "steps" in resp.json()["detail"].lower()

        # Try to set status READY on a testcase that has no steps and not sending steps in payload
        # First, remove steps on the draft test case
        r_resp = client.put(
            f"/api/test-cases/{tc_id}",
            json={"steps": []},
            headers=auth_headers(admin),
        )
        assert r_resp.status_code == 200
        
        # Now try to set status READY without sending steps
        resp2 = client.put(
            f"/api/test-cases/{tc_id}",
            json={"status": "READY"},
            headers=auth_headers(admin),
        )
        assert resp2.status_code == 422
        assert "steps" in resp2.json()["detail"].lower()
