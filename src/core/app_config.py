"""FastAPI application configuration and setup."""

import os
import logging
from datetime import timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .database import init_db_pool
from .redis_client import get_redis_client
from ..utils.wrappers.api_error import ApiError
from ..utils.wrappers.api_response import ApiResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for dependency injection
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle FastAPI app startup and shutdown events."""
    global redis_client
    
    # Startup
    logger.info(f"Starting Auth Service in {config.DEPLOYMENT} mode")
    
    try:
        # Initialize database connection pool
        init_db_pool()
        logger.info("Database connection pool initialized")
    except Exception:
        logger.exception("Failed to initialise database connection pool")
        raise
        
    try:
        # Initialize Redis client
        redis_client = get_redis_client()
        logger.info("Redis client initialized")
    except Exception:
        logger.exception("Failed to initialize Redis client")
        # Continue without Redis for now, but log the error
        redis_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth Service")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Auth Service",
        description="Authentication and Authorization Service for Avinya NeuroTech",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if config.DEPLOYMENT != "PRODUCTION" else None,
        redoc_url="/api/redoc" if config.DEPLOYMENT != "PRODUCTION" else None,
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "message": exc.detail
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status_code": 500,
                "message": "Internal server error"
            }
        )
    
    # Health check endpoint
    @app.get("/api/auth/health")
    async def health_check():
        """Health check endpoint."""
        logger.info("Health check endpoint accessed")
        return ApiResponse(
            status_code=200,
            data={"health": True},
            message="Service is healthy"
        ).to_dict()
    
    # 404 handler
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        """Catch-all route for 404 responses."""
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "status_code": 404,
                "message": "Resource not found"
            }
        )
    
    return app


def get_redis_blocklist():
    """Get Redis client for JWT blocklist."""
    global redis_client
    return redis_client


# Access token expiry
ACCESS_EXPIRES = timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_EXPIRES = timedelta(minutes=config.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)