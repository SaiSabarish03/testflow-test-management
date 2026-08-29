"""
User API tests — Phase 5.

Tests cover: CRUD, RBAC, validation, password security, pagination/filtering.
Uses SQLite in-memory via shared conftest fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole, UserStatus
from tests.conftest import make_user, auth_headers


# ===========================================================================
# Admin CRUD
# ===========================================================================

class TestAdminListUsers:
    def test_admin_lists_users(self, client: TestClient, db: Session):
        admin = make_user(db, "admin@example.com", role=UserRole.ADMIN)
        make_user(db, "qa@example.com", role=UserRole.QA_ENGINEER)
        resp = client.get("/api/users", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        assert "items" in body
        assert "pages" in body

    def test_list_users_pagination_fields(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_pg@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/users?page=1&page_size=5", headers=auth_headers(admin))
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 5

    def test_list_users_search_by_name(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_srch@example.com", role=UserRole.ADMIN, name="Admin User")
        make_user(db, "findme@example.com", role=UserRole.VIEWER, name="UniqueNameXYZ")
        resp = client.get("/api/users?search=UniqueNameXYZ", headers=auth_headers(admin))
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()["items"]]
        assert "findme@example.com" in emails

    def test_list_users_filter_by_role(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_role@example.com", role=UserRole.ADMIN)
        make_user(db, "viewer_role@example.com", role=UserRole.VIEWER)
        resp = client.get("/api/users?role=VIEWER", headers=auth_headers(admin))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["role"] == "VIEWER"

    def test_list_users_filter_by_status(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_stat@example.com", role=UserRole.ADMIN)
        make_user(db, "inactive_stat@example.com", role=UserRole.VIEWER, status=UserStatus.INACTIVE)
        resp = client.get("/api/users?status=INACTIVE", headers=auth_headers(admin))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "INACTIVE"


class TestAdminCreateUser:
    def test_admin_creates_user_returns_201(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_create@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "New User", "email": "newuser@example.com",
            "password": "Password1!", "role": "QA_ENGINEER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 201

    def test_created_user_response_fields(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_fields@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "Field User", "email": "fielduser@example.com",
            "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(admin))
        body = resp.json()
        assert body["email"] == "fielduser@example.com"
        assert body["role"] == "VIEWER"
        assert body["status"] == "ACTIVE"
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_password_never_returned_on_create(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_nopw@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "No PW", "email": "nopw@example.com",
            "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(admin))
        body = str(resp.json())
        assert "password" not in resp.json()
        assert "password_hash" not in body


class TestAdminGetUser:
    def test_admin_retrieves_user(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_get@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_get@example.com", role=UserRole.VIEWER)
        resp = client.get(f"/api/users/{target.id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["email"] == "target_get@example.com"

    def test_password_never_returned_on_get(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_getpw@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_getpw@example.com")
        resp = client.get(f"/api/users/{target.id}", headers=auth_headers(admin))
        assert "password" not in resp.json()
        assert "password_hash" not in str(resp.json())

    def test_nonexistent_user_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_404@example.com", role=UserRole.ADMIN)
        resp = client.get("/api/users/999999", headers=auth_headers(admin))
        assert resp.status_code == 404


class TestAdminUpdateUser:
    def test_admin_updates_user_name(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_upd@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_upd@example.com")
        resp = client.put(f"/api/users/{target.id}", json={"name": "Updated Name"}, headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_admin_updates_user_role(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_role_upd@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_role_upd@example.com", role=UserRole.VIEWER)
        resp = client.put(f"/api/users/{target.id}", json={"role": "QA_ENGINEER"}, headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["role"] == "QA_ENGINEER"

    def test_admin_updates_password_not_returned(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_pwupd@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_pwupd@example.com")
        resp = client.put(f"/api/users/{target.id}", json={"password": "NewPass123!"}, headers=auth_headers(admin))
        assert resp.status_code == 200
        assert "password" not in resp.json()
        assert "password_hash" not in str(resp.json())

    def test_update_nonexistent_user_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_upd404@example.com", role=UserRole.ADMIN)
        resp = client.put("/api/users/999999", json={"name": "X"}, headers=auth_headers(admin))
        assert resp.status_code == 404


class TestAdminDeactivateUser:
    def test_admin_deactivates_user(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_deact@example.com", role=UserRole.ADMIN)
        target = make_user(db, "target_deact@example.com")
        resp = client.delete(f"/api/users/{target.id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "INACTIVE"

    def test_deactivate_nonexistent_user_returns_404(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_deact404@example.com", role=UserRole.ADMIN)
        resp = client.delete("/api/users/999999", headers=auth_headers(admin))
        assert resp.status_code == 404


# ===========================================================================
# Validation — negative tests
# ===========================================================================

class TestUserValidation:
    def test_duplicate_email_returns_409(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dup@example.com", role=UserRole.ADMIN)
        make_user(db, "dup@example.com")
        resp = client.post("/api/users", json={
            "name": "Dup", "email": "dup@example.com",
            "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 409

    def test_invalid_email_format_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_bademail@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "Bad", "email": "not-an-email",
            "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_noname@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "email": "noname@example.com", "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_nopwd@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "No Pwd", "email": "nopwd@example.com", "role": "VIEWER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_short_password_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_shortpw@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "Short", "email": "short@example.com",
            "password": "abc", "role": "VIEWER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_invalid_role_returns_422(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_badrole@example.com", role=UserRole.ADMIN)
        resp = client.post("/api/users", json={
            "name": "Bad Role", "email": "badrole@example.com",
            "password": "Password1!", "role": "SUPERUSER",
        }, headers=auth_headers(admin))
        assert resp.status_code == 422

    def test_update_duplicate_email_returns_409(self, client: TestClient, db: Session):
        admin = make_user(db, "admin_dupupd@example.com", role=UserRole.ADMIN)
        make_user(db, "existing@example.com")
        target = make_user(db, "target_dupupd@example.com")
        resp = client.put(f"/api/users/{target.id}", json={"email": "existing@example.com"}, headers=auth_headers(admin))
        assert resp.status_code == 409


# ===========================================================================
# RBAC
# ===========================================================================

class TestUserRBAC:
    def test_unauthenticated_list_returns_401(self, client: TestClient):
        resp = client.get("/api/users")
        assert resp.status_code == 401

    def test_unauthenticated_create_returns_401(self, client: TestClient):
        resp = client.post("/api/users", json={
            "name": "X", "email": "x@example.com", "password": "Password1!", "role": "VIEWER",
        })
        assert resp.status_code == 401

    def test_viewer_list_returns_403(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_list@example.com", role=UserRole.VIEWER)
        resp = client.get("/api/users", headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_viewer_create_returns_403(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_create@example.com", role=UserRole.VIEWER)
        resp = client.post("/api/users", json={
            "name": "X", "email": "x2@example.com", "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_viewer_get_returns_403(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_get@example.com", role=UserRole.VIEWER)
        resp = client.get(f"/api/users/{viewer.id}", headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_viewer_update_returns_403(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_upd@example.com", role=UserRole.VIEWER)
        resp = client.put(f"/api/users/{viewer.id}", json={"name": "X"}, headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_viewer_delete_returns_403(self, client: TestClient, db: Session):
        viewer = make_user(db, "viewer_del@example.com", role=UserRole.VIEWER)
        resp = client.delete(f"/api/users/{viewer.id}", headers=auth_headers(viewer))
        assert resp.status_code == 403

    def test_qa_engineer_can_list_users(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_list@example.com", role=UserRole.QA_ENGINEER)
        resp = client.get("/api/users", headers=auth_headers(qa))
        assert resp.status_code == 200

    def test_qa_engineer_can_get_user(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_get@example.com", role=UserRole.QA_ENGINEER)
        target = make_user(db, "qa_target@example.com")
        resp = client.get(f"/api/users/{target.id}", headers=auth_headers(qa))
        assert resp.status_code == 200

    def test_qa_engineer_cannot_create_user(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_create@example.com", role=UserRole.QA_ENGINEER)
        resp = client.post("/api/users", json={
            "name": "X", "email": "qa_new@example.com", "password": "Password1!", "role": "VIEWER",
        }, headers=auth_headers(qa))
        assert resp.status_code == 403

    def test_qa_engineer_cannot_update_user(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_upd@example.com", role=UserRole.QA_ENGINEER)
        target = make_user(db, "qa_upd_target@example.com")
        resp = client.put(f"/api/users/{target.id}", json={"name": "X"}, headers=auth_headers(qa))
        assert resp.status_code == 403

    def test_qa_engineer_cannot_delete_user(self, client: TestClient, db: Session):
        qa = make_user(db, "qa_del@example.com", role=UserRole.QA_ENGINEER)
        target = make_user(db, "qa_del_target@example.com")
        resp = client.delete(f"/api/users/{target.id}", headers=auth_headers(qa))
        assert resp.status_code == 403
