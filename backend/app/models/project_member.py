from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="members"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="project_memberships"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members"),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember project_id={self.project_id} user_id={self.user_id}>"
