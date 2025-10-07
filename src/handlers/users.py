"""Users handler for FastAPI Auth Service."""

import traceback
import logging
from typing import Any, Dict, Optional, Tuple, List
from uuid import UUID
from contextlib import nullcontext

from uuid_extensions import uuid7str
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..dependencies import get_sync_session, get_session
from ..core.jwt_config import get_password_hash, verify_password, create_access_token, create_refresh_token
from ..core import config
from ..models import UserTable, HospitalTable, DoctorTable
from ..handlers.validators.users import ProfileUpdateData
# from ..models import HospitalTable, DoctorTable  # Will be added as we migrate other models

logger = logging.getLogger(__name__)


class UsersError(Exception):
    """Base exception for Users class errors."""
    pass


class UserNotFoundError(UsersError):
    """Raised when a user is not found."""
    pass


class ValidationError(UsersError):
    """Raised when data validation fails."""
    pass


class Users:
    """User management service with optimized SQLAlchemy operations."""
    
    # Valid gender values
    VALID_GENDERS = ['MALE', 'FEMALE', 'OTHER']
    
    def __init__(self):
        """Initialize the Users service."""
        # Note: Admin user creation moved to startup event in main.py
        pass
    
    def _ensure_admin_user_exists(self) -> None:
        """Create admin user if it doesn't exist."""
        try:
            admin_user_id = config.ADMIN_USER_ID
            with get_sync_session() as session:
                existing_admin = session.query(UserTable).filter_by(id=UUID(admin_user_id)).first()
                
                if not existing_admin:
                    admin_password = get_password_hash(config.ADMIN_USER_PASSWORD)
                    
                    new_admin = UserTable(
                        id=UUID(admin_user_id),
                        email=config.ADMIN_USER_EMAIL,
                        username=config.ADMIN_USER_USERNAME,
                        password=admin_password,
                        user_type="ADMIN",
                    )
                    session.add(new_admin)
        except Exception as e:
            logger.error(f"Error initializing admin user: {traceback.format_exc()}")
            raise UsersError("Failed to initialize admin user") from e
    
    @classmethod
    def create_user(cls, email: str, username: str, password: str, user_type: str, 
                optional_fields: Dict[str, str] = None, session: Session = None) -> str:
        """Create a new user with the given details."""
        optional_fields = optional_fields or {}
        user_uuid = uuid7str()
        
        try:
            # Use provided session or create context
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                if s.query(UserTable).filter_by(email=email).first():
                    raise ValidationError("Email already exists")
                
                new_user = UserTable(
                    id=UUID(user_uuid),
                    email=email,
                    username=username,
                    password=get_password_hash(password),
                    user_type=user_type,
                    name=optional_fields.get('name'),
                    gender=optional_fields.get('gender', '').upper() if optional_fields.get('gender') else None,
                    dob=optional_fields.get("dob")
                )
                
                s.add(new_user)
                return user_uuid
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {traceback.format_exc()}")
            raise UsersError("Failed to create user") from e
    
    @classmethod
    def get_user_by_email(cls, email: str, session: Session = None) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(email=email).first()
                if user:
                    return user.to_dict(exclude_fields=['password'])
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by email: {traceback.format_exc()}")
            raise UsersError("Failed to get user by email") from e

    @classmethod
    def get_user_by_username(cls, username: str, session: Session = None) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()

            with use_session as s:
                user = s.query(UserTable).filter_by(username=username).first()
                if user:
                    return user.to_dict(exclude_fields=['password'])
                return None

        except Exception as e:
            logger.error(f"Error getting user by username: {traceback.format_exc()}")
            raise UsersError("Failed to get user by username") from e
    
    @classmethod
    def get_user_by_id(cls, user_id: str, session: Session = None) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(id=UUID(user_id)).first()
                if user:
                    return user.to_dict(exclude_fields=['password'])
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {traceback.format_exc()}")
            raise UsersError("Failed to get user by ID") from e
    
    @classmethod
    def login(cls, email: str, password: str, session: Session = None) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Authenticate user and return tokens."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(email=email).first()
                
                if user and verify_password(password, user.password):
                    # Create tokens
                    user_id = str(user.id)
                    access_token = create_access_token(data={"sub": user_id})
                    refresh_token = create_refresh_token(data={"sub": user_id})
                    
                    user_dict = user.to_dict(exclude_fields=['password'])
                    return access_token, refresh_token, user_dict
                
                return None, None, None
                
        except Exception as e:
            logger.error(f"Error during login: {traceback.format_exc()}")
            raise UsersError("Failed to login") from e
    
    @classmethod
    def update_password(cls, user_id: str, old_password: str, new_password: str, session: Session = None) -> bool:
        """Update user password."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(id=UUID(user_id)).first()
                
                if not user:
                    raise UserNotFoundError("User not found")
                
                if not verify_password(old_password, user.password):
                    raise ValidationError("Current password is incorrect")
                
                user.password = get_password_hash(new_password)
                user.updated_at = datetime.now(timezone.utc)
                
                return True
                
        except (UserNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating password: {traceback.format_exc()}")
            raise UsersError("Failed to update password") from e
    
    @classmethod
    def delete_user_by_id(cls, user_id: str, session: Session = None) -> bool:
        """Delete user by ID."""
        try:
            use_session = nullcontext(session) if session else get_sync_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(id=UUID(user_id)).first()
                
                if not user:
                    raise UserNotFoundError("User not found")
                
                s.delete(user)
                return True
                
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting user: {traceback.format_exc()}")
            raise UsersError("Failed to delete user") from e

    @classmethod
    def get_profile_by_id(cls, user_id: UUID) -> Dict:
        """Retrieve user profile with related data based on user type."""
        try:
            with get_session() as session:
                # Use eager loading to prevent N+1 queries
                user = session.query(UserTable).filter_by(id=user_id).first()
                
                if not user:
                    raise UserNotFoundError("User not found")
                
                profile = user.to_dict(exclude_fields=['password'])
                
                if profile.get('user_type') == 'HOSPITAL':
                    hospital = session.query(HospitalTable).filter_by(admin=user_id).first()
                    if hospital:
                        profile['hospital'] = hospital.to_dict()
                        
                elif profile.get('user_type') == 'DOCTOR':
                    doctor = session.query(DoctorTable).filter_by(user_id=user_id).first()
                    if doctor:
                        profile['doctor'] = doctor.to_dict()
                        
                        # Use eager loading for hospital
                        hospital = session.query(HospitalTable).filter_by(id=doctor.hospital_id).first()
                        if hospital:
                            profile['hospital'] = hospital.to_dict()
                
                return profile

        except SQLAlchemyError as e:
            logger.error(f"Error fetching user profile: {traceback.format_exc()}")
            raise UsersError("Failed to fetch user profile") from e


    @classmethod
    def update_profile_by_id(cls, user_id: UUID, updated_data: Dict) -> Dict:
        """Update user profile in the database."""
        # Validate profile data
        errors, validated_data = cls.validate_profile_data(updated_data)
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        try:
            with get_session() as session:
                user = session.query(UserTable).filter_by(id=user_id).first()
                if not user:
                    raise UserNotFoundError("User not found")
                
                # Update fields
                for field, value in validated_data.items():
                    setattr(user, field, value)
                
                user.updated_at = datetime.now(timezone.utc)
                
                # Convert to dict before session closes
                return user.to_dict(exclude_fields=['password'])

        except SQLAlchemyError as e:
            logger.error(f"Error updating profile: {traceback.format_exc()}")
            raise UsersError("Failed to update profile") from e
    
    @classmethod
    def update_profilepic_by_id(cls, user_id: UUID, key: str) -> Dict:
        """Update user profile picture in the database."""
        try:
            with get_session() as session:
                user = session.query(UserTable).filter_by(id=user_id).first()
                if not user:
                    raise UserNotFoundError("User not found")
                
                user.profile_pic = key
                user.updated_at = datetime.now(timezone.utc)
                
                return user.to_dict(exclude_fields=['password'])

        except SQLAlchemyError as e:
            logger.error(f"Error updating profile picture: {traceback.format_exc()}")
            raise UsersError("Failed to update profile picture") from e
    
    @classmethod
    def validate_profile_data(cls, data: dict) -> Tuple[Optional[List[str]], Optional[Dict]]:
        """Validate the profile data using Pydantic V2."""
        try:
            # Create a Pydantic model instance
            profile_data = ProfileUpdateData.model_validate(data)
            
            # Get validated data as a dictionary
            validated_data = profile_data.model_dump(exclude_unset=True)
            
            return None, validated_data
        except ValidationError as e:
            # Extract error messages
            errors = []
            for error in e.errors():
                field = error['loc'][0]
                msg = error['msg']
                errors.append(f"{field}: {msg}")
            
            return errors, None

    @classmethod
    def bulk_create_users(cls, users_data: List[Dict]) -> List[str]:
        """Create multiple users in a single transaction."""
        created_ids = []
        try:
            with get_session() as session:
                for user_data in users_data:
                    user_uuid = uuid7str()
                    user = UserTable(
                        id=UUID(user_uuid),
                        email=user_data['email'],
                        username=user_data['username'],
                        password=cls.hash_password(user_data['password']),
                        user_type=user_data['user_type'],
                        name=user_data.get('name'),
                        gender=user_data.get('gender', '').upper() if user_data.get('gender') else None,
                        dob=user_data.get("dob")
                    )
                    session.add(user)
                    created_ids.append(user_uuid)
                
            return created_ids
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk create: {traceback.format_exc()}")
            raise UsersError("Failed to create users") from e

    @classmethod
    def search_users(cls, query: str, user_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search users by name, email, or username."""
        try:
            with get_session() as session:
                db_query = session.query(UserTable)
                
                # Apply search filter
                search_filter = (
                    UserTable.name.ilike(f"%{query}%") |
                    UserTable.email.ilike(f"%{query}%") |
                    UserTable.username.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
                
                # Apply user type filter if provided
                if user_type:
                    db_query = db_query.filter(UserTable.user_type == user_type)
                
                # Apply limit
                users = db_query.limit(limit).all()
                
                return [user.to_dict(exclude_fields=['password']) for user in users]
                
        except SQLAlchemyError as e:
            logger.error(f"Error searching users: {traceback.format_exc()}")
            raise UsersError("Failed to search users") from e
# Create a singleton instance (similar to the Flask version)
# For backward compatibility, export the Users class
# Don't auto-instantiate during import to avoid database connection issues
__all__ = ["Users"]
