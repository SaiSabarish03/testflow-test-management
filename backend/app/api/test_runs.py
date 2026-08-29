from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole, TestRunStatus, TestResultStatus
from app.models.user import User
from app.schemas.test_runs import (
    TestRunCreate,
    TestRunResponse,
    TestRunListResponse,
    TestRunSummaryResponse,
    TestResultUpdate,
    TestResultResponse,
    TestResultListResponse,
)
from app.services.test_run_service import TestRunService

router = APIRouter(tags=["test-runs"])

_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))
_any_authenticated = Depends(get_current_user)


def _svc(db: Annotated[Session, Depends(get_db)]) -> TestRunService:
    return TestRunService(db)


# ---------------------------------------------------------------------------
# Runs under a project
# ---------------------------------------------------------------------------

@router.post(
    "/api/projects/{project_id}/runs",
    response_model=TestRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a test run",
)
def create_run(
    project_id: int,
    payload: TestRunCreate,
    current_user: User = _admin_or_qa,
    svc: TestRunService = Depends(_svc),
) -> TestRunResponse:
    run = svc.create_run(project_id=project_id, payload=payload, created_by=current_user.id)
    return TestRunResponse.model_validate(run)


@router.get(
    "/api/projects/{project_id}/runs",
    response_model=TestRunListResponse,
    summary="List test runs for a project",
)
def list_runs(
    project_id: int,
    search: str | None = Query(default=None),
    status: TestRunStatus | None = Query(default=None),
    environment: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: TestRunService = Depends(_svc),
) -> TestRunListResponse:
    items, total = svc.list_runs(
        project_id=project_id,
        search=search,
        status=status,
        environment=environment,
        page=page,
        page_size=page_size,
    )
    return TestRunListResponse.build(items, total, page, page_size)


# ---------------------------------------------------------------------------
# Individual run operations
# ---------------------------------------------------------------------------

@router.get(
    "/api/runs/{run_id}",
    response_model=TestRunResponse,
    summary="Get a test run by ID",
)
def get_run(
    run_id: int,
    _: User = _any_authenticated,
    svc: TestRunService = Depends(_svc),
) -> TestRunResponse:
    return TestRunResponse.model_validate(svc.get_run(run_id))


@router.post(
    "/api/runs/{run_id}/start",
    response_model=TestRunResponse,
    summary="Start a test run (NOT_STARTED → IN_PROGRESS)",
)
def start_run(
    run_id: int,
    _: User = _admin_or_qa,
    svc: TestRunService = Depends(_svc),
) -> TestRunResponse:
    return TestRunResponse.model_validate(svc.start_run(run_id))


@router.post(
    "/api/runs/{run_id}/complete",
    response_model=TestRunResponse,
    summary="Complete a test run (IN_PROGRESS → COMPLETED)",
)
def complete_run(
    run_id: int,
    _: User = _admin_or_qa,
    svc: TestRunService = Depends(_svc),
) -> TestRunResponse:
    return TestRunResponse.model_validate(svc.complete_run(run_id))


@router.post(
    "/api/runs/{run_id}/abort",
    response_model=TestRunResponse,
    summary="Abort a test run (IN_PROGRESS → ABORTED)",
)
def abort_run(
    run_id: int,
    _: User = _admin_or_qa,
    svc: TestRunService = Depends(_svc),
) -> TestRunResponse:
    return TestRunResponse.model_validate(svc.abort_run(run_id))


@router.get(
    "/api/runs/{run_id}/summary",
    response_model=TestRunSummaryResponse,
    summary="Get result summary for a test run",
)
def get_summary(
    run_id: int,
    _: User = _any_authenticated,
    svc: TestRunService = Depends(_svc),
) -> TestRunSummaryResponse:
    return svc.get_summary(run_id)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@router.get(
    "/api/runs/{run_id}/results",
    response_model=TestResultListResponse,
    summary="List results for a test run",
)
def list_results(
    run_id: int,
    status: TestResultStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: TestRunService = Depends(_svc),
) -> TestResultListResponse:
    items, total = svc.list_results(run_id=run_id, status=status, page=page, page_size=page_size)
    return TestResultListResponse.build(items, total, page, page_size)


@router.put(
    "/api/runs/{run_id}/results/{result_id}",
    response_model=TestResultResponse,
    summary="Record a test result",
)
def record_result(
    run_id: int,
    result_id: int,
    payload: TestResultUpdate,
    current_user: User = _admin_or_qa,
    svc: TestRunService = Depends(_svc),
) -> TestResultResponse:
    result = svc.record_result(
        run_id=run_id,
        result_id=result_id,
        payload=payload,
        executed_by=current_user.id,
    )
    return TestResultResponse.model_validate(result)
