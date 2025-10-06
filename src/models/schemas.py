"""Pydantic models for request and response validation."""

from datetime import datetime, date
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserTypeEnum(str, Enum):
    """Valid user types."""
    ADMIN = "ADMIN"
    HOSPITAL = "HOSPITAL"
    DOCTOR = "DOCTOR"


class GenderEnum(str, Enum):
    """Valid gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


# Request Models
class UserRegisterRequest(BaseModel):
    """User registration request model."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    user_type: UserTypeEnum


class UserLoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str


class UserLoginCloudflareRequest(BaseModel):
    """User login with Cloudflare Turnstile request model."""
    email: EmailStr
    password: str
    turnstileToken: str


class PasswordUpdateRequest(BaseModel):
    """Password update request model."""
    old_password: str
    new_password: str = Field(..., min_length=6)


class NewsletterSubscribeRequest(BaseModel):
    """Newsletter subscription request model."""
    email: EmailStr


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


# Response Models
class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: str
    user_type: UserTypeEnum
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    dob: Optional[date] = None
    profile_pic: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class UserCreateResponse(BaseModel):
    """User creation response model."""
    id: str


class HealthResponse(BaseModel):
    """Health check response model."""
    health: bool


class MessageResponse(BaseModel):
    """Generic message response model."""
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    status_code: int
    message: str


class SuccessResponse(BaseModel):
    """Success response model."""
    success: bool = True
    status_code: int
    data: Optional[Dict[str, Any]] = None
    message: str


# Profile Update Models
class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""
    name: Optional[str] = Field(None, max_length=100)
    gender: Optional[GenderEnum] = None
    dob: Optional[date] = None
    profile_pic: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

    @validator('dob')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v


# Doctor Models
class DoctorResponse(BaseModel):
    """Doctor response model."""
    id: str
    user_id: str
    hospital_id: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Hospital Models
class HospitalResponse(BaseModel):
    """Hospital response model."""
    id: str
    admin_id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Patient Models
class PatientResponse(BaseModel):
    """Patient response model."""
    id: str
    user_id: str
    medical_record_number: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    insurance_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime