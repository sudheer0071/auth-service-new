from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, Dict, Any
from ..core.auth_dependencies import CurrentUser, require_admin
from ..handlers.users import Users
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes
from ..utils import http_messages

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=Dict[str, Any])
async def get_all_users(
    q: Optional[str] = Query("", description="Search query"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    current_user: CurrentUser = Depends(require_admin)
):
    """Get all users (Admin only)"""
    try:
        users_data = Users.get_all_users(search_param=q, user_type=user_type)
        return ApiResponse(
            status_codes.HTTP_OK,
            users_data,
            http_messages.HTTP_GET_USERS_SUCCESS_MESSAGE
        ).to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
    user_id: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Get user by ID (Admin only)"""
    try:
        user_data = Users.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            user_data,
            http_messages.HTTP_GET_USER_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user_by_id(
    user_id: str,
    data: Dict[str, Any],
    current_user: CurrentUser = Depends(require_admin)
):
    """Update user by ID (Admin only)"""
    try:
        updated_user = Users.update_user_by_id(user_id, data)
        if not updated_user:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            updated_user,
            "User updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user_by_id(
    user_id: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Delete user by ID (Admin only)"""
    try:
        success = Users.delete_user_by_id(user_id)
        if not success:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"User with id {user_id} deleted successfully"},
            "User deleted successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{user_id}/activate", response_model=Dict[str, Any])
async def activate_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Activate user (Admin only)"""
    try:
        success = Users.activate_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"User with id {user_id} activated successfully"},
            "User activated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{user_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Deactivate user (Admin only)"""
    try:
        success = Users.deactivate_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"User with id {user_id} deactivated successfully"},
            "User deactivated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )