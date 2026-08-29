import math
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.enums import TestCasePriority, TestCaseStatus


class TestStep(BaseModel):
    order: int = Field(..., gt=0)
    action: str

    @field_validator("action")
    @classmethod
    def action_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("action must not be blank")
        return v


class TestCaseCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    preconditions: str | None = None
    steps: list[TestStep] | None = None
    expected_result: str
    priority: TestCasePriority
    status: TestCaseStatus = TestCaseStatus.DRAFT

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v

    @field_validator("expected_result")
    @classmethod
    def expected_result_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("expected_result must not be blank")
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps_list(cls, v: list[TestStep] | None) -> list[TestStep] | None:
        if v is None:
            return v
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("step orders must be unique")
        return sorted(v, key=lambda s: s.order)


class TestCaseUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    preconditions: str | None = None
    steps: list[TestStep] | None = None
    expected_result: str | None = None
    priority: TestCasePriority | None = None
    status: TestCaseStatus | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v

    @field_validator("expected_result")
    @classmethod
    def expected_result_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("expected_result must not be blank")
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps_list(cls, v: list[TestStep] | None) -> list[TestStep] | None:
        if v is None:
            return v
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("step orders must be unique")
        return sorted(v, key=lambda s: s.order)


class TestCaseResponse(BaseModel):
    id: int
    suite_id: int
    title: str
    description: str | None
    preconditions: str | None
    steps: list[TestStep] | None
    expected_result: str
    priority: TestCasePriority
    status: TestCaseStatus
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestCaseListResponse(BaseModel):
    items: list[TestCaseResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "TestCaseListResponse":
        return cls(
            items=[TestCaseResponse.model_validate(tc) for tc in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
