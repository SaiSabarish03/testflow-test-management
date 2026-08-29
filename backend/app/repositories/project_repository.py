from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.project import Project
from app.models.enums import ProjectStatus


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, project_id: int) -> Project | None:
        return self._db.get(Project, project_id)

    def get_by_key(self, key: str) -> Project | None:
        return self._db.query(Project).filter(Project.key == key).first()

    def list(
        self,
        search: str | None = None,
        status: ProjectStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]:
        q = self._db.query(Project)
        if search:
            pattern = f"%{search}%"
            q = q.filter(or_(Project.name.ilike(pattern), Project.key.ilike(pattern)))
        if status:
            q = q.filter(Project.status == status)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(self, name: str, key: str, description: str | None, created_by: int, status: ProjectStatus = ProjectStatus.ACTIVE) -> Project:
        project = Project(name=name, key=key, description=description, created_by=created_by, status=status)
        self._db.add(project)
        self._db.flush()
        return project

    def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            setattr(project, key, value)
        self._db.flush()
        return project

    def archive(self, project: Project) -> Project:
        project.status = ProjectStatus.ARCHIVED
        self._db.flush()
        return project
