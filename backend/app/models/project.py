from datetime import datetime
from sqlalchemy import String, Text, Enum as SAEnum, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[created_by], back_populates="created_projects"
    )
    members: Mapped[list["ProjectMember"]] = relationship(  # type: ignore[name-defined]
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    test_suites: Mapped[list["TestSuite"]] = relationship(  # type: ignore[name-defined]
        "TestSuite", back_populates="project", cascade="all, delete-orphan"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(  # type: ignore[name-defined]
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )
    defects: Mapped[list["Defect"]] = relationship(  # type: ignore[name-defined]
        "Defect", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_projects_key", "key"),
        Index("ix_projects_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} key={self.key} status={self.status}>"
