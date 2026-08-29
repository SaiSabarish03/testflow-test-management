from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole, UserStatus


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("invalid email format")
        return v


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    status: UserStatus

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
