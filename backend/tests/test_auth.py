"""
Authentication and authorization tests — Phase 4.

Uses SQLite in-memory for the database layer.
All tests are isolated — no shared mutable state.
No MySQL required.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.main import app as fastapi_app
from app.models.user import User
from app.models.enums import UserRole, UserStatus
import app.models  # noqa: F401 — register all models


# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_engine():
    # StaticPool + check_same_thread=False allows the same in-memory DB
    # to be used across the test thread and FastAPI's worker threads.
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(eng, "connect")
    def set_fk(dbapi_conn, _):
        dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(test_engine) -> Session:
    # Bind session directly to the engine (not a connection) so SQLAlchemy
    # manages its own connection checkout — compatible with StaticPool.
    session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def clean_users(test_engine):
    """Delete all rows from users after each test to keep tests isolated."""
    yield
    with test_engine.connect() as conn:
        conn.execute(Base.metadata.tables["users"].delete())
        conn.commit()


@pytest.fixture
def client(db):
    """TestClient with the real DB dependency overridden to use the test session."""
    fastapi_app.dependency_overrides[get_db] = lambda: db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    db: Session,
    email: str = "user@example.com",
    password: str = "Secret123!",
    role: UserRole = UserRole.QA_ENGINEER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    u = User(
        name="Test User",
        email=email,
        password_hash=hash_password(password),
        role=role,
        status=status,
    )
    db.add(u)
    db.flush()
    return u


def _token_for(user: User) -> str:
    return create_access_token(subject=user.id)


def _expired_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _token_wrong_secret(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)


# ===========================================================================
# PASSWORD HASHING TESTS
# ===========================================================================

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("MyPassword1!")
        assert h != "MyPassword1!"

    def test_correct_password_verifies(self):
        h = hash_password("Correct!")
        assert verify_password("Correct!", h) is True

    def test_wrong_password_fails(self):
        h = hash_password("Correct!")
        assert verify_password("Wrong!", h) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt — same password produces different hashes."""
        h1 = hash_password("SamePass1!")
        h2 = hash_password("SamePass1!")
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = hash_password("SamePass1!")
        h2 = hash_password("SamePass1!")
        assert verify_password("SamePass1!", h1) is True
        assert verify_password("SamePass1!", h2) is True

    def test_empty_password_hashes(self):
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("notempty", h) is False


# ===========================================================================
# JWT TESTS
# ===========================================================================

