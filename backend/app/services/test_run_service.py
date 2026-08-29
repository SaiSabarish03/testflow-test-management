from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.enums import ProjectStatus, TestCaseStatus, TestRunStatus, TestResultStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.repositories.test_run_repository import TestRunRepository
from app.repositories.test_result_repository import TestResultRepository
from app.schemas.test_runs import TestRunCreate, TestResultUpdate, TestRunSummaryResponse


# Terminal result statuses — a run can only complete when all results are terminal
_TERMINAL = {TestResultStatus.PASSED, TestResultStatus.FAILED, TestResultStatus.BLOCKED}

# Valid state transitions for a TestRun
_ALLOWED_TRANSITIONS: dict[TestRunStatus, set[TestRunStatus]] = {
    TestRunStatus.NOT_STARTED: {TestRunStatus.IN_PROGRESS},
    TestRunStatus.IN_PROGRESS: {TestRunStatus.COMPLETED, TestRunStatus.ABORTED},
    TestRunStatus.COMPLETED: set(),
    TestRunStatus.ABORTED: set(),
}


class TestRunService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._project_repo = ProjectRepository(db)
        self._case_repo = TestCaseRepository(db)
        self._run_repo = TestRunRepository(db)
        self._result_repo = TestResultRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_run_or_404(self, run_id: int) -> TestRun:
        run = self._run_repo.get_by_id(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found")
        return run

    def _get_result_or_404(self, result_id: int) -> TestResult:
        result = self._result_repo.get_by_id(result_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")
        return result

    def _assert_transition(self, run: TestRun, target: TestRunStatus) -> None:
        if target not in _ALLOWED_TRANSITIONS[run.status]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition run from {run.status} to {target}",
            )

    # ------------------------------------------------------------------
    # Run CRUD
    # ------------------------------------------------------------------

    def list_runs(
        self,
        project_id: int,
        search: str | None = None,
        status: TestRunStatus | None = None,
        environment: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestRun], int]:
        project = self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return self._run_repo.list_by_project(
            project_id=project_id,
            search=search,
            status=status,
            environment=environment,
            page=page,
            page_size=page_size,
        )

    def get_run(self, run_id: int) -> TestRun:
        return self._get_run_or_404(run_id)

    def create_run(self, project_id: int, payload: TestRunCreate, created_by: int) -> TestRun:
        # Validate project
        project = self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.status == ProjectStatus.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a test run for an archived project",
            )

        # Validate all test cases (fail-fast with full error detail)
        invalid: list[str] = []
        for tc_id in payload.test_case_ids:
            tc = self._case_repo.get_by_id(tc_id)
            if tc is None:
                invalid.append(f"Test case {tc_id} not found")
                continue
            # Ownership: TestCase → TestSuite → Project
            if tc.suite.project_id != project_id:
                invalid.append(f"Test case {tc_id} does not belong to project {project_id}")
                continue
            if tc.status == TestCaseStatus.DEPRECATED:
                invalid.append(f"Test case {tc_id} is DEPRECATED")
                continue
            if tc.status != TestCaseStatus.READY:
                invalid.append(f"Test case {tc_id} is not READY (status={tc.status})")

        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid test cases", "errors": invalid},
            )

        # Atomic: create run + results in one transaction block
        run = self._run_repo.create(
            project_id=project_id,
            name=payload.name,
            environment=payload.environment,
            created_by=created_by,
        )
        for tc_id in payload.test_case_ids:
            self._result_repo.create(run_id=run.id, test_case_id=tc_id)

        self._db.commit()
        self._db.refresh(run)
        return run

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_run(self, run_id: int) -> TestRun:
        run = self._get_run_or_404(run_id)
        self._assert_transition(run, TestRunStatus.IN_PROGRESS)
        run = self._run_repo.start(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    def complete_run(self, run_id: int) -> TestRun:
        run = self._get_run_or_404(run_id)
        self._assert_transition(run, TestRunStatus.COMPLETED)

        # All results must be terminal
        counts = self._result_repo.count_by_status(run_id)
        not_run_count = counts.get(TestResultStatus.NOT_RUN, 0)
        if not_run_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot complete run: {not_run_count} result(s) still have status NOT_RUN",
            )

        run = self._run_repo.complete(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    def abort_run(self, run_id: int) -> TestRun:
        run = self._get_run_or_404(run_id)
        self._assert_transition(run, TestRunStatus.ABORTED)
        run = self._run_repo.abort(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def list_results(
        self,
        run_id: int,
        status: TestResultStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestResult], int]:
        self._get_run_or_404(run_id)
        return self._result_repo.list_by_run(run_id=run_id, status=status, page=page, page_size=page_size)

    def record_result(
        self,
        run_id: int,
        result_id: int,
        payload: TestResultUpdate,
        executed_by: int,
    ) -> TestResult:
        run = self._get_run_or_404(run_id)
        result = self._get_result_or_404(result_id)

        if result.test_run_id != run_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")

        if run.status != TestRunStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot modify results for a run with status {run.status}",
            )

        result = self._result_repo.record_result(
            result=result,
            status=payload.status,
            actual_result=payload.actual_result,
            executed_by=executed_by,
        )
        self._db.commit()
        self._db.refresh(result)
        return result

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self, run_id: int) -> TestRunSummaryResponse:
        self._get_run_or_404(run_id)
        counts = self._result_repo.count_by_status(run_id)
        not_run = counts.get(TestResultStatus.NOT_RUN, 0)
        passed = counts.get(TestResultStatus.PASSED, 0)
        failed = counts.get(TestResultStatus.FAILED, 0)
        blocked = counts.get(TestResultStatus.BLOCKED, 0)
        total = not_run + passed + failed + blocked
        pass_rate = round((passed / total) * 100, 1) if total > 0 else 0.0
        return TestRunSummaryResponse(
            total=total,
            not_run=not_run,
            passed=passed,
            failed=failed,
            blocked=blocked,
            pass_rate=pass_rate,
        )
