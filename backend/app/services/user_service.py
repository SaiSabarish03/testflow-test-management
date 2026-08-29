from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.enums import UserRole, UserStatus
from app.repositories.user_repository import UserRepository
from app.schemas.users import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = UserRepository(db)

    def list_users(
        self,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        return self._repo.list(search=search, role=role, status=status, page=page, page_size=page_size)

    def get_user(self, user_id: int) -> User:
        user = self._repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def create_user(self, payload: UserCreate) -> User:
        if self._repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = self._repo.create(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
            status=payload.status,
        )
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        updates = payload.model_dump(exclude_none=True)

        if "email" in updates and updates["email"] != user.email:
            if self._repo.get_by_email(updates["email"]):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if "password" in updates:
            updates["password_hash"] = hash_password(updates.pop("password"))

        user = self._repo.update(user, **updates)
        self._db.commit()
        self._db.refresh(user)
        return user

    def deactivate_user(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user = self._repo.deactivate(user)
        self._db.commit()
        self._db.refresh(user)
        return user
