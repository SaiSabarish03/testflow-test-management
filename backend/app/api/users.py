from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.db import get_db
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])

_admin_only = Depends(require_roles(UserRole.ADMIN))
_admin_or_qa = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))


def _svc(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


@router.get("", response_model=UserListResponse)
def list_users(
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = _admin_or_qa,
    svc: UserService = Depends(_svc),
) -> UserListResponse:
    items, total = svc.list_users(search=search, role=role, status=status, page=page, page_size=page_size)
    return UserListResponse.build(items, total, page, page_size)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = _admin_only,
    svc: UserService = Depends(_svc),
) -> UserResponse:
    user = svc.create_user(payload)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    _: User = _admin_or_qa,
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return UserResponse.model_validate(svc.get_user(user_id))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    _: User = _admin_only,
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return UserResponse.model_validate(svc.update_user(user_id, payload))


@router.delete("/{user_id}", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    _: User = _admin_only,
    svc: UserService = Depends(_svc),
) -> UserResponse:
    """Soft-deactivates the user (sets status=INACTIVE). Does not physically delete."""
    return UserResponse.model_validate(svc.deactivate_user(user_id))
