import traceback
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from ..handlers.users import Users
from ..handlers.doctor import Doctor
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..core.auth_dependencies import CurrentUser, get_current_user
from ..core import az_blob
import os
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["profile_User"])

AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME', "avinya-dev")
AZURE_BLOB_CONTAINER_NAME = os.getenv('AZURE_BLOB_CONTAINER_NAME')

class ProfileUpdateRequest(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    # Add other profile fields as needed

class ProfilePicUploadRequest(BaseModel):
    contentType: str

class ProfilePicConfirmRequest(BaseModel):
    key: str

@router.put("", response_model=Dict[str, Any])
@router.patch("", response_model=Dict[str, Any])
@router.post("", response_model=Dict[str, Any])
async def update_profile(
    updated_data: Dict[str, Any],
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update user profile"""
    try:
        user_id = current_user.id
        user_type = current_user.user_type

        if not updated_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile data is required"
            )

        # Validate profile data
        if user_type == 'DOCTOR':
            validation_errors, validated_data = Doctor.validate_doctor_profile_data(updated_data)
        else:
            validation_errors, validated_data = Users.validate_profile_data(updated_data)
        
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_errors
            )

        # Update profile in database
        if user_type == 'DOCTOR':
            result = Doctor.update_doctor_profile_by_id(user_id=user_id, data_to_be_updated=validated_data)
        else:
            result = Users.update_profile_by_id(user_id, updated_data=validated_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

        return ApiResponse(200, result, "Profile updated successfully").to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def generate_all_presigned_url(profile: Dict[str, Any]) -> dict:
    """Generate presigned URLs for profile images"""
    if not AZURE_BLOB_CONTAINER_NAME:
        return profile

    if profile.get("profile_pic"):
        image_key = profile.get("profile_pic")
        try:
            profile_pic_url = az_blob.generate_presigned_url(
                container_name=AZURE_BLOB_CONTAINER_NAME,
                blob_key=image_key,
                expiresIn=60*60*60,
                permissions='r'
            )
            if profile_pic_url:
                profile['profile_pic'] = profile_pic_url
        except Exception as exc:
            print(f"Unable to generate profile_pic SAS URL: {exc}")
    else:
        profile['profile_pic'] = None

    doctor_info = profile.get('doctor') or {}
    signature_key = doctor_info.get('signature')
    if signature_key:
        try:
            signature_url = az_blob.generate_presigned_url(
                container_name=AZURE_BLOB_CONTAINER_NAME,
                blob_key=signature_key,
                expiresIn=60*60*60,
                permissions='r'
            )
            if signature_url:
                doctor_info['signature'] = signature_url
        except Exception as exc:
            print(f"Unable to generate doctor signature SAS URL: {exc}")

    hospital_info = profile.get('hospital') or {}
    logo_key = hospital_info.get('logo')
    if logo_key:
        try:
            logo_url = az_blob.generate_presigned_url(
                container_name=AZURE_BLOB_CONTAINER_NAME,
                blob_key=logo_key,
                expiresIn=60*60*60,
                permissions='r'
            )
            if logo_url:
                hospital_info['logo'] = logo_url
        except Exception as exc:
            print(f"Unable to generate hospital logo SAS URL: {exc}")

    return profile

@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user profile"""
    try:
        print("reaching here/////// ")
        # current_user='test'
        user_id = current_user.id
        user_profile = Users.get_profile_by_id(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found for user"
            )
        
        generate_all_presigned_url(profile=user_profile)
        return ApiResponse(200, user_profile, "Profile retrieved successfully").to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/confirm_profile_pic_upload", response_model=Dict[str, Any])
async def confirm_profile_pic_upload(
    data: ProfilePicConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Confirm profile picture upload"""
    try:
        user_id = current_user.id
        image_key = data.key

        if not image_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image Key is required"
            )
        
        if not az_blob.blob_exists(container_name=AZURE_BLOB_CONTAINER_NAME, blob_key=image_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image not found in Storage"
            )

        # Update profile picture in database
        result = Users.update_profilepic_by_id(user_id, key=image_key)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile picture"
            )

        return ApiResponse(
            200,
            result,
            "Profile picture updated successfully"
        ).to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/upload_profile_pic", response_model=Dict[str, Any])
async def upload_profile_pic(
    data: ProfilePicUploadRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Upload profile picture"""
    try:
        user_id = current_user.id
        content_type = data.contentType

        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content type is required"
            )

        if content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Only JPEG and PNG are allowed"
            )
        
        image_key = f"users/{user_id}/profile_pic.png"

        # Generate presigned URL for upload
        presigned_url = az_blob.generate_presigned_url(
            container_name=AZURE_BLOB_CONTAINER_NAME,
            blob_key=image_key,
            permissions='wa',
            expiresIn=300
        )

        if not presigned_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate presigned URL"
            )
        
        return ApiResponse(
            200,
            {
                'upload_url': presigned_url,
                'key': image_key,
                'expires_in': 300
            },
            "Presigned URL generated successfully"
        ).to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )