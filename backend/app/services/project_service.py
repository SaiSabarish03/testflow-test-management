from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.enums import ProjectStatus
from app.repositories.project_repository import ProjectRepository
from app.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ProjectRepository(db)

    def list_projects(
        self,
        search: str | None = None,
        status: ProjectStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]:
        return self._repo.list(search=search, status=status, page=page, page_size=page_size)

    def get_project(self, project_id: int) -> Project:
        project = self._repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def create_project(self, payload: ProjectCreate, created_by: int) -> Project:
        if self._repo.get_by_key(payload.key):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project key already exists")
        project = self._repo.create(
            name=payload.name,
            key=payload.key,
            description=payload.description,
            created_by=created_by,
            status=payload.status,
        )
        self._db.commit()
        self._db.refresh(project)
        return project

    def update_project(self, project_id: int, payload: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        updates = payload.model_dump(exclude_none=True)
        project = self._repo.update(project, **updates)
        self._db.commit()
        self._db.refresh(project)
        return project

    def archive_project(self, project_id: int) -> Project:
        project = self.get_project(project_id)
        project = self._repo.archive(project)
        self._db.commit()
        self._db.refresh(project)
        return project
