from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.test_suites import TestSuiteCreate, TestSuiteUpdate, TestSuiteResponse, TestSuiteListResponse
from app.services.test_suite_service import TestSuiteService

router = APIRouter(tags=["test-suites"])

_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))
_any_authenticated = Depends(get_current_user)


def _svc(db: Annotated[Session, Depends(get_db)]) -> TestSuiteService:
    return TestSuiteService(db)


@router.get("/api/projects/{project_id}/suites", response_model=TestSuiteListResponse)
def list_suites(
    project_id: int,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: TestSuiteService = Depends(_svc),
) -> TestSuiteListResponse:
    items, total = svc.list_suites(project_id=project_id, search=search, page=page, page_size=page_size)
    return TestSuiteListResponse.build(items, total, page, page_size)


@router.post("/api/projects/{project_id}/suites", response_model=TestSuiteResponse, status_code=status.HTTP_201_CREATED)
def create_suite(
    project_id: int,
    payload: TestSuiteCreate,
    current_user: User = _admin_or_qa,
    svc: TestSuiteService = Depends(_svc),
) -> TestSuiteResponse:
    suite = svc.create_suite(project_id=project_id, payload=payload, created_by=current_user.id)
    return TestSuiteResponse.model_validate(suite)


@router.get("/api/suites/{suite_id}", response_model=TestSuiteResponse)
def get_suite(
    suite_id: int,
    _: User = _any_authenticated,
    svc: TestSuiteService = Depends(_svc),
) -> TestSuiteResponse:
    return TestSuiteResponse.model_validate(svc.get_suite(suite_id))


@router.put("/api/suites/{suite_id}", response_model=TestSuiteResponse)
def update_suite(
    suite_id: int,
    payload: TestSuiteUpdate,
    _: User = _admin_or_qa,
    svc: TestSuiteService = Depends(_svc),
) -> TestSuiteResponse:
    return TestSuiteResponse.model_validate(svc.update_suite(suite_id, payload))


@router.delete("/api/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suite(
    suite_id: int,
    _: User = _admin_or_qa,
    svc: TestSuiteService = Depends(_svc),
) -> None:
    svc.delete_suite(suite_id)
