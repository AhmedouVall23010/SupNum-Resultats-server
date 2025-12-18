from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email must end with @supnum.mr")
    password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        if not v.endswith('@supnum.mr'):
            raise ValueError('Email must end with @supnum.mr')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    # Note: refresh_token is sent in HttpOnly Secure cookie, not in response body


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailVerificationRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

