"""
Model tests — Phase 3.

Uses an in-memory SQLite database so tests run without MySQL.
SQLite does not enforce foreign keys by default; we enable them explicitly.
Enum columns are stored as VARCHAR in SQLite — behaviour is equivalent for testing.
"""
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
import app.models  # noqa: F401 — registers all models

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.test_suite import TestSuite
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.defect import Defect
from app.models.enums import (
    UserRole, UserStatus, ProjectStatus,
    TestCasePriority, TestCaseStatus,
    TestRunStatus, TestResultStatus,
    DefectSeverity, DefectPriority, DefectStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)

    # Enable FK enforcement in SQLite
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(db: Session, email: str, role: UserRole = UserRole.QA_ENGINEER) -> User:
    u = User(
        name="Test User",
        email=email,
        password_hash="hashed",
        role=role,
        status=UserStatus.ACTIVE,
    )
    db.add(u)
    db.flush()
    return u


def make_project(db: Session, key: str, created_by: int) -> Project:
    p = Project(
        name=f"Project {key}",
        key=key,
        status=ProjectStatus.ACTIVE,
        created_by=created_by,
    )
    db.add(p)
    db.flush()
    return p


def make_suite(db: Session, project_id: int, created_by: int, name: str = "Suite A") -> TestSuite:
    s = TestSuite(project_id=project_id, name=name, created_by=created_by)
    db.add(s)
    db.flush()
    return s


def make_test_case(db: Session, suite_id: int, created_by: int, title: str = "TC1") -> TestCase:
    tc = TestCase(
        suite_id=suite_id,
        title=title,
        expected_result="Expected outcome.",
        priority=TestCasePriority.HIGH,
        status=TestCaseStatus.READY,
        created_by=created_by,
    )
    db.add(tc)
    db.flush()
    return tc


def make_run(db: Session, project_id: int, created_by: int) -> TestRun:
    r = TestRun(
        project_id=project_id,
        name="Run 1",
        environment="QA",
        status=TestRunStatus.NOT_STARTED,
        created_by=created_by,
    )
    db.add(r)
    db.flush()
    return r


# ---------------------------------------------------------------------------
# Schema existence
# ---------------------------------------------------------------------------

def test_all_tables_created(engine):
    table_names = set(engine.dialect.get_table_names(engine.connect()))
    expected = {
        "users", "projects", "project_members",
        "test_suites", "test_cases", "test_runs",
        "test_results", "defects",
    }
    assert expected.issubset(table_names)


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

def test_user_create(db):
    u = make_user(db, "alice@example.com", UserRole.ADMIN)
    assert u.id is not None
    assert u.role == UserRole.ADMIN
    assert u.status == UserStatus.ACTIVE


def test_user_email_unique(db):
    make_user(db, "dup@example.com")
    with pytest.raises(IntegrityError):
        make_user(db, "dup@example.com")


def test_user_role_values():
    assert set(UserRole) == {UserRole.ADMIN, UserRole.QA_ENGINEER, UserRole.VIEWER}


def test_user_status_values():
    assert set(UserStatus) == {UserStatus.ACTIVE, UserStatus.INACTIVE}


# ---------------------------------------------------------------------------
# Project model
# ---------------------------------------------------------------------------

def test_project_create(db):
    u = make_user(db, "proj_owner@example.com")
    p = make_project(db, "PROJ1", u.id)
    assert p.id is not None
    assert p.key == "PROJ1"
    assert p.status == ProjectStatus.ACTIVE


def test_project_key_unique(db):
    u = make_user(db, "proj_owner2@example.com")
    make_project(db, "DUPKEY", u.id)
    with pytest.raises(IntegrityError):
        make_project(db, "DUPKEY", u.id)


def test_project_creator_relationship(db):
    u = make_user(db, "creator@example.com")
    p = make_project(db, "RELP", u.id)
    db.refresh(p)
    assert p.creator.email == "creator@example.com"


# ---------------------------------------------------------------------------
# ProjectMember model
# ---------------------------------------------------------------------------

def test_project_member_create(db):
    u = make_user(db, "member@example.com")
    p = make_project(db, "MEMB", u.id)
    pm = ProjectMember(project_id=p.id, user_id=u.id)
    db.add(pm)
    db.flush()
    assert pm.id is not None


