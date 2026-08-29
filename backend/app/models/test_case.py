from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SAEnum, func, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Any

from app.core.database import Base
from app.models.enums import TestCasePriority, TestCaseStatus


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("test_suites.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # steps stored as JSON array: [{"order": 1, "action": "..."}]
    steps: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[TestCasePriority] = mapped_column(
        SAEnum(TestCasePriority), nullable=False
    )
    status: Mapped[TestCaseStatus] = mapped_column(
        SAEnum(TestCaseStatus), nullable=False, default=TestCaseStatus.DRAFT
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    suite: Mapped["TestSuite"] = relationship(  # type: ignore[name-defined]
        "TestSuite", back_populates="test_cases"
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[created_by], back_populates="created_test_cases"
    )
    test_results: Mapped[list["TestResult"]] = relationship(  # type: ignore[name-defined]
        "TestResult", back_populates="test_case"
    )
    defects: Mapped[list["Defect"]] = relationship(  # type: ignore[name-defined]
        "Defect", back_populates="test_case"
    )

    __table_args__ = (
        Index("ix_test_cases_title", "title"),
        Index("ix_test_cases_priority", "priority"),
        Index("ix_test_cases_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<TestCase id={self.id} title={self.title!r} priority={self.priority}>"
