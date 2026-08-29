"""
Shared pytest fixtures for backend API tests.

Uses SQLite in-memory with StaticPool so the same DB is visible across
FastAPI's dependency injection and the test thread.
"""
import pytest
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from fastapi.testclient import TestClient

from app.core.database import Base
from app.core.security import hash_password, create_access_token
from app.dependencies.db import get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.models.enums import UserRole, UserStatus
import app.models  # noqa: F401 — register all models


@pytest.fixture(scope="module")
def test_engine():
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
    session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    yield
    with test_engine.connect() as conn:
        # Delete in FK-safe order
        for tbl in ("project_members", "defects", "test_results", "test_runs",
                    "test_cases", "test_suites", "projects", "users"):
            if tbl in Base.metadata.tables:
                conn.execute(Base.metadata.tables[tbl].delete())
        conn.commit()


@pytest.fixture
def client(db):
    fastapi_app.dependency_overrides[get_db] = lambda: db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def make_user(
    db: Session,
    email: str = "user@example.com",
    password: str = "Secret123!",
    role: UserRole = UserRole.QA_ENGINEER,
    status: UserStatus = UserStatus.ACTIVE,
    name: str = "Test User",
) -> User:
    u = User(name=name, email=email, password_hash=hash_password(password), role=role, status=status)
    db.add(u)
    db.flush()
    return u


def token_for(user: User) -> str:
    return create_access_token(subject=user.id)


def auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {token_for(user)}"}
