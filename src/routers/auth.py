"""FastAPI Auth Router - converted from Flask Blueprint."""

import re
import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
import requests

from ..core.auth_dependencies import get_current_user, get_refresh_user, CurrentUser
from ..core.app_config import get_redis_blocklist, ACCESS_EXPIRES
from ..core.jwt_config import create_access_token, create_refresh_token, blacklist_token
from ..core import config
from ..dependencies import get_db
from ..models import (
    UserRegisterRequest,
    UserLoginRequest,
    UserLoginCloudflareRequest,
    PasswordUpdateRequest,
    NewsletterSubscribeRequest,
    TokenResponse,
    UserResponse,
    UserCreateResponse,
    MessageResponse,
    UserTypeEnum
)
from ..utils.wrappers.api_response import ApiResponse, Cookie
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes, http_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Email regex for newsletter validation
EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


@router.post("/register", response_model=UserCreateResponse)
async def register(
    user_data: UserRegisterRequest,
    db = Depends(get_db)
):
    """Register a new user."""
    try:
        # Import here to avoid circular imports
        from ..handlers.users import Users
        from ..handlers.settings import Settings
        
        # Check if user already exists
        existing_user = Users.get_user_by_email(user_data.email)
        if existing_user:
            return ApiError(
                status_codes.HTTP_CONFLICT,
                http_messages.HTTP_REGISTER_USER_EXISTS_MESSAGE
            ).to_response()
        
        # Create user
        user_uuid = Users.create_user(
            user_data.email, 
            user_data.username, 
            user_data.password, 
            user_data.user_type.value
        )
        
        # Create settings for the user
        Settings.create_settings(user_uuid)
        
        return ApiResponse(
            status_codes.HTTP_CREATED,
            {'id': user_uuid},
            http_messages.HTTP_REGISTER_CREATED_MESSAGE
        ).to_response()
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR,
            f"Registration failed: {str(e)}"
        ).to_response()


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLoginRequest,
    db = Depends(get_db)
):
    """User login."""
    try:
        from ..handlers.users import Users
        
        # Attempt login
        access_token, refresh_token, user = Users.login(user_data.email, user_data.password)
        
        if access_token and refresh_token:
            # Create Cookie objects for secure token storage
            access_cookie = Cookie(
                key="jwt-token",
                value=access_token,
                max_age=int(timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()),
                path="/",
                httponly=True
            )
            
            refresh_cookie = Cookie(
                key="refresh-token", 
                value=refresh_token,
                max_age=int(timedelta(minutes=config.JWT_REFRESH_TOKEN_EXPIRE_MINUTES).total_seconds()),
                path="/",
                httponly=True
            )
            
            return ApiResponse(
                status_codes.HTTP_OK,
                {'access_token': access_token, 'refresh_token': refresh_token},
                http_messages.HTTP_LOGIN_SUCCESS_MESSAGE,
                cookies=[access_cookie, refresh_cookie]
            ).to_response()
        
        return ApiError(
            status_codes.HTTP_UNAUTHORIZED,
            http_messages.HTTP_LOGIN_INVALID_CREDENTIALS_MESSAGE
        ).to_response()
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR,
            f"Login failed: {str(e)}"
        ).to_response()


@router.post("/login-cloudflare", response_model=TokenResponse)
async def login_cloudflare(
    user_data: UserLoginCloudflareRequest,
    request: Request,
    db = Depends(get_db)
):
    """User login with Cloudflare Turnstile verification."""
    try:
        # Verify Turnstile token
        turnstile_response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': config.TURNSTILE_SECRET_KEY,
                'response': user_data.turnstileToken,
                # 'remoteip': request.client.host  # Optional
            }
        )

        if not turnstile_response.ok:
            return ApiError(
                status_codes.HTTP_BAD_REQUEST,
                "Failed to verify Turnstile token"
            ).to_response()

        turnstile_data = turnstile_response.json()
        if not turnstile_data.get('success'):
            return ApiError(
                status_codes.HTTP_BAD_REQUEST,
                "Invalid Turnstile token"
            ).to_response()

        # Proceed with login if Turnstile verification successful
        from ..handlers.users import Users
        access_token, refresh_token, user = Users.login(user_data.email, user_data.password)
        
        if access_token and refresh_token:
            return ApiResponse(
                status_codes.HTTP_OK,
                {'access_token': access_token, 'refresh_token': refresh_token},
                http_messages.HTTP_LOGIN_SUCCESS_MESSAGE
            ).to_response()

        return ApiError(
            status_codes.HTTP_UNAUTHORIZED,
            http_messages.HTTP_LOGIN_INVALID_CREDENTIALS_MESSAGE
        ).to_response()
        
    except Exception as e:
        logger.error(f"Cloudflare login error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR,
            f"Login failed: {str(e)}"
        ).to_response()


