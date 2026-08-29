from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TestResultStatus


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id"), nullable=False
    )
    status: Mapped[TestResultStatus] = mapped_column(
        SAEnum(TestResultStatus), nullable=False, default=TestResultStatus.NOT_RUN
    )
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    test_run: Mapped["TestRun"] = relationship(  # type: ignore[name-defined]
        "TestRun", back_populates="test_results"
    )
    test_case: Mapped["TestCase"] = relationship(  # type: ignore[name-defined]
        "TestCase", back_populates="test_results"
    )
    executor: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[executed_by], back_populates="executed_results"
    )

    __table_args__ = (
        # One result record per test case per run
        UniqueConstraint("test_run_id", "test_case_id", name="uq_result_run_case"),
    )

    def __repr__(self) -> str:
        return (
            f"<TestResult run={self.test_run_id} case={self.test_case_id} "
            f"status={self.status}>"
        )
