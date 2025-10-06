"""FastAPI error handling wrappers."""

from typing import Any, Dict
from fastapi.responses import JSONResponse


class ApiError:
    """Standardized API error wrapper for FastAPI."""
    
    def __init__(self, status_code: int, message: str = "Error"):
        self.success = False
        self.status_code = status_code
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "success": self.success,
            "status_code": self.status_code,
            "message": self.message
        }

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        response_data = self.to_dict()
        return JSONResponse(content=response_data, status_code=self.status_code)