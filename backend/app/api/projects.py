from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole, ProjectStatus
from app.models.user import User
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])

_admin_only = Depends(require_roles(UserRole.ADMIN))
_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))
_any_authenticated = Depends(get_current_user)


def _svc(db: Annotated[Session, Depends(get_db)]) -> ProjectService:
    return ProjectService(db)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    search: str | None = Query(default=None),
    status: ProjectStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _any_authenticated,
    svc: ProjectService = Depends(_svc),
) -> ProjectListResponse:
    items, total = svc.list_projects(search=search, status=status, page=page, page_size=page_size)
    return ProjectListResponse.build(items, total, page, page_size)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = _admin_or_qa,
    svc: ProjectService = Depends(_svc),
) -> ProjectResponse:
    project = svc.create_project(payload, created_by=current_user.id)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    _: User = _any_authenticated,
    svc: ProjectService = Depends(_svc),
) -> ProjectResponse:
    return ProjectResponse.model_validate(svc.get_project(project_id))


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    _: User = _admin_or_qa,
    svc: ProjectService = Depends(_svc),
) -> ProjectResponse:
    return ProjectResponse.model_validate(svc.update_project(project_id, payload))


@router.delete("/{project_id}", response_model=ProjectResponse)
def archive_project(
    project_id: int,
    _: User = _admin_or_qa,
    svc: ProjectService = Depends(_svc),
) -> ProjectResponse:
    """Archives the project (sets status=ARCHIVED). Preserves all historical test data."""
    return ProjectResponse.model_validate(svc.archive_project(project_id))
