from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SAEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DefectSeverity, DefectPriority, DefectStatus


class Defect(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    test_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_cases.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[DefectSeverity] = mapped_column(
        SAEnum(DefectSeverity), nullable=False
    )
    priority: Mapped[DefectPriority] = mapped_column(
        SAEnum(DefectPriority), nullable=False
    )
    environment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DefectStatus] = mapped_column(
        SAEnum(DefectStatus), nullable=False, default=DefectStatus.OPEN
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="defects"
    )
    test_case: Mapped["TestCase | None"] = relationship(  # type: ignore[name-defined]
        "TestCase", back_populates="defects"
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[created_by], back_populates="created_defects"
    )
    assignee: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[assigned_to], back_populates="assigned_defects"
    )

    __table_args__ = (
        Index("ix_defects_status", "status"),
        Index("ix_defects_severity", "severity"),
        Index("ix_defects_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Defect id={self.id} title={self.title!r} status={self.status}>"
