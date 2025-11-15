"""User schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Create user schema"""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    tenant_id: Optional[UUID] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class UserUpdate(BaseModel):
    """Update user schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    tenant_id: Optional[UUID] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# Auth Schemas
class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Token data schema"""
    user_id: UUID
    username: str
    role: UserRole
    tenant_id: Optional[UUID] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class ChangePassword(BaseModel):
    """Change password schema"""
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


# API Key Schemas
class APIKeyCreate(BaseModel):
    """Create API key schema"""
    name: str = Field(..., min_length=3, max_length=100)
    expires_days: Optional[int] = Field(None, gt=0, le=365)


class APIKeyResponse(BaseModel):
    """API key response schema"""
    id: UUID
    name: str
    key: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# Tenant Schemas
class TenantBase(BaseModel):
    """Base tenant schema"""
    name: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    webhook_url: Optional[str] = None
    notification_email: Optional[EmailStr] = None


class TenantCreate(TenantBase):
    """Create tenant schema"""
    pass


class TenantUpdate(BaseModel):
    """Update tenant schema"""
    name: Optional[str] = None
    webhook_url: Optional[str] = None
    notification_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    """Tenant response schema"""
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
