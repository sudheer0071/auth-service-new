from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from ..handlers.settings import Settings
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..core.auth_dependencies import CurrentUser, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdateRequest(BaseModel):
    # Add specific settings fields as needed
    notifications: bool = True
    theme: str = "light"
    language: str = "en"
    # Add other settings fields based on your requirements

@router.put("", response_model=Dict[str, Any])
@router.patch("", response_model=Dict[str, Any])
async def update_settings(
    updated_settings: Dict[str, Any],
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update user settings"""
    try:
        user_id = current_user.id

        if not updated_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Settings data is required"
            )

        # Update settings in database
        result = Settings.update_settings(updated_settings, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found for user"
            )

        return ApiResponse(200, result, "Settings updated successfully").to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=Dict[str, Any])
async def get_settings(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user settings"""
    try:
        user_id = current_user.id
        user_settings = Settings.get_settings(user_id)
        
        if not user_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found for user"
            )

        return ApiResponse(200, user_settings, "Settings retrieved successfully").to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/reset", response_model=Dict[str, Any])
async def reset_settings(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Reset user settings to default"""
    try:
        user_id = current_user.id
        result = Settings.reset_settings(user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found for user"
            )

        return ApiResponse(200, result, "Settings reset to default").to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )