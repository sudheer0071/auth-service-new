from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, Dict, Any
from ..core.auth_dependencies import CurrentUser, get_current_user, require_admin_or_hospital, require_admin_hospital_doctor
from ..handlers.patient import Patient
from ..utils.wrappers.api_response import ApiResponse
from ..utils.wrappers.api_error import ApiError
from ..utils import status_codes
from ..utils import http_messages
from pydantic import BaseModel

router = APIRouter(prefix="/patients", tags=["patients"])

class PatientRegistrationRequest(BaseModel):
    fullname: str
    gender: str
    hospital_id: Optional[str] = None
    uhid: Optional[str] = None
    height: Optional[float] = 0
    weight: Optional[float] = 0
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    department: Optional[str] = None

class PatientUpdateRequest(BaseModel):
    fullname: Optional[str] = None
    gender: Optional[str] = None
    uhid: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    department: Optional[str] = None

@router.get("", response_model=Dict[str, Any])
async def get_all_patients(
    q: Optional[str] = Query("", description="Search query"),
    uhid: Optional[str] = Query(None, description="Filter by UHID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    latest_date: Optional[str] = Query(None, description="Filter by latest date"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all patients"""
    try:
        sort_config = {
            "uhid": uhid,
            "department": department,
            "latest_date": latest_date
        }
        
        if current_user.user_type != 'ADMIN':
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            
            if not hospital_id:
                raise HTTPException(
                    status_code=status_codes.HTTP_BAD_REQUEST,
                    detail="Hospital context missing for current user"
                )
            
            patients_data = Patient.get_patients_by_hospital_id(q, hospital_id, sort_config=sort_config)
        else:
            patients_data = Patient.get_all_patients_ADMIN_PERMISSION(q, sort_config=sort_config)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            patients_data,
            http_messages.HTTP_GET_PATIENTS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{patient_id}", response_model=Dict[str, Any])
async def get_patient_by_id(
    patient_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get patient by ID"""
    try:
        if current_user.user_type != 'ADMIN':
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            patient_info = Patient.get_patient(patient_id, hospital_id)
        else:
            patient_info = Patient.get_patient(patient_id)
        
        if not patient_info:
            raise HTTPException(
                status_code=status_codes.HTTP_NOT_FOUND,
                detail=f"Patient with id {patient_id} is not present"
            )
        
        return ApiResponse(
            status_codes.HTTP_OK,
            patient_info,
            http_messages.HTTP_GET_PATIENTS_SUCCESS_MESSAGE
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{patient_id}", response_model=Dict[str, Any])
async def update_patient_by_id(
    patient_id: str,
    data: PatientUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update patient by ID"""
    try:
        data_dict = data.dict(exclude_unset=True)
        
        if current_user.user_type == "HOSPITAL":
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            data_dict['hospital_id'] = hospital_id
        
        updated_patient = Patient.update_patient(patient_id, data_dict)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            updated_patient,
            "Patient updated successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail="Error while updating patient!"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register_patient(
    data: PatientRegistrationRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Register a new patient"""
    try:
        data_dict = data.dict()
        
        if current_user.user_type == "HOSPITAL":
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            data_dict['hospital_id'] = hospital_id
        
        # Validate required fields
        required_fields = ['fullname', 'gender', 'hospital_id']
        missing_fields = [field for field in required_fields if not data_dict.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status_codes.HTTP_BAD_REQUEST,
                detail=f"Missing fields: {', '.join(missing_fields)}"
            )
        
        # Check if UHID already exists
        if data_dict.get('uhid'):
            existing_patient = Patient.get_patient_by_uhid(data_dict['uhid'])
            if existing_patient:
                raise HTTPException(
                    status_code=status_codes.HTTP_CONFLICT,
                    detail="Patient already exists with the same UHID"
                )
        
        # Set default values
        if 'height' not in data_dict or data_dict['height'] is None:
            data_dict['height'] = 0
        if 'weight' not in data_dict or data_dict['weight'] is None:
            data_dict['weight'] = 0
        
        patient_info = Patient.create_patient(data_dict)
        
        return ApiResponse(
            status_codes.HTTP_CREATED,
            patient_info,
            "Patient registered successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{patient_id}", response_model=Dict[str, Any])
async def delete_patient(
    patient_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete patient by ID"""
    try:
        if current_user.user_type == 'ADMIN':
            Patient.delete_patient(patient_id)
        else:
            hospital_info = getattr(current_user, 'hospital', None) or {}
            hospital_id = hospital_info.get('id') if isinstance(hospital_info, dict) else getattr(hospital_info, 'id', None)
            Patient.delete_patient(patient_id, hospital_id)
        
        return ApiResponse(
            status_codes.HTTP_OK,
            {"message": f"Patient with id {patient_id} deleted successfully"},
            "Patient deleted successfully"
        ).to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status_codes.HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )