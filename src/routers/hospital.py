from fastapi import APIRouter, Depends, Query, HTTPException, status, Form
from typing import Optional, Dict, Any
from ..core.auth_dependencies import CurrentUser, get_current_user, require_admin
from ..handlers.hospital import Hospital
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes
from ..utils import http_messages
from pydantic import BaseModel
from ..core import az_blob
import os

router = APIRouter(prefix="/hospitals", tags=["hospitals"])

AZURE_BLOB_CONTAINER_NAME = os.getenv('AZURE_BLOB_CONTAINER_NAME')

class HospitalRegistrationRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    confirm_password: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    registration_number: Optional[str] = None
    license_number: Optional[str] = None
    website: Optional[str] = None

class HospitalUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    registration_number: Optional[str] = None
    license_number: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None

@router.get("", response_model=Dict[str, Any])
async def get_all_hospitals(
    q: Optional[str] = Query("", description="Search query"),
    current_user: CurrentUser = Depends(require_admin)
):
    """Get all hospitals (Admin only)"""
    try:
        hospitals_data = Hospital.get_all_hospitals(search_param=q)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            hospitals_data,
            http_messages.HTTP_GET_HOSPITALS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{hospital_id}", response_model=Dict[str, Any])
async def get_hospital_by_id(
    hospital_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get hospital by ID"""
    try:
        hospital_info = Hospital.get_hospital(hospital_id)
        
        if not hospital_info:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"Hospital with id {hospital_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            hospital_info,
            http_messages.HTTP_GET_HOSPITALS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{hospital_id}", response_model=Dict[str, Any])
async def update_hospital_by_id(
    hospital_id: str,
    data: HospitalUpdateRequest,
    current_user: CurrentUser = Depends(require_admin)
):
    """Update hospital by ID (Admin only)"""
    try:
        data_dict = data.dict(exclude_unset=True)
        updated_hospital = Hospital.update_hospital(hospital_id, data_dict)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            updated_hospital,
            "Hospital updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail="Error while updating hospital!"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register_hospital(
    data: HospitalRegistrationRequest,
    current_user: CurrentUser = Depends(require_admin)
):
    """Register a new hospital (Admin only)"""
    try:
        data_dict = data.dict()
        
        # Validate password confirmation
        if data_dict['password'] != data_dict['confirm_password']:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Remove confirm_password from data
        del data_dict['confirm_password']
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'password']
        missing_fields = [field for field in required_fields if not data_dict.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail=f"Missing fields: {', '.join(missing_fields)}"
            )
        
        # Check if hospital already exists
        existing_hospital = Hospital.get_hospital_by_email(data_dict['email'])
        if existing_hospital:
            raise HTTPException(
                status_code=status_codes.HTTP_CONFLICT,
                detail="Hospital already exists with this email"
            )
        
        hospital_info = Hospital.create_hospital(data_dict)
        
        return ApiResponse(
            status_codes.HTTP_CREATED,
            hospital_info,
            "Hospital registered successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{hospital_id}", response_model=Dict[str, Any])
async def delete_hospital(
    hospital_id: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Delete hospital by ID (Admin only)"""
    try:
        Hospital.delete_hospital(hospital_id)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"Hospital with id {hospital_id} deleted successfully"},
            "Hospital deleted successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{hospital_id}/upload_logo", response_model=Dict[str, Any])
async def upload_logo(
    hospital_id: str,
    contentType: str = Form(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Upload hospital logo"""
    try:
        if not contentType:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Content type is required"
            )
        
        if contentType not in ['image/jpeg', 'image/jpg', 'image/png']:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Invalid image format. Only JPEG and PNG are allowed"
            )
        
        logo_key = f"hospitals/{hospital_id}/logo.png"
        
        # Generate presigned URL for upload
        presigned_url = az_blob.generate_presigned_url(
            container_name=AZURE_BLOB_CONTAINER_NAME,
            blob_key=logo_key,
            permissions='wa',
            expiresIn=300
        )
        
        if not presigned_url:
            raise HTTPException(
                status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
                detail="Could not generate presigned URL"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {
                'upload_url': presigned_url,
                'key': logo_key,
                'expires_in': 300
            },
            "Presigned URL generated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{hospital_id}/confirm_logo_upload", response_model=Dict[str, Any])
async def confirm_logo_upload(
    hospital_id: str,
    data: Dict[str, str],
    current_user: CurrentUser = Depends(get_current_user)
):
    """Confirm hospital logo upload"""
    try:
        logo_key = data.get('key')
        
        if not logo_key:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Logo key is required"
            )
        
        if not az_blob.blob_exists(container_name=AZURE_BLOB_CONTAINER_NAME, blob_key=logo_key):
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Logo not found in storage"
            )
        
        # Update hospital logo in database
        result = Hospital.update_hospital_logo_by_id(hospital_id, key=logo_key)
        if not result:
            raise HTTPException(
                status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
                detail="Failed to update hospital logo"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            result,
            "Hospital logo updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
