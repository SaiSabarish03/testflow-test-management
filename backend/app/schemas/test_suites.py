import math
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TestSuiteCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v


class TestSuiteUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be blank")
        return v


class TestSuiteResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestSuiteListResponse(BaseModel):
    items: list[TestSuiteResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "TestSuiteListResponse":
        return cls(
            items=[TestSuiteResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
