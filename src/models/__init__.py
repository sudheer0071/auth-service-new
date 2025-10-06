"""SQLAlchemy models for FastAPI Auth Service."""

from .users import UserTable, valid_user_type, valid_user_gender
from .schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserLoginCloudflareRequest,
    PasswordUpdateRequest,
    NewsletterSubscribeRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    UserCreateResponse,
    HealthResponse,
    MessageResponse,
    ErrorResponse,
    SuccessResponse,
    ProfileUpdateRequest,
    DoctorResponse,
    HospitalResponse,
    PatientResponse,
    UserTypeEnum,
    GenderEnum
)

# Import other models as we migrate them
from .doctor import DoctorTable
from .hospital import HospitalTable, CounterTable
from .patient import PatientTable
from .settings import SettingsTable
from .newsletter import NewsletterSubscriber

__all__ = [
    # SQLAlchemy models
    "UserTable",
    "DoctorTable",
    "HospitalTable",
    "CounterTable", 
    "PatientTable",
    "SettingsTable",
    "NewsletterSubscriber",
    "valid_user_type",
    "valid_user_gender",
    
    # Pydantic schemas
    "UserRegisterRequest",
    "UserLoginRequest", 
    "UserLoginCloudflareRequest",
    "PasswordUpdateRequest",
    "NewsletterSubscribeRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreateResponse",
    "HealthResponse",
    "MessageResponse",
    "ErrorResponse",
    "SuccessResponse",
    "ProfileUpdateRequest",
    "DoctorResponse",
    "HospitalResponse",
    "PatientResponse",
    "UserTypeEnum",
    "GenderEnum"
]