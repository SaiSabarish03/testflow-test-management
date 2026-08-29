from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dependencies.db import get_db
from app.models.user import User
from app.models.enums import UserRole, UserStatus

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    FastAPI dependency — extract and validate the Bearer JWT, return the active User.

    Raises HTTP 401 for any authentication failure.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise _unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError:
        raise _unauthorized

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized

    if user.status == UserStatus.INACTIVE:
        raise _unauthorized

    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """
    Dependency factory — returns a dependency that enforces role membership.

    Usage:
        @router.delete(..., dependencies=[Depends(require_roles(UserRole.ADMIN))])

    Or as a typed dependency:
        current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.QA_ENGINEER))

    Returns the authenticated User on success.
    Raises HTTP 403 when the user's role is not in the allowed set.
    """
    def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check
