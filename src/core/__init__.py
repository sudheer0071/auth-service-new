"""Core module for FastAPI Auth Service."""

from .config import *
from .database import SessionLocal, Base, engine, init_db_pool
from .redis_client import get_redis_client
from .app_config import create_app, get_redis_blocklist, ACCESS_EXPIRES, REFRESH_EXPIRES
from .jwt_config import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    is_token_blacklisted,
    blacklist_token,
    security
)
from . import az_blob

__all__ = [
    # Config
    "DEPLOYMENT", "APP_PORT", "SECRET_KEY", "JWT_SECRET_KEY", "JWT_ALGORITHM",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_REFRESH_TOKEN_EXPIRE_MINUTES",
    "ADMIN_USER_EMAIL", "ADMIN_USER_PASSWORD", "ADMIN_USER_ID", "ADMIN_USER_USERNAME",
    
    # Database
    "SessionLocal", "Base", "engine", "init_db_pool",
    
    # Redis
    "get_redis_client", "get_redis_blocklist",
    
    # App
    "create_app", "ACCESS_EXPIRES", "REFRESH_EXPIRES",
    
    # JWT
    "verify_password", "get_password_hash", "create_access_token", "create_refresh_token",
    "verify_token", "is_token_blacklisted", "blacklist_token", "security"
]