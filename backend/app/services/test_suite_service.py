from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.test_suite import TestSuite
from app.models.enums import ProjectStatus
from app.repositories.test_suite_repository import TestSuiteRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.test_suites import TestSuiteCreate, TestSuiteUpdate


class TestSuiteService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = TestSuiteRepository(db)
        self._project_repo = ProjectRepository(db)

    def list_suites(
        self,
        project_id: int,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestSuite], int]:
        # Validate project exists
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return self._repo.list_by_project(project_id=project_id, search=search, page=page, page_size=page_size)

    def get_suite(self, suite_id: int) -> TestSuite:
        suite = self._repo.get_by_id(suite_id)
        if suite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
        return suite

    def create_suite(self, project_id: int, payload: TestSuiteCreate, created_by: int) -> TestSuite:
        # Validate project exists and is active
        project = self._project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.status == ProjectStatus.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a test suite in an archived project",
            )
        suite = self._repo.create(
            project_id=project_id,
            name=payload.name,
            description=payload.description,
            created_by=created_by,
        )
        self._db.commit()
        self._db.refresh(suite)
        return suite

    def update_suite(self, suite_id: int, payload: TestSuiteUpdate) -> TestSuite:
        suite = self.get_suite(suite_id)
        updates = payload.model_dump(exclude_none=True)
        suite = self._repo.update(suite, **updates)
        self._db.commit()
        self._db.refresh(suite)
        return suite

    def delete_suite(self, suite_id: int) -> None:
        suite = self.get_suite(suite_id)
        # Check if any nested test case has test results or defects
        for tc in suite.test_cases:
            if len(tc.test_results) > 0 or len(tc.defects) > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete test suite containing test cases with historical test results or defects",
                )
        self._repo.delete(suite)
        self._db.commit()
