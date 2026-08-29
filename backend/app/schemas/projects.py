import math
import re
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.models.enums import ProjectStatus

# Project key: 2–20 uppercase letters and digits only
_KEY_RE = re.compile(r"^[A-Z0-9]{2,20}$")


class ProjectCreate(BaseModel):
    name: str
    key: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v

    @field_validator("key")
    @classmethod
    def key_format(cls, v: str) -> str:
        if not _KEY_RE.match(v):
            raise ValueError("key must be 2–20 uppercase letters/digits (e.g. TFW, CRM01)")
        return v


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be blank")
        return v

    # Project key is intentionally excluded — immutable after creation.


class ProjectResponse(BaseModel):
    id: int
    name: str
    key: str
    description: str | None
    status: ProjectStatus
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "ProjectListResponse":
        return cls(
            items=[ProjectResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
