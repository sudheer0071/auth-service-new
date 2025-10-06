"""FastAPI response and error handling wrappers."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import Response
from fastapi.responses import JSONResponse
import os


class Cookie(BaseModel):
    """Cookie model for FastAPI responses."""
    key: str
    value: str = ""
    max_age: Optional[Union[timedelta, int]] = None
    expires: Optional[Union[str, datetime, int, float]] = None
    path: Optional[str] = "/"
    domain: Optional[str] = ".avinyaneurotech.com" if os.getenv('DEPLOYMENT') == "PRODUCTION" else None
    secure: bool = os.getenv('DEPLOYMENT') == "PRODUCTION"
    httponly: bool = False
    samesite: Optional[str] = None if os.getenv('DEPLOYMENT') == "PRODUCTION" else 'LAX'


class ApiResponse:
    """Standardized API response wrapper for FastAPI."""
    
    def __init__(
        self, 
        status_code: int, 
        data: Dict[str, Any] = {}, 
        message: str = "Success", 
        cookies: Optional[List[Cookie]] = None
    ):
        self.success = status_code < 400
        self.status_code = status_code
        self.data = data
        self.message = message
        self.cookies = cookies or []

    def format_datetime(self, obj: Any) -> Any:
        """Recursively convert datetime objects in the response data to ISO formatted strings."""
        if isinstance(obj, dict):
            return {key: self.format_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.format_datetime(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "success": self.success,
            "status_code": self.status_code,
            "data": self.format_datetime(self.data),
            "message": self.message
        }

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse with cookies."""
        response_data = self.to_dict()
        response = JSONResponse(content=response_data, status_code=self.status_code)
        
        # Set cookies if any
        for cookie in self.cookies:
            cookie_dict = cookie.dict()
            key = cookie_dict.pop('key')
            value = cookie_dict.pop('value')
            
            # Convert timedelta to seconds for max_age
            if isinstance(cookie_dict.get('max_age'), timedelta):
                cookie_dict['max_age'] = int(cookie_dict['max_age'].total_seconds())
            
            # Remove None values
            cookie_dict = {k: v for k, v in cookie_dict.items() if v is not None}
            
            response.set_cookie(key, value, **cookie_dict)
        
        return response


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