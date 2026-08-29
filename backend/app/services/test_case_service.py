from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.enums import ProjectStatus, TestCaseStatus, TestCasePriority
from app.repositories.test_case_repository import TestCaseRepository
from app.repositories.test_suite_repository import TestSuiteRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.test_cases import TestCaseCreate, TestCaseUpdate


class TestCaseService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = TestCaseRepository(db)
        self._suite_repo = TestSuiteRepository(db)
        self._project_repo = ProjectRepository(db)

    def list_test_cases(
        self,
        suite_id: int,
        search: str | None = None,
        priority: TestCasePriority | None = None,
        status: TestCaseStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCase], int]:
        # Validate suite exists
        suite = self._suite_repo.get_by_id(suite_id)
        if not suite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
        return self._repo.list_by_suite(
            suite_id=suite_id,
            search=search,
            priority=priority,
            status=status,
            page=page,
            page_size=page_size,
        )

    def get_test_case(self, test_case_id: int) -> TestCase:
        test_case = self._repo.get_by_id(test_case_id)
        if test_case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        return test_case

    def create_test_case(self, suite_id: int, payload: TestCaseCreate, created_by: int) -> TestCase:
        # Validate suite exists
        suite = self._suite_repo.get_by_id(suite_id)
        if not suite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

        # Validate project is active
        project = self._project_repo.get_by_id(suite.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.status == ProjectStatus.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a test case in an archived project",
            )

        # Enforce READY status requirements
        if payload.status == TestCaseStatus.READY:
            if not payload.title or not payload.title.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Title is required for READY status",
                )
            if not payload.expected_result or not payload.expected_result.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expected result is required for READY status",
                )
            if not payload.steps or len(payload.steps) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Steps are required for READY status",
                )

        steps_data = [s.model_dump() for s in payload.steps] if payload.steps is not None else None

        test_case = self._repo.create(
            suite_id=suite_id,
            title=payload.title,
            description=payload.description,
            preconditions=payload.preconditions,
            steps=steps_data,
            expected_result=payload.expected_result,
            priority=payload.priority,
            status=payload.status,
            created_by=created_by,
        )
        self._db.commit()
        self._db.refresh(test_case)
        return test_case

    def update_test_case(self, test_case_id: int, payload: TestCaseUpdate) -> TestCase:
        test_case = self.get_test_case(test_case_id)
        updates = payload.model_dump(exclude_none=True)

        # Merge fields to check final state rules
        final_title = updates.get("title", test_case.title)
        final_expected_result = updates.get("expected_result", test_case.expected_result)
        final_status = updates.get("status", test_case.status)

        # Check if steps are provided or if we use existing ones
        if "steps" in updates and updates["steps"] is not None:
            final_steps = updates["steps"]
        else:
            final_steps = test_case.steps

        if final_status == TestCaseStatus.READY:
            if not final_title or not final_title.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Title is required for READY status",
                )
            if not final_expected_result or not final_expected_result.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expected result is required for READY status",
                )
            if not final_steps or len(final_steps) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Steps are required for READY status",
                )



        test_case = self._repo.update(test_case, **updates)
        self._db.commit()
        self._db.refresh(test_case)
        return test_case

    def delete_test_case(self, test_case_id: int) -> TestCase:
        test_case = self.get_test_case(test_case_id)
        test_case = self._repo.deprecate(test_case)
        self._db.commit()
        self._db.refresh(test_case)
        return test_case
