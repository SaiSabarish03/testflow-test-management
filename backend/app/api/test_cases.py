from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole, TestCasePriority, TestCaseStatus
from app.models.user import User
from app.schemas.test_cases import TestCaseCreate, TestCaseUpdate, TestCaseResponse, TestCaseListResponse
from app.services.test_case_service import TestCaseService

router = APIRouter(tags=["test-cases"])

_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))
_any_authenticated = Depends(get_current_user)


def _svc(db: Annotated[Session, Depends(get_db)]) -> TestCaseService:
    return TestCaseService(db)


@router.get("/api/suites/{suite_id}/test-cases", response_model=TestCaseListResponse)
def list_test_cases(
    suite_id: int,
    search: str | None = Query(default=None),
    priority: TestCasePriority | None = Query(default=None),
    status: TestCaseStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: TestCaseService = Depends(_svc),
) -> TestCaseListResponse:
    items, total = svc.list_test_cases(
        suite_id=suite_id,
        search=search,
        priority=priority,
        status=status,
        page=page,
        page_size=page_size,
    )
    return TestCaseListResponse.build(items, total, page, page_size)


@router.post("/api/suites/{suite_id}/test-cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def create_test_case(
    suite_id: int,
    payload: TestCaseCreate,
    current_user: User = _admin_or_qa,
    svc: TestCaseService = Depends(_svc),
) -> TestCaseResponse:
    test_case = svc.create_test_case(suite_id=suite_id, payload=payload, created_by=current_user.id)
    return TestCaseResponse.model_validate(test_case)


@router.get("/api/test-cases/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(
    test_case_id: int,
    _: User = _any_authenticated,
    svc: TestCaseService = Depends(_svc),
) -> TestCaseResponse:
    return TestCaseResponse.model_validate(svc.get_test_case(test_case_id))


@router.put("/api/test-cases/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_case_id: int,
    payload: TestCaseUpdate,
    _: User = _admin_or_qa,
    svc: TestCaseService = Depends(_svc),
) -> TestCaseResponse:
    return TestCaseResponse.model_validate(svc.update_test_case(test_case_id, payload))


@router.delete("/api/test-cases/{test_case_id}", response_model=TestCaseResponse)
def delete_test_case(
    test_case_id: int,
    _: User = _admin_or_qa,
    svc: TestCaseService = Depends(_svc),
) -> TestCaseResponse:
    """Soft-deletes the testcase by setting status to DEPRECATED."""
    return TestCaseResponse.model_validate(svc.delete_test_case(test_case_id))
