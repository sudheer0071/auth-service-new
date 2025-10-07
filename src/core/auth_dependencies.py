"""FastAPI dependency injection for authentication and authorization."""

import logging
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from ..core.jwt_config import verify_token, is_token_blacklisted, security
from ..core.app_config import get_redis_blocklist
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes, http_messages

logger = logging.getLogger(__name__)


class CurrentUser:
    """Current user information from JWT token."""
    
    def __init__(self, user_data: Dict[str, Any]):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.username = user_data.get('username')
        self.user_type = user_data.get('user_type')
        self.hospital = user_data.get('hospital')
        self.doctor = user_data.get('doctor')


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    redis_client = Depends(get_redis_blocklist)
) -> CurrentUser:
    """
    Get current user from JWT token.
    This replaces Flask's @token_required decorator.
    """
    try:
        # Verify the token
        payload = verify_token(credentials.credentials, "access")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti, redis_client):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user identity
        identity = payload.get("sub")
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print("identity ", identity)
        # In the new implementation, identity is the user ID string
        user_id = identity if isinstance(identity, str) else identity.get('id')
        # print("user_id ", user_id)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload - missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Import Users handler
        from ..handlers.users import Users
        user_info = Users.get_user_by_id(user_id)
        # print("user_info ", user_info)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Build user info dictionary
        user_data = {
            'id': user_info['id'],
            'email': user_info['email'],
            'username': user_info['username'],
            'user_type': user_info['user_type']
        }
        
        # Add hospital info if user is HOSPITAL type
        if user_info['user_type'] == 'HOSPITAL':
            from ..handlers.hospital import Hospital
            hospital_info = Hospital.get_hospital_by_admin(admin_id=user_info['id'])
            user_data['hospital'] = hospital_info
        
        # Add doctor and hospital info if user is DOCTOR type
        if user_info['user_type'] == 'DOCTOR':
            from ..handlers.doctor import Doctor
            from ..handlers.hospital import Hospital
            
            doctor_info = Doctor.get_doctor_by_userId(user_id=user_info['id'])
            user_data['doctor'] = doctor_info
            # print("user data updated", user_data)
            if doctor_info and doctor_info.get('hospital_id'):
                hospital_id = doctor_info['hospital_id']
                hospital_info = Hospital.get_hospital_by_id(hospital_id=hospital_id)
                # print("hospital_info //////////", hospital_info)
                user_data['hospital'] = hospital_info
                # print("user data updated", user_data)
            else:
                logger.warning(f"Doctor profile incomplete for user_id: {user_info['id']}")
                user_data['hospital'] = None
        
        return CurrentUser(user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_refresh_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    redis_client = Depends(get_redis_blocklist)
) -> CurrentUser:
    """
    Get current user from refresh token.
    """
    try:
        # Verify the refresh token
        payload = verify_token(credentials.credentials, "refresh")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti, redis_client):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user identity
        identity = payload.get("sub")
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = identity if isinstance(identity, str) else identity.get('id')
        from ..handlers.users import Users
        user_info = Users.get_user_by_id(user_id)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = {
            'id': user_info['id'],
            'email': user_info['email'],
            'username': user_info['username'],
            'user_type': user_info['user_type']
        }
        
        return CurrentUser(user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_refresh_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Role-based access control dependencies
async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require ADMIN role."""
    if current_user.user_type != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins allowed"
        )
    return current_user


async def require_hospital(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require HOSPITAL role."""
    if current_user.user_type != 'HOSPITAL' or current_user.hospital is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered hospital's admin allowed"
        )
    return current_user


async def require_admin_or_hospital(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require ADMIN or HOSPITAL role."""
    if current_user.user_type not in ['ADMIN', 'HOSPITAL']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and hospital's admin allowed"
        )
    if current_user.user_type == 'HOSPITAL' and current_user.hospital is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered hospital's admin allowed"
        )
    return current_user


async def require_admin_hospital_doctor(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require ADMIN, HOSPITAL, or DOCTOR role."""
    if current_user.user_type not in ['ADMIN', 'HOSPITAL', 'DOCTOR']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, doctor and hospital's admin allowed"
        )
    if current_user.user_type == 'HOSPITAL' and current_user.hospital is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered hospital's admin allowed"
        )
    return current_user


async def require_doctor(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require DOCTOR role."""
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Doctor allowed"
        )
    return current_user