from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.defect import Defect
from app.models.enums import DefectStatus, UserStatus
from app.repositories.defect_repository import DefectRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.repositories.user_repository import UserRepository
from app.schemas.defects import DefectCreate, DefectUpdate

# ---------------------------------------------------------------------------
# Lifecycle — allowed transitions
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[DefectStatus, set[DefectStatus]] = {
    DefectStatus.OPEN:        {DefectStatus.IN_PROGRESS, DefectStatus.REJECTED},
    DefectStatus.IN_PROGRESS: {DefectStatus.RESOLVED, DefectStatus.REJECTED},
    DefectStatus.RESOLVED:    {DefectStatus.CLOSED, DefectStatus.IN_PROGRESS},
    DefectStatus.REJECTED:    {DefectStatus.OPEN},
    DefectStatus.CLOSED:      set(),
}


class DefectService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = DefectRepository(db)
        self._project_repo = ProjectRepository(db)
        self._case_repo = TestCaseRepository(db)
        self._user_repo = UserRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_404(self, defect_id: int) -> Defect:
        defect = self._repo.get_by_id(defect_id)
        if defect is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Defect not found")
        return defect

    def _validate_project(self, project_id: int):
        project = self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def _validate_test_case(self, test_case_id: int, project_id: int):
        tc = self._case_repo.get_by_id(test_case_id)
        if tc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        if tc.suite.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test case {test_case_id} does not belong to project {project_id}",
            )
        return tc

    def _validate_assignee(self, assigned_to: int):
        user = self._user_repo.get_by_id(assigned_to)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
        if user.status == UserStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign defect to an inactive user",
            )
        return user

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_defects(
        self,
        project_id: int | None = None,
        test_case_id: int | None = None,
        severity=None,
        priority=None,
        status=None,
        assigned_to: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Defect], int]:
        return self._repo.list(
            project_id=project_id,
            test_case_id=test_case_id,
            severity=severity,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            search=search,
            page=page,
            page_size=page_size,
        )

    def get_defect(self, defect_id: int) -> Defect:
        return self._get_or_404(defect_id)

    def create_defect(self, payload: DefectCreate, created_by: int) -> Defect:
        self._validate_project(payload.project_id)
        if payload.test_case_id is not None:
            self._validate_test_case(payload.test_case_id, payload.project_id)
        if payload.assigned_to is not None:
            self._validate_assignee(payload.assigned_to)

        defect = self._repo.create(
            project_id=payload.project_id,
            title=payload.title,
            severity=payload.severity,
            priority=payload.priority,
            created_by=created_by,
            description=payload.description,
            environment=payload.environment,
            test_case_id=payload.test_case_id,
            assigned_to=payload.assigned_to,
        )
        self._db.commit()
        self._db.refresh(defect)
        return defect

    def update_defect(self, defect_id: int, payload: DefectUpdate) -> Defect:
        defect = self._get_or_404(defect_id)

        # Validate status transition if status is being changed
        if payload.status is not None and payload.status != defect.status:
            allowed = _ALLOWED_TRANSITIONS[defect.status]
            if payload.status not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot transition defect from {defect.status} to {payload.status}",
                )

        # Validate new assignee if provided
        if payload.assigned_to is not None:
            self._validate_assignee(payload.assigned_to)

        updates = payload.model_dump(exclude_unset=True)
        self._repo.update(defect, **updates)
        self._db.commit()
        self._db.refresh(defect)
        return defect

    def delete_defect(self, defect_id: int) -> None:
        """
        Physical deletion. Defects are historical QA artifacts; deletion is
        permitted only when the defect has no downstream dependencies that
        would lose traceability. The current schema has no child tables that
        reference defects, so physical deletion is safe. If a defect-comments
        or defect-attachments table is added in a future phase, this method
        should check for those dependencies first and return 409 if any exist.
        """
        defect = self._get_or_404(defect_id)
        self._repo.delete(defect)
        self._db.commit()
