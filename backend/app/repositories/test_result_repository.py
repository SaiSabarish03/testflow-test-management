from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.test_result import TestResult
from app.models.enums import TestResultStatus


class TestResultRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, result_id: int) -> TestResult | None:
        return self._db.get(TestResult, result_id)

    def list_by_run(
        self,
        run_id: int,
        status: TestResultStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestResult], int]:
        q = (
            self._db.query(TestResult)
            .options(joinedload(TestResult.test_case))
            .filter(TestResult.test_run_id == run_id)
        )
        if status:
            q = q.filter(TestResult.status == status)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_by_run_and_case(self, run_id: int, test_case_id: int) -> TestResult | None:
        return (
            self._db.query(TestResult)
            .filter(
                TestResult.test_run_id == run_id,
                TestResult.test_case_id == test_case_id,
            )
            .first()
        )

    def create(self, run_id: int, test_case_id: int) -> TestResult:
        result = TestResult(
            test_run_id=run_id,
            test_case_id=test_case_id,
            status=TestResultStatus.NOT_RUN,
        )
        self._db.add(result)
        self._db.flush()
        return result

    def record_result(
        self,
        result: TestResult,
        status: TestResultStatus,
        actual_result: str | None,
        executed_by: int,
    ) -> TestResult:
        result.status = status
        result.actual_result = actual_result
        result.executed_by = executed_by
        result.executed_at = datetime.now(timezone.utc)
        self._db.flush()
        return result

    def count_by_status(self, run_id: int) -> dict[TestResultStatus, int]:
        rows = (
            self._db.query(TestResult.status, func.count(TestResult.id))
            .filter(TestResult.test_run_id == run_id)
            .group_by(TestResult.status)
            .all()
        )
        return {s: c for s, c in rows}
