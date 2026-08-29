"""
Seed script — creates realistic development data.

Usage:
    cd backend
    python -m seed.seed

Safe to run multiple times — existing records are skipped by email/key lookup.
Passwords are hashed with bcrypt. Never commit real credentials.

Development credentials (local only):
    admin@testflow.local   / Admin123!
    qa@testflow.local      / QaPass123!
    viewer@testflow.local  / View123!
"""
from datetime import datetime, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.test_suite import TestSuite
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.defect import Defect
from app.models.enums import (
    UserRole, UserStatus,
    ProjectStatus,
    TestCasePriority, TestCaseStatus,
    TestRunStatus, TestResultStatus,
    DefectSeverity, DefectPriority, DefectStatus,
)

from app.core.security import hash_password


def _hash(password: str) -> str:
    return hash_password(password)


def _get_or_create_user(
    db: Session, email: str, name: str, password: str, role: UserRole
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=_hash(password),
            role=role,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        print(f"  Created user: {email}")
    return user


def _get_or_create_project(
    db: Session, key: str, name: str, description: str, created_by: int
) -> Project:
    project = db.query(Project).filter(Project.key == key).first()
    if not project:
        project = Project(
            name=name,
            key=key,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_by=created_by,
        )
        db.add(project)
        db.flush()
        print(f"  Created project: {key}")
    return project


def run(db: Session) -> None:
    print("Seeding users...")
    admin = _get_or_create_user(db, "admin@testflow.local", "Admin User", "Admin123!", UserRole.ADMIN)
    qa = _get_or_create_user(db, "qa@testflow.local", "QA Engineer", "QaPass123!", UserRole.QA_ENGINEER)
    viewer = _get_or_create_user(db, "viewer@testflow.local", "Viewer User", "View123!", UserRole.VIEWER)

    print("Seeding projects...")
    p1 = _get_or_create_project(
        db, "TFW", "TestFlow Web",
        "The TestFlow web application — primary system under test.",
        admin.id,
    )
    p2 = _get_or_create_project(
        db, "MOBILE", "TestFlow Mobile",
        "Mobile companion app for TestFlow.",
        admin.id,
    )

    # Project members
    for project_id, user_id in [
        (p1.id, qa.id), (p1.id, viewer.id),
        (p2.id, qa.id),
    ]:
        exists = db.query(ProjectMember).filter_by(
            project_id=project_id, user_id=user_id
        ).first()
        if not exists:
            db.add(ProjectMember(project_id=project_id, user_id=user_id))

    db.flush()
    print("  Project members added.")

    print("Seeding test suites...")
    suite_defs = [
        ("Authentication", "Login, logout, and session management test cases."),
        ("Project Management", "Create, update, archive, and search projects."),
        ("Test Case Management", "CRUD operations and validation for test cases."),
        ("Test Execution", "Test run creation and result recording."),
        ("Defect Management", "Defect lifecycle from creation to resolution."),
    ]
    suites: list[TestSuite] = []
    for name, desc in suite_defs:
        suite = db.query(TestSuite).filter_by(project_id=p1.id, name=name).first()
        if not suite:
            suite = TestSuite(
                project_id=p1.id, name=name, description=desc, created_by=qa.id
            )
            db.add(suite)
            db.flush()
            print(f"  Created suite: {name}")
        suites.append(suite)

    auth_suite, proj_suite, tc_suite, exec_suite, defect_suite = suites

    print("Seeding test cases...")
    tc_defs = [
        (
            auth_suite.id,
            "Verify valid login",
            "User is on the login page.",
            [
                {"order": 1, "action": "Navigate to /login"},
                {"order": 2, "action": "Enter valid email and password"},
                {"order": 3, "action": "Click Login button"},
            ],
            "User is redirected to the dashboard.",
            TestCasePriority.CRITICAL,
            TestCaseStatus.READY,
        ),
        (
            auth_suite.id,
            "Verify invalid password is rejected",
            "User is on the login page.",
            [
                {"order": 1, "action": "Navigate to /login"},
                {"order": 2, "action": "Enter valid email and incorrect password"},
                {"order": 3, "action": "Click Login button"},
            ],
            "Error message is displayed. User remains on login page.",
            TestCasePriority.CRITICAL,
            TestCaseStatus.READY,
        ),
        (
            auth_suite.id,
            "Verify inactive user cannot log in",
            "An INACTIVE user account exists in the system.",
            [
                {"order": 1, "action": "Attempt login with inactive user credentials"},
            ],
            "Login is rejected with an appropriate error message.",
            TestCasePriority.HIGH,
            TestCaseStatus.READY,
        ),
        (
            proj_suite.id,
            "Verify project creation with valid data",
            "User is authenticated as QA_ENGINEER or ADMIN.",
            [
                {"order": 1, "action": "Navigate to Projects page"},
                {"order": 2, "action": "Click Create Project"},
                {"order": 3, "action": "Fill in name, key, and description"},
                {"order": 4, "action": "Submit the form"},
            ],
            "Project is created and appears in the project list.",
            TestCasePriority.HIGH,
            TestCaseStatus.READY,
        ),
        (
            proj_suite.id,
            "Verify duplicate project key is rejected",
            "A project with key 'TFW' already exists.",
            [
                {"order": 1, "action": "Attempt to create a project with key 'TFW'"},
            ],
            "API returns 409 Conflict. Project is not created.",
            TestCasePriority.HIGH,
            TestCaseStatus.READY,
        ),
        (
            tc_suite.id,
            "Verify test case creation with all fields",
            "A test suite exists in an active project.",
            [
                {"order": 1, "action": "Navigate to the test suite"},
                {"order": 2, "action": "Click Add Test Case"},
                {"order": 3, "action": "Fill in all required fields"},
                {"order": 4, "action": "Submit"},
            ],
            "Test case is created and visible in the suite.",
            TestCasePriority.MEDIUM,
            TestCaseStatus.READY,
        ),
        (
            tc_suite.id,
            "Verify deprecated test case cannot be added to new run",
            "A test case with status DEPRECATED exists.",
            [
                {"order": 1, "action": "Create a new test run"},
                {"order": 2, "action": "Attempt to add the deprecated test case"},
            ],
            "API returns 400. Deprecated test case is not added.",
            TestCasePriority.MEDIUM,
            TestCaseStatus.READY,
        ),
        (
            exec_suite.id,
            "Verify test result can be recorded as PASSED",
            "A test run is IN_PROGRESS with at least one test case.",
            [
                {"order": 1, "action": "Open the test run"},
                {"order": 2, "action": "Select a test case result"},
                {"order": 3, "action": "Set status to PASSED"},
                {"order": 4, "action": "Save"},
            ],
            "Result is saved as PASSED and visible in the run summary.",
            TestCasePriority.HIGH,
            TestCaseStatus.READY,
        ),
        (
            defect_suite.id,
            "Verify defect creation with required fields",
            "User is authenticated as QA_ENGINEER or ADMIN.",
            [
                {"order": 1, "action": "Navigate to Defects"},
                {"order": 2, "action": "Click Create Defect"},
                {"order": 3, "action": "Fill in title, severity, and priority"},
                {"order": 4, "action": "Submit"},
            ],
            "Defect is created with status OPEN.",
            TestCasePriority.HIGH,
            TestCaseStatus.READY,
        ),
    ]

    created_cases: list[TestCase] = []
    for suite_id, title, precond, steps, expected, priority, status in tc_defs:
        tc = db.query(TestCase).filter_by(suite_id=suite_id, title=title).first()
        if not tc:
            tc = TestCase(
                suite_id=suite_id,
                title=title,
                preconditions=precond,
                steps=steps,
                expected_result=expected,
                priority=priority,
                status=status,
                created_by=qa.id,
            )
            db.add(tc)
            db.flush()
            print(f"  Created test case: {title[:50]}")
        created_cases.append(tc)

    print("Seeding test run...")
    run_obj = db.query(TestRun).filter_by(project_id=p1.id, name="Regression Run - Release 1.0").first()
    if not run_obj:
        run_obj = TestRun(
            project_id=p1.id,
            name="Regression Run - Release 1.0",
            environment="QA",
            status=TestRunStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
            created_by=qa.id,
        )
        db.add(run_obj)
        db.flush()
        print("  Created test run.")

        # Add results for the first 4 test cases
        result_data = [
            (created_cases[0].id, TestResultStatus.PASSED, "Login succeeded, redirected to dashboard."),
            (created_cases[1].id, TestResultStatus.PASSED, "Error message displayed correctly."),
            (created_cases[2].id, TestResultStatus.NOT_RUN, None),
            (created_cases[3].id, TestResultStatus.FAILED, "Project was created but key validation was skipped."),
        ]
        for tc_id, status, actual in result_data:
            result = TestResult(
                test_run_id=run_obj.id,
                test_case_id=tc_id,
                status=status,
                actual_result=actual,
                executed_by=qa.id if status != TestResultStatus.NOT_RUN else None,
                executed_at=datetime.now(timezone.utc) if status != TestResultStatus.NOT_RUN else None,
            )
            db.add(result)
        db.flush()
        print("  Created test results.")

    print("Seeding defects...")
    defect_defs = [
        (
            "Login error message does not specify invalid password",
            "When an incorrect password is entered, the error message says 'Login failed' "
            "instead of providing a more specific message.",
            DefectSeverity.MINOR,
            DefectPriority.LOW,
            "QA",
            DefectStatus.OPEN,
            created_cases[1].id,
            qa.id,
        ),
        (
            "Project search does not filter archived projects",
            "When filtering by status=ACTIVE, archived projects still appear in results.",
            DefectSeverity.MAJOR,
            DefectPriority.HIGH,
            "QA",
            DefectStatus.IN_PROGRESS,
            created_cases[4].id,
            admin.id,
        ),
        (
            "Test run completion does not set completed_at timestamp",
            "Marking a test run as COMPLETED leaves the completed_at field as NULL.",
            DefectSeverity.MINOR,
            DefectPriority.MEDIUM,
            "QA",
            DefectStatus.RESOLVED,
            None,
            None,
        ),
    ]
    for title, desc, severity, priority, env, status, tc_id, assignee_id in defect_defs:
        exists = db.query(Defect).filter_by(project_id=p1.id, title=title).first()
        if not exists:
            db.add(Defect(
                project_id=p1.id,
                test_case_id=tc_id,
                title=title,
                description=desc,
                severity=severity,
                priority=priority,
                environment=env,
                status=status,
                created_by=qa.id,
                assigned_to=assignee_id,
            ))
            print(f"  Created defect: {title[:50]}")

    db.commit()
    print("\nSeed complete.")


def main() -> None:
    db = SessionLocal()
    try:
        run(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
