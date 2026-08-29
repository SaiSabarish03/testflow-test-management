from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.models.enums import UserRole, UserStatus


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._db.query(User).filter(User.email == email).first()

    def list(
        self,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        q = self._db.query(User)
        if search:
            pattern = f"%{search}%"
            q = q.filter(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
        if role:
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(self, name: str, email: str, password_hash: str, role: UserRole, status: UserStatus = UserStatus.ACTIVE) -> User:
        user = User(name=name, email=email, password_hash=password_hash, role=role, status=status)
        self._db.add(user)
        self._db.flush()
        return user

    def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            setattr(user, key, value)
        self._db.flush()
        return user

    def deactivate(self, user: User) -> User:
        user.status = UserStatus.INACTIVE
        self._db.flush()
        return user
