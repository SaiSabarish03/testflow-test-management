from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships — back-references populated by other models
    created_projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined]
        "Project", foreign_keys="Project.created_by", back_populates="creator"
    )
    project_memberships: Mapped[list["ProjectMember"]] = relationship(  # type: ignore[name-defined]
        "ProjectMember", back_populates="user"
    )
    created_test_suites: Mapped[list["TestSuite"]] = relationship(  # type: ignore[name-defined]
        "TestSuite", foreign_keys="TestSuite.created_by", back_populates="creator"
    )
    created_test_cases: Mapped[list["TestCase"]] = relationship(  # type: ignore[name-defined]
        "TestCase", foreign_keys="TestCase.created_by", back_populates="creator"
    )
    created_test_runs: Mapped[list["TestRun"]] = relationship(  # type: ignore[name-defined]
        "TestRun", foreign_keys="TestRun.created_by", back_populates="creator"
    )
    executed_results: Mapped[list["TestResult"]] = relationship(  # type: ignore[name-defined]
        "TestResult", foreign_keys="TestResult.executed_by", back_populates="executor"
    )
    created_defects: Mapped[list["Defect"]] = relationship(  # type: ignore[name-defined]
        "Defect", foreign_keys="Defect.created_by", back_populates="creator"
    )
    assigned_defects: Mapped[list["Defect"]] = relationship(  # type: ignore[name-defined]
        "Defect", foreign_keys="Defect.assigned_to", back_populates="assignee"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