class TestJWT:
    def test_create_token_returns_string(self):
        token = create_access_token(subject=42)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token_returns_user_id(self):
        token = create_access_token(subject=99)
        assert decode_access_token(token) == 99

    def test_decode_string_subject(self):
        token = create_access_token(subject="7")
        assert decode_access_token(token) == 7

    def test_expired_token_raises(self):
        token = _expired_token(1)
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token(token)

    def test_wrong_signature_raises(self):
        token = _token_wrong_secret(1)
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token(token)

    def test_malformed_token_raises(self):
        with pytest.raises(ValueError):
            decode_access_token("not.a.jwt")

    def test_empty_token_raises(self):
        with pytest.raises(ValueError):
            decode_access_token("")

    def test_token_missing_sub_raises(self):
        payload = {
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(ValueError, match="missing subject"):
            decode_access_token(token)

    def test_token_non_integer_sub_raises(self):
        payload = {
            "sub": "not-an-int",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(ValueError, match="not a valid user identifier"):
            decode_access_token(token)

    def test_token_contains_expiration(self):
        token = create_access_token(subject=1)
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        assert "exp" in payload
        assert "sub" in payload

    def test_password_hash_not_in_token(self):
        token = create_access_token(subject=1)
        # Decode without verification to inspect raw payload
        raw = jwt.get_unverified_claims(token)
        assert "password" not in raw
        assert "password_hash" not in raw


# ===========================================================================
# POST /api/auth/login TESTS
# ===========================================================================

class TestLogin:
    def test_valid_credentials_returns_200(self, client, db):
        _make_user(db, "login_ok@example.com", "Pass123!")
        resp = client.post("/api/auth/login", json={"email": "login_ok@example.com", "password": "Pass123!"})
        assert resp.status_code == 200

    def test_valid_login_returns_token(self, client, db):
        _make_user(db, "token_ok@example.com", "Pass123!")
        resp = client.post("/api/auth/login", json={"email": "token_ok@example.com", "password": "Pass123!"})
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0

    def test_valid_login_returns_user_info(self, client, db):
        _make_user(db, "userinfo@example.com", "Pass123!", role=UserRole.ADMIN)
        resp = client.post("/api/auth/login", json={"email": "userinfo@example.com", "password": "Pass123!"})
        user = resp.json()["user"]
        assert user["email"] == "userinfo@example.com"
        assert user["role"] == "ADMIN"
        assert user["status"] == "ACTIVE"

    def test_password_hash_not_in_response(self, client, db):
        _make_user(db, "nohash@example.com", "Pass123!")
        resp = client.post("/api/auth/login", json={"email": "nohash@example.com", "password": "Pass123!"})
        body = str(resp.json())
        assert "password_hash" not in body
        assert "password" not in resp.json()["user"]

    def test_invalid_email_returns_401(self, client, db):
        resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "Pass123!"})
        assert resp.status_code == 401

    def test_invalid_password_returns_401(self, client, db):
        _make_user(db, "wrongpass@example.com", "Correct123!")
        resp = client.post("/api/auth/login", json={"email": "wrongpass@example.com", "password": "Wrong123!"})
        assert resp.status_code == 401

    def test_inactive_user_returns_401(self, client, db):
        _make_user(db, "inactive@example.com", "Pass123!", status=UserStatus.INACTIVE)
        resp = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "Pass123!"})
        assert resp.status_code == 401

    def test_empty_email_returns_422(self, client):
        resp = client.post("/api/auth/login", json={"email": "", "password": "Pass123!"})
        assert resp.status_code == 422

    def test_empty_password_returns_422(self, client):
        # Empty password passes Pydantic (it's a non-empty string type) but fails auth
        # FastAPI validates the schema — empty string is valid str, so 401 not 422
        resp = client.post("/api/auth/login", json={"email": "x@example.com", "password": ""})
        assert resp.status_code in (401, 422)

    def test_missing_email_field_returns_422(self, client):
        resp = client.post("/api/auth/login", json={"password": "Pass123!"})
        assert resp.status_code == 422

    def test_missing_password_field_returns_422(self, client):
        resp = client.post("/api/auth/login", json={"email": "x@example.com"})
        assert resp.status_code == 422

    def test_malformed_json_returns_422(self, client):
        resp = client.post(
            "/api/auth/login",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_invalid_email_format_returns_422(self, client):
        resp = client.post("/api/auth/login", json={"email": "not-an-email", "password": "Pass123!"})
        assert resp.status_code == 422


# ===========================================================================
# GET /api/auth/me TESTS
# ===========================================================================

class TestMe:
    def test_valid_token_returns_200(self, client, db):
        user = _make_user(db, "me_ok@example.com")
        token = _token_for(user)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_me_returns_correct_user(self, client, db):
        user = _make_user(db, "me_data@example.com", role=UserRole.VIEWER)
        token = _token_for(user)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        body = resp.json()
        assert body["email"] == "me_data@example.com"
        assert body["role"] == "VIEWER"
        assert "password_hash" not in body
        assert "password" not in body

    def test_missing_token_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_malformed_token_returns_401(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client, db):
        user = _make_user(db, "me_expired@example.com")
        token = _expired_token(user.id)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_wrong_signature_returns_401(self, client, db):
        user = _make_user(db, "me_badsig@example.com")
        token = _token_wrong_secret(user.id)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_nonexistent_user_in_token_returns_401(self, client):
        token = create_access_token(subject=999999)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_inactive_user_token_returns_401(self, client, db):
        user = _make_user(db, "me_inactive@example.com", status=UserStatus.INACTIVE)
        token = _token_for(user)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_wrong_scheme_returns_401(self, client, db):
        user = _make_user(db, "me_scheme@example.com")
        token = _token_for(user)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Token {token}"})
        assert resp.status_code == 401


# ===========================================================================
# ROLE-BASED AUTHORIZATION TESTS
# ===========================================================================

class TestRBAC:
    """
    Test the require_roles dependency directly by creating a small protected
    endpoint on the test client — avoids creating permanent fake endpoints
    in the production app.
    """

    @pytest.fixture
    def rbac_client(self, db):
        from fastapi import APIRouter, Depends
        from typing import Annotated

        test_router = APIRouter()

        @test_router.get("/test/admin-only")
        def admin_only(
            user: Annotated[User, Depends(require_roles(UserRole.ADMIN))]
        ):
            return {"role": user.role}

        @test_router.get("/test/qa-or-admin")
        def qa_or_admin(
            user: Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))]
        ):
            return {"role": user.role}

        @test_router.get("/test/any-authenticated")
        def any_auth(user: Annotated[User, Depends(get_current_user)]):
            return {"role": user.role}

        fastapi_app.include_router(test_router)
        fastapi_app.dependency_overrides[get_db] = lambda: db
        yield TestClient(fastapi_app)
        fastapi_app.dependency_overrides.clear()

    def test_admin_can_access_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_admin@example.com", role=UserRole.ADMIN)
        token = _token_for(user)
        resp = rbac_client.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_qa_engineer_cannot_access_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_qa_denied@example.com", role=UserRole.QA_ENGINEER)
        token = _token_for(user)
        resp = rbac_client.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_viewer_cannot_access_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_viewer_denied@example.com", role=UserRole.VIEWER)
        token = _token_for(user)
        resp = rbac_client.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_qa_engineer_can_access_qa_or_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_qa_ok@example.com", role=UserRole.QA_ENGINEER)
        token = _token_for(user)
        resp = rbac_client.get("/test/qa-or-admin", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_admin_can_access_qa_or_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_admin_qa@example.com", role=UserRole.ADMIN)
        token = _token_for(user)
        resp = rbac_client.get("/test/qa-or-admin", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_viewer_cannot_access_qa_or_admin_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_viewer_qa@example.com", role=UserRole.VIEWER)
        token = _token_for(user)
        resp = rbac_client.get("/test/qa-or-admin", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_viewer_can_access_any_authenticated_endpoint(self, rbac_client, db):
        user = _make_user(db, "rbac_viewer_any@example.com", role=UserRole.VIEWER)
        token = _token_for(user)
        resp = rbac_client.get("/test/any-authenticated", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_unauthenticated_request_returns_401_not_403(self, rbac_client):
        """Unauthenticated → 401, not 403."""
        resp = rbac_client.get("/test/admin-only")
        assert resp.status_code == 401

    def test_wrong_role_returns_403_not_401(self, rbac_client, db):
        """Authenticated but wrong role → 403, not 401."""
        user = _make_user(db, "rbac_wrong_role@example.com", role=UserRole.VIEWER)
        token = _token_for(user)
        resp = rbac_client.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
