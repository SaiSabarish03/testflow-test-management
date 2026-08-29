"""
Phase 8 — Defect Management API tests.

Each test class is self-contained: creates its own users, projects, and test cases.
No seed-data dependency. No ordering dependency.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, UserStatus, ProjectStatus, TestCasePriority, TestCaseStatus
from app.models.project import Project
from app.models.test_suite import TestSuite
from app.models.test_case import TestCase
from tests.conftest import make_user, auth_headers


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_project(db: Session, key: str) -> Project:
    owner = make_user(db, f"owner_{key.lower()}@example.com", role=UserRole.ADMIN)
    p = Project(name=f"Project {key}", key=key, created_by=owner.id, status=ProjectStatus.ACTIVE)
    db.add(p)
    db.flush()
    return p


def _make_suite(db: Session, project: Project) -> TestSuite:
    owner = make_user(db, f"suite_owner_{project.key.lower()}@example.com", role=UserRole.ADMIN)
    s = TestSuite(project_id=project.id, name="Suite", created_by=owner.id)
    db.add(s)
    db.flush()
    return s


def _make_ready_case(db: Session, suite: TestSuite, suffix: str = "") -> TestCase:
    owner = make_user(db, f"tc_{suite.id}_{suffix}@example.com", role=UserRole.ADMIN)
    tc = TestCase(
        suite_id=suite.id,
        title=f"Case {suffix}",
        expected_result="Pass",
        priority=TestCasePriority.MEDIUM,
        status=TestCaseStatus.READY,
        created_by=owner.id,
    )
    db.add(tc)
    db.flush()
    return tc


def _create_defect(client, headers, project_id, **kwargs):
    payload = {
        "project_id": project_id,
        "title": kwargs.get("title", "Login button broken"),
        "severity": kwargs.get("severity", "MAJOR"),
        "priority": kwargs.get("priority", "HIGH"),
    }
    for k in ("test_case_id", "description", "environment", "assigned_to"):
        if k in kwargs:
            payload[k] = kwargs[k]
    return client.post("/api/defects", json=payload, headers=headers)


# ===========================================================================
# Creation
# ===========================================================================

class TestDefectCreation:
    def test_admin_creates_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC1")
        resp = _create_defect(client, auth_headers(admin), p.id)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "OPEN"
        assert body["project_id"] == p.id

    def test_qa_engineer_creates_defect(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_dc2@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "DC2")
        resp = _create_defect(client, auth_headers(qa), p.id)
        assert resp.status_code == 201

    def test_viewer_cannot_create_defect(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_dc3@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "DC3")
        resp = _create_defect(client, auth_headers(viewer), p.id)
        assert resp.status_code == 403

    def test_unauthenticated_creation_rejected(self, client: TestClient, db: Session):
        p = _make_project(db, "DC4")
        resp = _create_defect(client, {}, p.id)
        assert resp.status_code == 401

    def test_missing_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc5@example.com", role=UserRole.ADMIN)
        resp = _create_defect(client, auth_headers(admin), 999999)
        assert resp.status_code == 404

    def test_missing_title_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc6@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC6")
        resp = client.post(
            "/api/defects",
            json={"project_id": p.id, "severity": "MAJOR", "priority": "HIGH"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_invalid_severity_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc7@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC7")
        resp = _create_defect(client, auth_headers(admin), p.id, severity="EXTREME")
        assert resp.status_code == 422

    def test_invalid_priority_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc8@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC8")
        resp = _create_defect(client, auth_headers(admin), p.id, priority="URGENT")
        assert resp.status_code == 422

    def test_optional_test_case_omitted(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc9@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC9")
        resp = _create_defect(client, auth_headers(admin), p.id)
        assert resp.status_code == 201
        assert resp.json()["test_case_id"] is None

    def test_valid_test_case_association(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc10@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC10")
        s = _make_suite(db, p)
        tc = _make_ready_case(db, s, "dc10")
        resp = _create_defect(client, auth_headers(admin), p.id, test_case_id=tc.id)
        assert resp.status_code == 201
        assert resp.json()["test_case_id"] == tc.id

    def test_test_case_from_another_project_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc11@example.com", role=UserRole.ADMIN)
        p_a = _make_project(db, "DC11A")
        p_b = _make_project(db, "DC11B")
        s_b = _make_suite(db, p_b)
        tc_b = _make_ready_case(db, s_b, "dc11")
        resp = _create_defect(client, auth_headers(admin), p_a.id, test_case_id=tc_b.id)
        assert resp.status_code == 400

    def test_nonexistent_assignee_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc12@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC12")
        resp = _create_defect(client, auth_headers(admin), p.id, assigned_to=999999)
        assert resp.status_code == 404

    def test_inactive_assignee_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc13@example.com", role=UserRole.ADMIN)
        inactive = make_user(db, "inactive_dc13@example.com", role=UserRole.QA_ENGINEER,
                             status=UserStatus.INACTIVE)
        p = _make_project(db, "DC13")
        resp = _create_defect(client, auth_headers(admin), p.id, assigned_to=inactive.id)
        assert resp.status_code == 400

    def test_created_by_from_authenticated_user(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc14@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC14")
        resp = _create_defect(client, auth_headers(admin), p.id)
        assert resp.json()["created_by"] == admin.id

    def test_default_status_is_open(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dc15@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DC15")
        resp = _create_defect(client, auth_headers(admin), p.id)
        assert resp.json()["status"] == "OPEN"


# ===========================================================================
# Retrieval
# ===========================================================================

class TestDefectRetrieval:
    def _make_defect(self, client, db, key, email, role=UserRole.ADMIN):
        user = make_user(db, email, role=role)
        p = _make_project(db, key)
        resp = _create_defect(client, auth_headers(user), p.id)
        return user, p, resp.json()

    def test_admin_retrieves_defect(self, client: TestClient, db: Session):
        admin, p, d = self._make_defect(client, db, "DR1", "admin_dr1@example.com")
        resp = client.get(f"/api/defects/{d['id']}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["id"] == d["id"]

    def test_qa_engineer_retrieves_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr2a@example.com", role=UserRole.ADMIN)
        qa = make_user(db, "qa_dr2@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "DR2")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.get(f"/api/defects/{d['id']}", headers=auth_headers(qa))
        assert resp.status_code == 200

    def test_viewer_retrieves_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr3a@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_dr3@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "DR3")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.get(f"/api/defects/{d['id']}", headers=auth_headers(viewer))
        assert resp.status_code == 200

    def test_unauthenticated_retrieval_rejected(self, client: TestClient, db: Session):
        resp = client.get("/api/defects/1")
        assert resp.status_code == 401

    def test_nonexistent_defect_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr5@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/defects/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_list_defects(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr6@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR6")
        _create_defect(client, auth_headers(admin), p.id, title="Defect A")
        _create_defect(client, auth_headers(admin), p.id, title="Defect B")
        resp = client.get("/api/defects", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "pages" in body

    def test_pagination(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr7@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR7")
        for i in range(5):
            _create_defect(client, auth_headers(admin), p.id, title=f"Defect {i}")
        resp = client.get(
            f"/api/defects?project_id={p.id}&page=1&page_size=2",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2
        assert body["page_size"] == 2

    def test_search_by_title(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr8@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR8")
        _create_defect(client, auth_headers(admin), p.id, title="UniqueLoginBug")
        _create_defect(client, auth_headers(admin), p.id, title="Other Issue")
        resp = client.get(
            f"/api/defects?project_id={p.id}&search=UniqueLoginBug",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        titles = [d["title"] for d in resp.json()["items"]]
        assert "UniqueLoginBug" in titles
        assert "Other Issue" not in titles

    def test_filter_by_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr9@example.com", role=UserRole.ADMIN)
        p1 = _make_project(db, "DR9A")
        p2 = _make_project(db, "DR9B")
        _create_defect(client, auth_headers(admin), p1.id, title="P1 Defect")
        _create_defect(client, auth_headers(admin), p2.id, title="P2 Defect")
        resp = client.get(f"/api/defects?project_id={p1.id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        for d in resp.json()["items"]:
            assert d["project_id"] == p1.id

    def test_filter_by_severity(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr10@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR10")
        _create_defect(client, auth_headers(admin), p.id, severity="BLOCKER")
        _create_defect(client, auth_headers(admin), p.id, severity="TRIVIAL")
        resp = client.get(
            f"/api/defects?project_id={p.id}&severity=BLOCKER",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        for d in resp.json()["items"]:
            assert d["severity"] == "BLOCKER"

    def test_filter_by_priority(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr11@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR11")
        _create_defect(client, auth_headers(admin), p.id, priority="CRITICAL")
        _create_defect(client, auth_headers(admin), p.id, priority="LOW")
        resp = client.get(
            f"/api/defects?project_id={p.id}&priority=CRITICAL",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        for d in resp.json()["items"]:
            assert d["priority"] == "CRITICAL"

    def test_filter_by_status(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr12@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DR12")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        # Transition one to IN_PROGRESS
        client.put(
            f"/api/defects/{d['id']}",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(admin),
        )
        resp = client.get(
            f"/api/defects?project_id={p.id}&status=OPEN",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "OPEN"

    def test_filter_by_assignee(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dr13@example.com", role=UserRole.ADMIN)
        assignee = make_user(db, "assignee_dr13@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "DR13")
        _create_defect(client, auth_headers(admin), p.id, assigned_to=assignee.id)
        _create_defect(client, auth_headers(admin), p.id)
        resp = client.get(
            f"/api/defects?project_id={p.id}&assigned_to={assignee.id}",
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        for d in resp.json()["items"]:
            assert d["assigned_to"] == assignee.id


# ===========================================================================
# Update
# ===========================================================================

class TestDefectUpdate:
    def _setup(self, db, client, key, email, role=UserRole.ADMIN):
        user = make_user(db, email, role=role)
        p = _make_project(db, key)
        d = _create_defect(client, auth_headers(user), p.id).json()
        return user, p, d

    def test_admin_updates_defect(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU1", "admin_du1@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_qa_engineer_updates_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_du2a@example.com", role=UserRole.ADMIN)
        qa = make_user(db, "qa_du2@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "DU2")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"title": "QA Updated"},
            headers=auth_headers(qa),
        )
        assert resp.status_code == 200

    def test_viewer_cannot_update_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_du3a@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_du3@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "DU3")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"title": "Viewer Update"},
            headers=auth_headers(viewer),
        )
        assert resp.status_code == 403

    def test_update_title(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU4", "admin_du4@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"title": "New Title"},
            headers=auth_headers(admin),
        )
        assert resp.json()["title"] == "New Title"

    def test_update_severity(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU5", "admin_du5@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"severity": "BLOCKER"},
            headers=auth_headers(admin),
        )
        assert resp.json()["severity"] == "BLOCKER"

    def test_update_priority(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU6", "admin_du6@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"priority": "LOW"},
            headers=auth_headers(admin),
        )
        assert resp.json()["priority"] == "LOW"

    def test_update_environment(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU7", "admin_du7@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"environment": "STAGING"},
            headers=auth_headers(admin),
        )
        assert resp.json()["environment"] == "STAGING"

    def test_assign_active_user(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU8", "admin_du8@example.com")
        assignee = make_user(db, "assignee_du8@example.com", role=UserRole.QA_ENGINEER)
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"assigned_to": assignee.id},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == assignee.id

    def test_reject_inactive_assignee_on_update(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU9", "admin_du9@example.com")
        inactive = make_user(db, "inactive_du9@example.com", role=UserRole.QA_ENGINEER,
                             status=UserStatus.INACTIVE)
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"assigned_to": inactive.id},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400

    def test_reject_nonexistent_assignee_on_update(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU10", "admin_du10@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"assigned_to": 999999},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_project_id_not_changeable(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU11", "admin_du11@example.com")
        other_p = _make_project(db, "DU11B")
        # project_id is not in DefectUpdate schema — it should be ignored
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"project_id": other_p.id, "title": "Same Title"},
            headers=auth_headers(admin),
        )
        if resp.status_code == 200:
            assert resp.json()["project_id"] == p.id

    def test_invalid_update_payload_returns_422(self, client: TestClient, db: Session):
        admin, p, d = self._setup(db, client, "DU12", "admin_du12@example.com")
        resp = client.put(
            f"/api/defects/{d['id']}",
            json={"severity": "INVALID_VALUE"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422


# ===========================================================================
# Lifecycle transitions
# ===========================================================================

class TestDefectLifecycle:
    def _open_defect(self, client, db, key, email):
        admin = make_user(db, email, role=UserRole.ADMIN)
        p = _make_project(db, key)
        d = _create_defect(client, auth_headers(admin), p.id).json()
        return admin, d

    def _transition(self, client, headers, defect_id, new_status):
        return client.put(
            f"/api/defects/{defect_id}",
            json={"status": new_status},
            headers=headers,
        )

    def test_open_to_in_progress(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL1", "admin_dl1@example.com")
        resp = self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_open_to_rejected(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL2", "admin_dl2@example.com")
        resp = self._transition(client, auth_headers(admin), d["id"], "REJECTED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_in_progress_to_resolved(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL3", "admin_dl3@example.com")
        self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        resp = self._transition(client, auth_headers(admin), d["id"], "RESOLVED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"

    def test_in_progress_to_rejected(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL4", "admin_dl4@example.com")
        self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        resp = self._transition(client, auth_headers(admin), d["id"], "REJECTED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_resolved_to_closed(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL5", "admin_dl5@example.com")
        self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        self._transition(client, auth_headers(admin), d["id"], "RESOLVED")
        resp = self._transition(client, auth_headers(admin), d["id"], "CLOSED")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CLOSED"

    def test_resolved_to_in_progress(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL6", "admin_dl6@example.com")
        self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        self._transition(client, auth_headers(admin), d["id"], "RESOLVED")
        resp = self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_rejected_to_open(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL7", "admin_dl7@example.com")
        self._transition(client, auth_headers(admin), d["id"], "REJECTED")
        resp = self._transition(client, auth_headers(admin), d["id"], "OPEN")
        assert resp.status_code == 200
        assert resp.json()["status"] == "OPEN"

    def test_closed_cannot_transition(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL8", "admin_dl8@example.com")
        self._transition(client, auth_headers(admin), d["id"], "IN_PROGRESS")
        self._transition(client, auth_headers(admin), d["id"], "RESOLVED")
        self._transition(client, auth_headers(admin), d["id"], "CLOSED")
        for target in ("OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"):
            resp = self._transition(client, auth_headers(admin), d["id"], target)
            assert resp.status_code == 409, f"Expected 409 for CLOSED->{target}"

    def test_invalid_transition_rejected(self, client: TestClient, db: Session):
        admin, d = self._open_defect(client, db, "DL9", "admin_dl9@example.com")
        # OPEN → CLOSED is not allowed
        resp = self._transition(client, auth_headers(admin), d["id"], "CLOSED")
        assert resp.status_code == 409

    def test_viewer_cannot_transition(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dl10a@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_dl10@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "DL10")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = self._transition(client, auth_headers(viewer), d["id"], "IN_PROGRESS")
        assert resp.status_code == 403


# ===========================================================================
# Delete
# ===========================================================================

class TestDefectDelete:
    """
    Physical deletion strategy: defects are deleted permanently.
    The current schema has no child tables referencing defects, so physical
    deletion is safe. A 204 is returned on success.
    """

    def test_admin_deletes_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dd1@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DD1")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.delete(f"/api/defects/{d['id']}", headers=auth_headers(admin))
        assert resp.status_code == 204

    def test_deleted_defect_not_retrievable(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dd2@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DD2")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        client.delete(f"/api/defects/{d['id']}", headers=auth_headers(admin))
        resp = client.get(f"/api/defects/{d['id']}", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_delete_nonexistent_defect_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dd3@example.com", role=UserRole.ADMIN)
        resp = client.delete("/api/defects/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_viewer_cannot_delete_defect(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dd4a@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_dd4@example.com", role=UserRole.VIEWER)
        p = _make_project(db, "DD4")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.delete(f"/api/defects/{d['id']}", headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_qa_engineer_can_delete_defect(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_dd5@example.com", role=UserRole.QA_ENGINEER)
        p = _make_project(db, "DD5")
        d = _create_defect(client, auth_headers(qa), p.id).json()
        resp = client.delete(f"/api/defects/{d['id']}", headers=auth_headers(qa))
        assert resp.status_code == 204

    def test_unauthenticated_delete_rejected(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dd6@example.com", role=UserRole.ADMIN)
        p = _make_project(db, "DD6")
        d = _create_defect(client, auth_headers(admin), p.id).json()
        resp = client.delete(f"/api/defects/{d['id']}")
        assert resp.status_code == 401
