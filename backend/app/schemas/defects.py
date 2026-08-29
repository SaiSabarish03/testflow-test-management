import math
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import DefectSeverity, DefectPriority, DefectStatus


class DefectCreate(BaseModel):
    project_id: int
    test_case_id: int | None = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    severity: DefectSeverity
    priority: DefectPriority
    environment: str | None = Field(default=None, max_length=100)
    assigned_to: int | None = None


class DefectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    severity: DefectSeverity | None = None
    priority: DefectPriority | None = None
    environment: str | None = Field(default=None, max_length=100)
    assigned_to: int | None = None
    status: DefectStatus | None = None


class DefectResponse(BaseModel):
    id: int
    project_id: int
    test_case_id: int | None
    title: str
    description: str | None
    severity: DefectSeverity
    priority: DefectPriority
    environment: str | None
    status: DefectStatus
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DefectListResponse(BaseModel):
    items: list[DefectResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "DefectListResponse":
        return cls(
            items=[DefectResponse.model_validate(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
