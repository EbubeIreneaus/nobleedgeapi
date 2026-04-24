from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
import uuid
from app.utils.enums import UserRole, KYCStatus

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str | None = None
    country: str | None = None
    profile_picture: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    referral_code: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    profile_picture: str | None = None

class UserRead(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    is_banned: bool
    kyc_status: KYCStatus
    referral_code: str
    referred_by_id: uuid.UUID | None
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfile(UserRead):
    # This will be populated in routers when returning full profile
    wallet: "Any" = None

from typing import Any
