import re

from pydantic import BaseModel, EmailStr, field_validator

PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")  # loose E.164-ish check


class SignupRequest(BaseModel):
    email: EmailStr
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_PATTERN.match(v):
            raise ValueError("Phone must be in international format, e.g. +919876543210")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    phone: str

    model_config = {"from_attributes": True}  # lets this build directly from a User ORM object


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
