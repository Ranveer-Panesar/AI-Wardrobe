import re

from pydantic import BaseModel, EmailStr, field_validator

# E.164-ish: optional leading +, non-zero first digit, 8–15 digits total
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")

# Password must have: ≥8 chars, 1 uppercase, 1 digit, 1 special character
_UPPER = re.compile(r"[A-Z]")
_DIGIT = re.compile(r"\d")
_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")


class SignupRequest(BaseModel):
    email: EmailStr
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                "Phone must be in international format with 8–15 digits, e.g. +919876543210"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not _UPPER.search(v):
            errors.append("at least one uppercase letter")
        if not _DIGIT.search(v):
            errors.append("at least one digit")
        if not _SPECIAL.search(v):
            errors.append("at least one special character (!@#$%^&* etc.)")
        if errors:
            raise ValueError("Password must contain " + ", ".join(errors))
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