def test_project_member_unique(db):
    u = make_user(db, "member2@example.com")
    p = make_project(db, "MEMB2", u.id)
    db.add(ProjectMember(project_id=p.id, user_id=u.id))
    db.flush()
    with pytest.raises(IntegrityError):
        db.add(ProjectMember(project_id=p.id, user_id=u.id))
        db.flush()


# ---------------------------------------------------------------------------
# TestSuite model
# ---------------------------------------------------------------------------

def test_test_suite_create(db):
    u = make_user(db, "suite_owner@example.com")
    p = make_project(db, "SUITE", u.id)
    s = make_suite(db, p.id, u.id)
    assert s.id is not None
    assert s.project_id == p.id


def test_test_suite_project_relationship(db):
    u = make_user(db, "suite_rel@example.com")
    p = make_project(db, "SREL", u.id)
    s = make_suite(db, p.id, u.id)
    db.refresh(s)
    assert s.project.key == "SREL"


# ---------------------------------------------------------------------------
# TestCase model
# ---------------------------------------------------------------------------

def test_test_case_create(db):
    u = make_user(db, "tc_owner@example.com")
    p = make_project(db, "TCP", u.id)
    s = make_suite(db, p.id, u.id)
    tc = make_test_case(db, s.id, u.id)
    assert tc.id is not None
    assert tc.priority == TestCasePriority.HIGH
    assert tc.status == TestCaseStatus.READY


def test_test_case_steps_json(db):
    u = make_user(db, "tc_steps@example.com")
    p = make_project(db, "TCSTEP", u.id)
    s = make_suite(db, p.id, u.id)
    steps = [{"order": 1, "action": "Open page"}, {"order": 2, "action": "Click button"}]
    tc = TestCase(
        suite_id=s.id,
        title="Steps TC",
        expected_result="Page loads.",
        priority=TestCasePriority.MEDIUM,
        status=TestCaseStatus.DRAFT,
        created_by=u.id,
        steps=steps,
    )
    db.add(tc)
    db.flush()
    db.refresh(tc)
    assert tc.steps == steps


def test_test_case_priority_values():
    assert set(TestCasePriority) == {
        TestCasePriority.LOW, TestCasePriority.MEDIUM,
        TestCasePriority.HIGH, TestCasePriority.CRITICAL,
    }


def test_test_case_status_values():
    assert set(TestCaseStatus) == {
        TestCaseStatus.DRAFT, TestCaseStatus.READY, TestCaseStatus.DEPRECATED
    }


# ---------------------------------------------------------------------------
# TestRun model
# ---------------------------------------------------------------------------

def test_test_run_create(db):
    u = make_user(db, "run_owner@example.com")
    p = make_project(db, "RUNP", u.id)
    r = make_run(db, p.id, u.id)
    assert r.id is not None
    assert r.status == TestRunStatus.NOT_STARTED


def test_test_run_status_values():
    assert set(TestRunStatus) == {
        TestRunStatus.NOT_STARTED, TestRunStatus.IN_PROGRESS,
        TestRunStatus.COMPLETED, TestRunStatus.ABORTED,
    }


# ---------------------------------------------------------------------------
# TestResult model
# ---------------------------------------------------------------------------

def test_test_result_create(db):
    u = make_user(db, "result_owner@example.com")
    p = make_project(db, "RESP", u.id)
    s = make_suite(db, p.id, u.id)
    tc = make_test_case(db, s.id, u.id)
    r = make_run(db, p.id, u.id)
    result = TestResult(
        test_run_id=r.id,
        test_case_id=tc.id,
        status=TestResultStatus.PASSED,
        executed_by=u.id,
    )
    db.add(result)
    db.flush()
    assert result.id is not None
    assert result.status == TestResultStatus.PASSED


def test_test_result_unique_per_run_and_case(db):
    u = make_user(db, "result_dup@example.com")
    p = make_project(db, "RDUP", u.id)
    s = make_suite(db, p.id, u.id)
    tc = make_test_case(db, s.id, u.id)
    r = make_run(db, p.id, u.id)
    db.add(TestResult(test_run_id=r.id, test_case_id=tc.id, status=TestResultStatus.NOT_RUN))
    db.flush()
    with pytest.raises(IntegrityError):
        db.add(TestResult(test_run_id=r.id, test_case_id=tc.id, status=TestResultStatus.PASSED))
        db.flush()


