"""Main FastAPI application entry point."""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
if os.getenv('DEPLOYMENT', default="DEVELOPMENT") != "PRODUCTION":
    load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.app_config import create_app
from .routers import auth, user, doctor, hospital, patient, profile, settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = create_app()

# Include routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/auth")
app.include_router(hospital.router, prefix="/api/auth")
app.include_router(doctor.router, prefix="/api/auth")
app.include_router(patient.router, prefix="/api/auth") 
app.include_router(settings.router, prefix="/api/auth")
app.include_router(profile.router, prefix="/api/auth")

if __name__ == "__main__":
    import uvicorn
    from .core import config
    
    port = config.APP_PORT
    logger.info(f"Starting FastAPI server on port {port}")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=config.DEPLOYMENT != "PRODUCTION",
        log_level="info"
    )