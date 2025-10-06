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

from ..dependencies import get_session
from ..core.jwt_config import get_password_hash, verify_password, create_access_token, create_refresh_token
from ..core import config
from ..models import UserTable
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
            with get_session() as session:
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
            use_session = nullcontext(session) if session else get_session()
            
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
            use_session = nullcontext(session) if session else get_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(email=email).first()
                if user:
                    return user.to_dict(exclude_fields=['password'])
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by email: {traceback.format_exc()}")
            raise UsersError("Failed to get user by email") from e
    
    @classmethod
    def get_user_by_id(cls, user_id: str, session: Session = None) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            use_session = nullcontext(session) if session else get_session()
            
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
            use_session = nullcontext(session) if session else get_session()
            
            with use_session as s:
                user = s.query(UserTable).filter_by(email=email).first()
                
                if user and verify_password(password, user.password):
                    # Create tokens
                    user_data = {"id": str(user.id)}
                    access_token = create_access_token(data={"sub": user_data})
                    refresh_token = create_refresh_token(data={"sub": user_data})
                    
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
            use_session = nullcontext(session) if session else get_session()
            
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
            use_session = nullcontext(session) if session else get_session()
            
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


# Create a singleton instance (similar to the Flask version)
# For backward compatibility, export the Users class
# Don't auto-instantiate during import to avoid database connection issues
__all__ = ["Users"]