def test_test_result_executed_by_nullable(db):
    u = make_user(db, "result_null@example.com")
    p = make_project(db, "RNULL", u.id)
    s = make_suite(db, p.id, u.id)
    tc = make_test_case(db, s.id, u.id)
    r = make_run(db, p.id, u.id)
    result = TestResult(
        test_run_id=r.id, test_case_id=tc.id,
        status=TestResultStatus.NOT_RUN, executed_by=None,
    )
    db.add(result)
    db.flush()
    assert result.executed_by is None


# ---------------------------------------------------------------------------
# Defect model
# ---------------------------------------------------------------------------

def test_defect_create(db):
    u = make_user(db, "defect_owner@example.com")
    p = make_project(db, "DEFP", u.id)
    d = Defect(
        project_id=p.id,
        title="Login button missing",
        severity=DefectSeverity.CRITICAL,
        priority=DefectPriority.HIGH,
        status=DefectStatus.OPEN,
        created_by=u.id,
    )
    db.add(d)
    db.flush()
    assert d.id is not None
    assert d.status == DefectStatus.OPEN


def test_defect_test_case_nullable(db):
    u = make_user(db, "defect_null@example.com")
    p = make_project(db, "DEFNULL", u.id)
    d = Defect(
        project_id=p.id,
        title="Orphan defect",
        severity=DefectSeverity.MINOR,
        priority=DefectPriority.LOW,
        status=DefectStatus.OPEN,
        created_by=u.id,
        test_case_id=None,
        assigned_to=None,
    )
    db.add(d)
    db.flush()
    assert d.test_case_id is None
    assert d.assigned_to is None


def test_defect_assigned_to_nullable(db):
    u = make_user(db, "defect_assign@example.com")
    p = make_project(db, "DEFASSIGN", u.id)
    d = Defect(
        project_id=p.id,
        title="Unassigned defect",
        severity=DefectSeverity.MAJOR,
        priority=DefectPriority.MEDIUM,
        status=DefectStatus.OPEN,
        created_by=u.id,
    )
    db.add(d)
    db.flush()
    assert d.assigned_to is None


def test_defect_severity_values():
    assert set(DefectSeverity) == {
        DefectSeverity.BLOCKER, DefectSeverity.CRITICAL, DefectSeverity.MAJOR,
        DefectSeverity.MINOR, DefectSeverity.TRIVIAL,
    }


def test_defect_status_values():
    assert set(DefectStatus) == {
        DefectStatus.OPEN, DefectStatus.IN_PROGRESS, DefectStatus.RESOLVED,
        DefectStatus.CLOSED, DefectStatus.REJECTED,
    }


# ---------------------------------------------------------------------------
# Relationship traversal
# ---------------------------------------------------------------------------

def test_project_test_suites_relationship(db):
    u = make_user(db, "rel_suite@example.com")
    p = make_project(db, "RELTS", u.id)
    make_suite(db, p.id, u.id, "Suite X")
    make_suite(db, p.id, u.id, "Suite Y")
    db.refresh(p)
    assert len(p.test_suites) == 2


def test_suite_test_cases_relationship(db):
    u = make_user(db, "rel_tc@example.com")
    p = make_project(db, "RELTC", u.id)
    s = make_suite(db, p.id, u.id)
    make_test_case(db, s.id, u.id, "TC A")
    make_test_case(db, s.id, u.id, "TC B")
    db.refresh(s)
    assert len(s.test_cases) == 2


def test_run_results_relationship(db):
    u = make_user(db, "rel_run@example.com")
    p = make_project(db, "RELRUN", u.id)
    s = make_suite(db, p.id, u.id)
    tc1 = make_test_case(db, s.id, u.id, "TC Run 1")
    tc2 = make_test_case(db, s.id, u.id, "TC Run 2")
    r = make_run(db, p.id, u.id)
    db.add(TestResult(test_run_id=r.id, test_case_id=tc1.id, status=TestResultStatus.PASSED))
    db.add(TestResult(test_run_id=r.id, test_case_id=tc2.id, status=TestResultStatus.FAILED))
    db.flush()
    db.refresh(r)
    assert len(r.test_results) == 2
