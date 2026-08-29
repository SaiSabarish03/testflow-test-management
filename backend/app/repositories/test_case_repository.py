from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.test_case import TestCase
from app.models.enums import TestCasePriority, TestCaseStatus


class TestCaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, test_case_id: int) -> TestCase | None:
        return self._db.get(TestCase, test_case_id)

    def list_by_suite(
        self,
        suite_id: int,
        search: str | None = None,
        priority: TestCasePriority | None = None,
        status: TestCaseStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCase], int]:
        q = self._db.query(TestCase).filter(TestCase.suite_id == suite_id)
        if search:
            pattern = f"%{search}%"
            q = q.filter(TestCase.title.ilike(pattern))
        if priority:
            q = q.filter(TestCase.priority == priority)
        if status:
            q = q.filter(TestCase.status == status)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(
        self,
        suite_id: int,
        title: str,
        description: str | None,
        preconditions: str | None,
        steps: list | None,
        expected_result: str,
        priority: TestCasePriority,
        status: TestCaseStatus,
        created_by: int,
    ) -> TestCase:
        test_case = TestCase(
            suite_id=suite_id,
            title=title,
            description=description,
            preconditions=preconditions,
            steps=steps,
            expected_result=expected_result,
            priority=priority,
            status=status,
            created_by=created_by,
        )
        self._db.add(test_case)
        self._db.flush()
        return test_case

    def update(self, test_case: TestCase, **fields) -> TestCase:
        for key, value in fields.items():
            setattr(test_case, key, value)
        self._db.flush()
        return test_case

    def deprecate(self, test_case: TestCase) -> TestCase:
        test_case.status = TestCaseStatus.DEPRECATED
        self._db.flush()
        return test_case
