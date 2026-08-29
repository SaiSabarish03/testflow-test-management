from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole, DefectSeverity, DefectPriority, DefectStatus
from app.models.user import User
from app.schemas.defects import DefectCreate, DefectUpdate, DefectResponse, DefectListResponse
from app.services.defect_service import DefectService

router = APIRouter(prefix="/api/defects", tags=["defects"])

_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))
_any_authenticated = Depends(get_current_user)


def _svc(db: Annotated[Session, Depends(get_db)]) -> DefectService:
    return DefectService(db)


@router.post("", response_model=DefectResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a defect")
def create_defect(
    payload: DefectCreate,
    current_user: User = _admin_or_qa,
    svc: DefectService = Depends(_svc),
) -> DefectResponse:
    defect = svc.create_defect(payload=payload, created_by=current_user.id)
    return DefectResponse.model_validate(defect)


@router.get("", response_model=DefectListResponse, summary="List defects")
def list_defects(
    project_id: int | None = Query(default=None),
    test_case_id: int | None = Query(default=None),
    severity: DefectSeverity | None = Query(default=None),
    priority: DefectPriority | None = Query(default=None),
    status: DefectStatus | None = Query(default=None),
    assigned_to: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: DefectService = Depends(_svc),
) -> DefectListResponse:
    items, total = svc.list_defects(
        project_id=project_id,
        test_case_id=test_case_id,
        severity=severity,
        priority=priority,
        status=status,
        assigned_to=assigned_to,
        search=search,
        page=page,
        page_size=page_size,
    )
    return DefectListResponse.build(items, total, page, page_size)


@router.get("/{defect_id}", response_model=DefectResponse, summary="Get a defect by ID")
def get_defect(
    defect_id: int,
    _: User = _any_authenticated,
    svc: DefectService = Depends(_svc),
) -> DefectResponse:
    return DefectResponse.model_validate(svc.get_defect(defect_id))


@router.put("/{defect_id}", response_model=DefectResponse, summary="Update a defect")
def update_defect(
    defect_id: int,
    payload: DefectUpdate,
    _: User = _admin_or_qa,
    svc: DefectService = Depends(_svc),
) -> DefectResponse:
    return DefectResponse.model_validate(svc.update_defect(defect_id, payload))


@router.delete("/{defect_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a defect")
def delete_defect(
    defect_id: int,
    _: User = _admin_or_qa,
    svc: DefectService = Depends(_svc),
) -> None:
    svc.delete_defect(defect_id)
