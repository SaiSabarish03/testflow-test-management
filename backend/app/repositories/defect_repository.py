from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.defect import Defect
from app.models.enums import DefectSeverity, DefectPriority, DefectStatus


class DefectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, defect_id: int) -> Defect | None:
        return self._db.get(Defect, defect_id)

    def list(
        self,
        project_id: int | None = None,
        test_case_id: int | None = None,
        severity: DefectSeverity | None = None,
        priority: DefectPriority | None = None,
        status: DefectStatus | None = None,
        assigned_to: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Defect], int]:
        q = self._db.query(Defect)
        if project_id is not None:
            q = q.filter(Defect.project_id == project_id)
        if test_case_id is not None:
            q = q.filter(Defect.test_case_id == test_case_id)
        if severity is not None:
            q = q.filter(Defect.severity == severity)
        if priority is not None:
            q = q.filter(Defect.priority == priority)
        if status is not None:
            q = q.filter(Defect.status == status)
        if assigned_to is not None:
            q = q.filter(Defect.assigned_to == assigned_to)
        if search:
            q = q.filter(Defect.title.ilike(f"%{search}%"))
        total = q.count()
        items = q.order_by(Defect.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(
        self,
        project_id: int,
        title: str,
        severity: DefectSeverity,
        priority: DefectPriority,
        created_by: int,
        description: str | None = None,
        environment: str | None = None,
        test_case_id: int | None = None,
        assigned_to: int | None = None,
    ) -> Defect:
        defect = Defect(
            project_id=project_id,
            title=title,
            severity=severity,
            priority=priority,
            created_by=created_by,
            description=description,
            environment=environment,
            test_case_id=test_case_id,
            assigned_to=assigned_to,
            status=DefectStatus.OPEN,
        )
        self._db.add(defect)
        self._db.flush()
        return defect

    def update(self, defect: Defect, **fields) -> Defect:
        for key, value in fields.items():
            setattr(defect, key, value)
        self._db.flush()
        return defect

    def delete(self, defect: Defect) -> None:
        self._db.delete(defect)
        self._db.flush()
