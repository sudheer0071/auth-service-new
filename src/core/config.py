"""Core configuration helpers for environment-driven settings."""

from __future__ import annotations

import os
from typing import Optional


def _get_env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _get_env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


# App Configuration
DEPLOYMENT: str = os.getenv("DEPLOYMENT", "DEVELOPMENT")
APP_PORT: int = _get_env_int("APP_PORT", 8000)
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")

# JWT Configuration
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_env_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 7200)  # 5 days
JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = _get_env_int("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", 43200)  # 30 days

# Admin Configuration
ADMIN_USER_EMAIL: str = os.getenv("ADMIN_USER_EMAIL", "")
ADMIN_USER_PASSWORD: str = os.getenv("ADMIN_USER_PASSWORD", "")
ADMIN_USER_ID: str = os.getenv("ADMIN_USER_ID", "")
ADMIN_USER_USERNAME: str = "admin"

# External Services
EDF_SERVICE_URL: str = os.getenv("EDF_SERVICE_URL", "http://edf:8002")
TURNSTILE_SECRET_KEY: str = os.getenv("TURNSTILE_SECRET_KEY", "")

# Redis configuration
REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = _get_env_int("REDIS_PORT", 6379)
REDIS_DB: int = _get_env_int("REDIS_DB", 0)
REDIS_USERNAME: Optional[str] = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
REDIS_CLUSTER_MODE: bool = _get_env_bool("REDIS_CLUSTER_MODE", False)
REDIS_SOCKET_TIMEOUT: float = _get_env_float("REDIS_SOCKET_TIMEOUT", 1.0)
REDIS_SOCKET_CONNECT_TIMEOUT: float = _get_env_float("REDIS_SOCKET_CONNECT_TIMEOUT", 1.0)
REDIS_HEALTH_CHECK_INTERVAL: int = _get_env_int("REDIS_HEALTH_CHECK_INTERVAL", 30)

# Queue configuration (Redis-based)
QUEUE_PREDICT_KEY: str = os.getenv("QUEUE_PREDICT_KEY", "edf_queue")
QUEUE_EXTRACT_KEY: str = os.getenv("QUEUE_EXTRACT_KEY", "edf_queue_extract")
QUEUE_HOST: str = os.getenv("QUEUE_HOST", "localhost")
QUEUE_PORT: int = _get_env_int("QUEUE_PORT", 5672)
QUEUE_USER: str = os.getenv("QUEUE_USER", "")
QUEUE_PASS: str = os.getenv("QUEUE_PASS", "")

# Database Configuration
DB_NAME: str = os.getenv("DB_NAME", "")
DB_USERNAME: str = os.getenv("DB_USERNAME", "")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DBTYPE: str = os.getenv("DBTYPE", "postgresql")
DB_DRIVER: str = os.getenv("DB_DRIVER", "psycopg2")
DB_SSLMODE: Optional[str] = os.getenv("DB_SSLMODE")
DB_LOCAL_SSLMODE: Optional[str] = os.getenv("DB_LOCAL_SSLMODE")
DB_POOL_RECYCLE: int = _get_env_int("DB_POOL_RECYCLE", 1800)
DB_POOL_TIMEOUT: int = _get_env_int("DB_POOL_TIMEOUT", 30)
DB_POOL_MIN: int = _get_env_int("DB_POOL_MIN", 1)
DB_POOL_MAX: int = _get_env_int("DB_POOL_MAX", 10)
DB_MAX_RETRIES: int = _get_env_int("DB_MAX_RETRIES", 3)

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING: Optional[str] = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_CLIENT_ID: Optional[str] = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET: Optional[str] = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID: Optional[str] = os.getenv("AZURE_TENANT_ID")