@router.put("/reset-password")
@router.post("/reset-password")
@router.patch("/reset-password")
async def update_password(
    password_data: PasswordUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update user password."""
    try:
        from ..handlers.users import Users
        
        Users.update_password(
            current_user.id, 
            password_data.old_password, 
            password_data.new_password
        )
        
        return ApiResponse(
            status_codes.HTTP_CREATED, 
            {"id": current_user.id},
            http_messages.HTTP_PASSWORD_UPDATE_SUCCESS_MESSAGE
        ).to_response()
        
    except Exception as e:
        logger.error(f"Password update error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR,
            f"Password update failed: {str(e)}"
        ).to_response()


@router.delete("/delete")
async def delete_user_self(
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete current user's account."""
    try:
        from ..handlers.users import Users
        
        Users.delete_user_by_id(current_user.id)
        return ApiResponse(
            status_code=200,
            data={"id": current_user.id},
            message="User deleted successfully"
        ).to_response()
        
    except Exception as e:
        logger.error(f"User deletion error: {str(e)}")
        return ApiError(
            status_code=500,
            message=f"Failed to delete user: {str(e)}"
        ).to_response()


@router.delete("/delete/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete user by ID (admin only)."""
    try:
        if current_user.user_type != 'ADMIN':
            return ApiError(
                status_code=status_codes.HTTP_UNAUTHORIZED, 
                message="Only ADMIN allowed"
            ).to_response()
        
        from ..handlers.users import Users
        Users.delete_user_by_id(user_id)
        
        return ApiResponse(
            status_codes.HTTP_CREATED, 
            {"id": user_id},
            http_messages.HTTP_DELETE_USER_SUCCESS_MESSAGE
        ).to_response()
        
    except Exception as e:
        logger.error(f"Admin user deletion error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR,
            f"Failed to delete user: {str(e)}"
        ).to_response()


@router.get("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: CurrentUser = Depends(get_refresh_user),
    redis_client = Depends(get_redis_blocklist)
):
    """Refresh access token using refresh token."""
    try:
        # Create new access token
        new_access_token = create_access_token(
            data={"sub": current_user.id}
        )
        
        return ApiResponse(
            200,
            {'access_token': new_access_token},
            "New token generated successfully"
        ).to_response()
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return ApiError(400, str(e)).to_response()


@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    redis_client = Depends(get_redis_blocklist)
):
    """Logout user and blacklist token."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return ApiError(400, "Invalid authorization header").to_response()
        
        token = auth_header.split(" ")[1]
        
        # Verify token to get jti
        from ..core.jwt_config import verify_token
        payload = verify_token(token, "access")
        jti = payload.get("jti")
        
        if jti and blacklist_token(jti, redis_client, ACCESS_EXPIRES):
            return ApiResponse(
                200, 
                {}, 
                "Access token revoked successfully"
            ).to_response()
        else:
            return ApiError(500, "Failed to revoke token").to_response()
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return ApiError(400, str(e)).to_response()


@router.get("/validate", response_model=UserResponse)
async def validate_user(current_user: CurrentUser = Depends(get_current_user)):
    """Validate user token and return user information."""
    user_info = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "user_type": current_user.user_type
    }
    
    # Add additional info if available
    if hasattr(current_user, 'hospital') and current_user.hospital:
        user_info["hospital"] = current_user.hospital
    if hasattr(current_user, 'doctor') and current_user.doctor:
        user_info["doctor"] = current_user.doctor
    
    return ApiResponse(
        status_codes.HTTP_OK,
        user_info,
        http_messages.HTTP_GET_USER_SUCCESS_MESSAGE
    ).to_response()


@router.post("/subscribe", response_model=MessageResponse)
async def subscribe_newsletter(
    subscription_data: NewsletterSubscribeRequest,
    db = Depends(get_db)
):
    """Subscribe to newsletter."""
    try:
        email = subscription_data.email.strip().lower()
        
        if not EMAIL_REGEX.match(email):
            return ApiError(
                status_codes.HTTP_BAD_REQUEST, 
                'Invalid email format'
            ).to_response()
        
        from ..handlers.newsletter import Newsletter
        created, record = Newsletter.subscribe(email)
        
        message = 'Successfully subscribed to future updates' if created else 'Already subscribed to updates'
        return ApiResponse(
            status_codes.HTTP_OK, 
            {'email': record.email}, 
            message
        ).to_response()
        
    except Exception as e:
        logger.error(f"Newsletter subscription error: {str(e)}")
        return ApiError(
            status_codes.HTTP_INTERNAL_SERVER_ERROR, 
            str(e)
        ).to_response()