import math
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.enums import TestRunStatus, TestResultStatus


# ---------------------------------------------------------------------------
# Test Run schemas
# ---------------------------------------------------------------------------

class TestRunCreate(BaseModel):
    name: str = Field(..., max_length=255)
    environment: str = Field(..., max_length=100)
    test_case_ids: list[int] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v

    @field_validator("environment")
    @classmethod
    def env_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("environment must not be blank")
        return v

    @field_validator("test_case_ids")
    @classmethod
    def ids_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("test_case_ids must be unique")
        return v


class TestRunResponse(BaseModel):
    id: int
    project_id: int
    name: str
    environment: str
    status: TestRunStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TestRunListResponse(BaseModel):
    items: list[TestRunResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "TestRunListResponse":
        return cls(
            items=[TestRunResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )


class TestRunSummaryResponse(BaseModel):
    total: int
    not_run: int
    passed: int
    failed: int
    blocked: int
    pass_rate: float


# ---------------------------------------------------------------------------
# Test Result schemas
# ---------------------------------------------------------------------------

class TestCaseMinimal(BaseModel):
    id: int
    title: str
    suite_id: int

    model_config = {"from_attributes": True}


class TestResultUpdate(BaseModel):
    status: TestResultStatus
    actual_result: str | None = None

    @field_validator("status")
    @classmethod
    def must_be_terminal(cls, v: TestResultStatus) -> TestResultStatus:
        if v == TestResultStatus.NOT_RUN:
            raise ValueError("Cannot set result status back to NOT_RUN")
        return v


class TestResultResponse(BaseModel):
    id: int
    test_run_id: int
    test_case_id: int
    status: TestResultStatus
    actual_result: str | None
    executed_by: int | None
    executed_at: datetime | None
    test_case: TestCaseMinimal | None = None

    model_config = {"from_attributes": True}


class TestResultListResponse(BaseModel):
    items: list[TestResultResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "TestResultListResponse":
        return cls(
            items=[TestResultResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
