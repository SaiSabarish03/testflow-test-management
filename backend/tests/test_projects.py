"""
Project API tests — Phase 5.

Tests cover: CRUD, RBAC, validation, search, filtering, pagination, archive semantics.
Uses SQLite in-memory via shared conftest fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, UserStatus, ProjectStatus
from tests.conftest import make_user, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_project(client: TestClient, headers: dict, name: str = "TestFlow", key: str = "TFW", description: str | None = None) -> dict:
    payload = {"name": name, "key": key}
    if description:
        payload["description"] = description
    resp = client.post("/api/projects", json=payload, headers=headers)
    return resp


# ===========================================================================
# Admin CRUD
# ===========================================================================

class TestAdminCreateProject:
    def test_admin_creates_project_returns_201(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_proj@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "My Project", "MYPROJ")
        assert resp.status_code == 201

    def test_created_project_response_fields(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_pfields@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Field Project", "FLDP")
        body = resp.json()
        assert body["name"] == "Field Project"
        assert body["key"] == "FLDP"
        assert body["status"] == "ACTIVE"
        assert body["created_by"] == admin.id
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_created_by_comes_from_auth_user(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_createdby@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Auth Project", "AUTHP")
        assert resp.json()["created_by"] == admin.id

    def test_new_project_defaults_to_active(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_active@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Active Project", "ACTP")
        assert resp.json()["status"] == "ACTIVE"


class TestQACreateProject:
    def test_qa_engineer_creates_project(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_proj@example.com", role=UserRole.QA_ENGINEER)
        resp = _create_project(client, auth_headers(qa), "QA Project", "QAPRJ")
        assert resp.status_code == 201
        assert resp.json()["created_by"] == qa.id


class TestProjectRetrieval:
    def test_admin_retrieves_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_retr@example.com", role=UserRole.ADMIN)
        created = _create_project(client, auth_headers(admin), "Retrieve Me", "RETRP").json()
        resp = client.get(f"/api/projects/{created['id']}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["key"] == "RETRP"

    def test_viewer_can_read_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_vread@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_read@example.com", role=UserRole.VIEWER)
        created = _create_project(client, auth_headers(admin), "Viewer Read", "VREAD").json()
        resp = client.get(f"/api/projects/{created['id']}", headers=auth_headers(viewer))
        assert resp.status_code == 200

    def test_nonexistent_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_p404@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/projects/999999", headers=auth_headers(admin))
        assert resp.status_code == 404


class TestProjectUpdate:
    def test_admin_updates_project_name(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_pupd@example.com", role=UserRole.ADMIN)
        created = _create_project(client, auth_headers(admin), "Old Name", "OLDNM").json()
        resp = client.put(f"/api/projects/{created['id']}", json={"name": "New Name"}, headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_qa_engineer_updates_project(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_pupd@example.com", role=UserRole.QA_ENGINEER)
        created = _create_project(client, auth_headers(qa), "QA Update", "QAUPD").json()
        resp = client.put(f"/api/projects/{created['id']}", json={"description": "Updated desc"}, headers=auth_headers(qa))
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated desc"

    def test_project_key_cannot_be_changed(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_keyimm@example.com", role=UserRole.ADMIN)
        created = _create_project(client, auth_headers(admin), "Key Immutable", "KEYIM").json()
        # key is not in ProjectUpdate schema — it should be ignored/rejected
        resp = client.put(f"/api/projects/{created['id']}", json={"key": "NEWKEY"}, headers=auth_headers(admin))
        # Either 200 with key unchanged, or 422 — key field is not accepted
        if resp.status_code == 200:
            assert resp.json()["key"] == "KEYIM"

    def test_update_nonexistent_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_upd404p@example.com", role=UserRole.ADMIN)
        resp = client.put("/api/projects/999999", json={"name": "X"}, headers=auth_headers(admin))
        assert resp.status_code == 404


class TestProjectArchive:
    def test_admin_archives_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_arch@example.com", role=UserRole.ADMIN)
        created = _create_project(client, auth_headers(admin), "Archive Me", "ARCHP").json()
        resp = client.delete(f"/api/projects/{created['id']}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ARCHIVED"

    def test_qa_engineer_archives_project(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_arch@example.com", role=UserRole.QA_ENGINEER)
        created = _create_project(client, auth_headers(qa), "QA Archive", "QAARCH").json()
        resp = client.delete(f"/api/projects/{created['id']}", headers=auth_headers(qa))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ARCHIVED"

    def test_archive_nonexistent_project_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_arch404@example.com", role=UserRole.ADMIN)
        resp = client.delete("/api/projects/999999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_archived_project_still_retrievable(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_archget@example.com", role=UserRole.ADMIN)
        created = _create_project(client, auth_headers(admin), "Still Here", "STLHR").json()
        client.delete(f"/api/projects/{created['id']}", headers=auth_headers(admin))
        resp = client.get(f"/api/projects/{created['id']}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ARCHIVED"


# ===========================================================================
# Validation — negative tests
# ===========================================================================

class TestProjectValidation:
    def test_duplicate_key_returns_409(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dupkey@example.com", role=UserRole.ADMIN)
        _create_project(client, auth_headers(admin), "First", "DUPK")
        resp = _create_project(client, auth_headers(admin), "Second", "DUPK")
        assert resp.status_code == 409

    def test_invalid_key_lowercase_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_badkey@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Bad Key", "lowercase")
        assert resp.status_code == 422

    def test_invalid_key_with_spaces_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_spacekey@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Space Key", "MY KEY")
        assert resp.status_code == 422

    def test_invalid_key_too_short_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_shortkey@example.com", role=UserRole.ADMIN)
        resp = _create_project(client, auth_headers(admin), "Short Key", "A")
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_noname_p@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/projects", json={"key": "NONAME"}, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_missing_key_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_nokey@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/projects", json={"name": "No Key"}, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_valid_key_formats(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_validkey@example.com", role=UserRole.ADMIN)
        for key in ["TFW", "MOBILE", "CRM01", "AB"]:
            resp = _create_project(client, auth_headers(admin), f"Project {key}", key)
            assert resp.status_code == 201, f"Expected 201 for key={key}, got {resp.status_code}"


# ===========================================================================
# RBAC
# ===========================================================================

class TestProjectRBAC:
    def test_unauthenticated_list_returns_401(self, client: TestClient):
        resp = client.get("/api/projects")
        assert resp.status_code == 401

    def test_unauthenticated_create_returns_401(self, client: TestClient):
        resp = client.post("/api/projects", json={"name": "X", "key": "XX"})
        assert resp.status_code == 401

    def test_viewer_can_list_projects(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_plist@example.com", role=UserRole.VIEWER)
        resp = client.get("/api/projects", headers=auth_headers(viewer))
        assert resp.status_code == 200

    def test_viewer_cannot_create_project(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_pcreate@example.com", role=UserRole.VIEWER)
        resp = _create_project(client, auth_headers(viewer), "Viewer Project", "VWRP")
        assert resp.status_code == 403

    def test_viewer_cannot_update_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_vupd@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_pupd@example.com", role=UserRole.VIEWER)
        created = _create_project(client, auth_headers(admin), "Viewer Update", "VUPD").json()
        resp = client.put(f"/api/projects/{created['id']}", json={"name": "X"}, headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_viewer_cannot_archive_project(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_varch@example.com", role=UserRole.ADMIN)
        viewer = make_user(db, "viewer_parch@example.com", role=UserRole.VIEWER)
        created = _create_project(client, auth_headers(admin), "Viewer Archive", "VARCH").json()
        resp = client.delete(f"/api/projects/{created['id']}", headers=auth_headers(viewer))
        assert resp.status_code == 403


# ===========================================================================
# List — search, filter, pagination
# ===========================================================================

class TestProjectList:
    def test_list_returns_pagination_fields(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_lpg@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/projects?page=1&page_size=10", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "page_size" in body
        assert "pages" in body

    def test_search_by_name(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_srchp@example.com", role=UserRole.ADMIN)
        _create_project(client, auth_headers(admin), "UniqueSearchName", "USRCH")
        _create_project(client, auth_headers(admin), "Other Project", "OTHRP")
        resp = client.get("/api/projects?search=UniqueSearchName", headers=auth_headers(admin))
        assert resp.status_code == 200
        keys = [p["key"] for p in resp.json()["items"]]
        assert "USRCH" in keys
        assert "OTHRP" not in keys

    def test_search_by_key(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_srchk@example.com", role=UserRole.ADMIN)
        _create_project(client, auth_headers(admin), "Key Search Project", "KSRCH")
        resp = client.get("/api/projects?search=KSRCH", headers=auth_headers(admin))
        assert resp.status_code == 200
        keys = [p["key"] for p in resp.json()["items"]]
        assert "KSRCH" in keys

    def test_filter_by_status_active(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_fstat@example.com", role=UserRole.ADMIN)
        _create_project(client, auth_headers(admin), "Active One", "ACTO")
        archived = _create_project(client, auth_headers(admin), "Archived One", "ARCHO").json()
        client.delete(f"/api/projects/{archived['id']}", headers=auth_headers(admin))
        resp = client.get("/api/projects?status=ACTIVE", headers=auth_headers(admin))
        assert resp.status_code == 200
        for p in resp.json()["items"]:
            assert p["status"] == "ACTIVE"

    def test_filter_by_status_archived(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_farch@example.com", role=UserRole.ADMIN)
        archived = _create_project(client, auth_headers(admin), "Archived Filter", "ARCHF").json()
        client.delete(f"/api/projects/{archived['id']}", headers=auth_headers(admin))
        resp = client.get("/api/projects?status=ARCHIVED", headers=auth_headers(admin))
        assert resp.status_code == 200
        for p in resp.json()["items"]:
            assert p["status"] == "ARCHIVED"

    def test_pagination_page_size(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_ppg@example.com", role=UserRole.ADMIN)
        for i in range(5):
            _create_project(client, auth_headers(admin), f"Paged {i}", f"PG{i:02d}")
        resp = client.get("/api/projects?page=1&page_size=3", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 3
        assert body["page_size"] == 3

    def test_pagination_second_page(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_pg2@example.com", role=UserRole.ADMIN)
        for i in range(4):
            _create_project(client, auth_headers(admin), f"Page2 {i}", f"P2{i:02d}")
        resp = client.get("/api/projects?page=2&page_size=2", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
