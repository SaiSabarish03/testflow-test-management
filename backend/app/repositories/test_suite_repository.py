from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.test_suite import TestSuite


class TestSuiteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, suite_id: int) -> TestSuite | None:
        return self._db.get(TestSuite, suite_id)

    def list_by_project(
        self,
        project_id: int,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestSuite], int]:
        q = self._db.query(TestSuite).filter(TestSuite.project_id == project_id)
        if search:
            pattern = f"%{search}%"
            q = q.filter(TestSuite.name.ilike(pattern))
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(
        self,
        project_id: int,
        name: str,
        description: str | None,
        created_by: int,
    ) -> TestSuite:
        suite = TestSuite(
            project_id=project_id,
            name=name,
            description=description,
            created_by=created_by,
        )
        self._db.add(suite)
        self._db.flush()
        return suite

    def update(self, suite: TestSuite, **fields) -> TestSuite:
        for key, value in fields.items():
            setattr(suite, key, value)
        self._db.flush()
        return suite

    def delete(self, suite: TestSuite) -> None:
        self._db.delete(suite)
        self._db.flush()
