"""
Infrastructure tests — Phase 2.

These tests verify the FastAPI application starts, health endpoints respond,
the database session dependency works, and DB failures are handled gracefully.

Tests that require a live MySQL connection are skipped when MySQL is unavailable
so the suite can run in CI without a database (those tests run in Docker).
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app
from app.core.database import check_database_connection, SessionLocal
from app.dependencies.db import get_db

client = TestClient(app)


# ---------------------------------------------------------------------------
# Application startup
# ---------------------------------------------------------------------------

def test_app_is_created():
    assert app.title == "TestFlow API"


def test_health_endpoint_responds():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "TestFlow"


# ---------------------------------------------------------------------------
# Database health endpoint
# ---------------------------------------------------------------------------

def test_db_health_returns_ok_when_db_available():
    """Returns 200 when MySQL is reachable (mocked)."""
    with patch("app.main.check_database_connection", return_value=True):
        response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"


def test_db_health_returns_503_when_db_unavailable():
    """Returns 503 when MySQL is unreachable — does NOT fake success."""
    with patch("app.main.check_database_connection", return_value=False):
        response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["database"] == "unreachable"


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

def test_get_db_yields_session():
    """get_db dependency yields a SQLAlchemy Session object."""
    from sqlalchemy.orm import Session
    gen = get_db()
    db = next(gen)
    assert isinstance(db, Session)
    try:
        next(gen)
    except StopIteration:
        pass  # expected — generator exhausted after cleanup


# ---------------------------------------------------------------------------
# check_database_connection behaviour
# ---------------------------------------------------------------------------

def test_check_database_connection_returns_false_on_error():
    """check_database_connection returns False (not raises) when DB is down."""
    with patch("app.core.database.engine") as mock_engine:
        mock_engine.connect.side_effect = OperationalError(
            "Can't connect", None, None
        )
        result = check_database_connection()
    assert result is False


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_settings_load():
    from app.core.config import settings
    assert settings.APP_NAME == "TestFlow"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------

def test_base_exists():
    from app.core.database import Base
    from sqlalchemy.orm import DeclarativeBase
    assert issubclass(Base, DeclarativeBase)
