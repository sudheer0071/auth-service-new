"""Application entry point for FastAPI Auth Service."""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    import uvicorn
    from src.core import config
    
    port = config.APP_PORT
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=config.DEPLOYMENT != "PRODUCTION",
        log_level="info"
    )