from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Authentication Schemas
class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    password: str = Field(..., min_length=4, max_length=100, description="User password")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordReset(BaseModel):
    """Schema for password reset."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=4, max_length=100, description="New password")


class Message(BaseModel):
    """Schema for generic message response."""
    message: str = Field(..., description="Response message")


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str
    phone: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserProfile(UserBase):
    """Schema for user profile response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    language: str
    created_at: datetime
