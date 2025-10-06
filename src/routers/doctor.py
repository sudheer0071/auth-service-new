from fastapi import APIRouter, Depends, Query, HTTPException, status, Form, UploadFile, File
from typing import Optional, Dict, Any
from ..core.auth_dependencies import CurrentUser, get_current_user, require_admin_or_hospital
from ..handlers.doctor import Doctor
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes
from ..utils import http_messages
from pydantic import BaseModel
from ..core import az_blob
import os

router = APIRouter(prefix="/doctors", tags=["doctors"])

AZURE_BLOB_CONTAINER_NAME = os.getenv('AZURE_BLOB_CONTAINER_NAME')

class DoctorRegistrationRequest(BaseModel):
    email: str
    fullname: str
    phone: str
    password: str
    confirm_password: str
    hospital_id: Optional[str] = None
    department: Optional[str] = None
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[int] = None
    registration_number: Optional[str] = None

class DoctorUpdateRequest(BaseModel):
    email: Optional[str] = None
    fullname: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[int] = None
    registration_number: Optional[str] = None
    signature: Optional[str] = None

@router.get("", response_model=Dict[str, Any])
async def get_all_doctors(
    q: Optional[str] = Query("", description="Search query"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all doctors"""
    try:
        if current_user.user_type != 'ADMIN':
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            
            if not hospital_id:
                raise HTTPException(
                    status_code=status_codes.HTTP_BAD_REQUEST,
                    detail="Hospital context missing for current user"
                )
            
            doctors_data = Doctor.get_doctors_by_hospital_id(q, hospital_id)
        else:
            doctors_data = Doctor.get_all_doctors_ADMIN_PERMISSION(q)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            doctors_data,
            http_messages.HTTP_GET_DOCTORS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{doctor_id}", response_model=Dict[str, Any])
async def get_doctor_by_id(
    doctor_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get doctor by ID"""
    try:
        if current_user.user_type != 'ADMIN':
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            doctor_info = Doctor.get_doctor(doctor_id, hospital_id)
        else:
            doctor_info = Doctor.get_doctor(doctor_id)
        
        if not doctor_info:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"Doctor with id {doctor_id} not found"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            doctor_info,
            http_messages.HTTP_GET_DOCTORS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{doctor_id}", response_model=Dict[str, Any])
async def update_doctor_by_id(
    doctor_id: str,
    data: DoctorUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update doctor by ID"""
    try:
        data_dict = data.dict(exclude_unset=True)
        
        if current_user.user_type == "HOSPITAL":
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            data_dict['hospital_id'] = hospital_id
        
        updated_doctor = Doctor.update_doctor(doctor_id, data_dict)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            updated_doctor,
            "Doctor updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail="Error while updating doctor!"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register_doctor(
    data: DoctorRegistrationRequest,
    current_user: CurrentUser = Depends(require_admin_or_hospital)
):
    """Register a new doctor"""
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
        
        if current_user.user_type == "HOSPITAL":
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            data_dict['hospital_id'] = hospital_id
        
        # Validate required fields
        required_fields = ['email', 'fullname', 'phone', 'password', 'hospital_id']
        missing_fields = [field for field in required_fields if not data_dict.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail=f"Missing fields: {', '.join(missing_fields)}"
            )
        
        # Check if doctor already exists
        existing_doctor = Doctor.get_doctor_by_email(data_dict['email'])
        if existing_doctor:
            raise HTTPException(
                status_code=status_codes.HTTP_CONFLICT,
                detail="Doctor already exists with this email"
            )
        
        doctor_info = Doctor.create_doctor(data_dict)
        
        return ApiResponse(
            status_codes.HTTP_CREATED,
            doctor_info,
            "Doctor registered successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{doctor_id}", response_model=Dict[str, Any])
async def delete_doctor(
    doctor_id: str,
    current_user: CurrentUser = Depends(require_admin_or_hospital)
):
    """Delete doctor by ID"""
    try:
        if current_user.user_type == 'ADMIN':
            Doctor.delete_doctor(doctor_id)
        else:
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            Doctor.delete_doctor(doctor_id, hospital_id)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"Doctor with id {doctor_id} deleted successfully"},
            "Doctor deleted successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{doctor_id}/upload_signature", response_model=Dict[str, Any])
async def upload_signature(
    doctor_id: str,
    contentType: str = Form(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Upload doctor signature"""
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
        
        signature_key = f"doctors/{doctor_id}/signature.png"
        
        # Generate presigned URL for upload
        presigned_url = az_blob.generate_presigned_url(
            container_name=AZURE_BLOB_CONTAINER_NAME,
            blob_key=signature_key,
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
                'key': signature_key,
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

@router.post("/{doctor_id}/confirm_signature_upload", response_model=Dict[str, Any])
async def confirm_signature_upload(
    doctor_id: str,
    data: Dict[str, str],
    current_user: CurrentUser = Depends(get_current_user)
):
    """Confirm doctor signature upload"""
    try:
        signature_key = data.get('key')
        
        if not signature_key:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Signature key is required"
            )
        
        if not az_blob.blob_exists(container_name=AZURE_BLOB_CONTAINER_NAME, blob_key=signature_key):
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail="Signature not found in storage"
            )
        
        # Update doctor signature in database
        result = Doctor.update_doctor_signature_by_id(doctor_id, key=signature_key)
        if not result:
            raise HTTPException(
                status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
                detail="Failed to update doctor signature"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            result,
            "Doctor signature updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )