from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TestRunStatus


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[TestRunStatus] = mapped_column(
        SAEnum(TestRunStatus), nullable=False, default=TestRunStatus.NOT_STARTED
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="test_runs"
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[created_by], back_populates="created_test_runs"
    )
    test_results: Mapped[list["TestResult"]] = relationship(  # type: ignore[name-defined]
        "TestResult", back_populates="test_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_test_runs_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<TestRun id={self.id} name={self.name!r} status={self.status}>"
