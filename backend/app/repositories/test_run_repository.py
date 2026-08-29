from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.test_run import TestRun
from app.models.enums import TestRunStatus


class TestRunRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, run_id: int) -> TestRun | None:
        return self._db.get(TestRun, run_id)

    def list_by_project(
        self,
        project_id: int,
        search: str | None = None,
        status: TestRunStatus | None = None,
        environment: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestRun], int]:
        q = self._db.query(TestRun).filter(TestRun.project_id == project_id)
        if search:
            q = q.filter(TestRun.name.ilike(f"%{search}%"))
        if status:
            q = q.filter(TestRun.status == status)
        if environment:
            q = q.filter(TestRun.environment.ilike(f"%{environment}%"))
        total = q.count()
        items = q.order_by(TestRun.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(self, project_id: int, name: str, environment: str, created_by: int) -> TestRun:
        run = TestRun(
            project_id=project_id,
            name=name,
            environment=environment,
            created_by=created_by,
            status=TestRunStatus.NOT_STARTED,
        )
        self._db.add(run)
        self._db.flush()
        return run

    def update(self, run: TestRun, **fields) -> TestRun:
        for key, value in fields.items():
            setattr(run, key, value)
        self._db.flush()
        return run

    def start(self, run: TestRun) -> TestRun:
        run.status = TestRunStatus.IN_PROGRESS
        run.started_at = datetime.now(timezone.utc)
        self._db.flush()
        return run

    def complete(self, run: TestRun) -> TestRun:
        run.status = TestRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        self._db.flush()
        return run

    def abort(self, run: TestRun) -> TestRun:
        run.status = TestRunStatus.ABORTED
        self._db.flush()
        return run
