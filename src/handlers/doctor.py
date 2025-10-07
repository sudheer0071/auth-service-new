"""Doctor handler with stub implementations for FastAPI migration."""

import traceback
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from .users import Users
from ..dependencies import get_session
from ..models import DoctorTable, UserTable, HospitalTable
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class DoctorError(Exception):
    """Base exception for Doctor class errors."""
    pass


class DoctorNotFoundError(DoctorError):
    """Raised when a doctor is not found."""
    pass


class ValidationError(DoctorError):
    """Raised when data validation fails."""
    pass


class Doctor(Users):
    """Doctor management service - stub implementation for FastAPI migration."""
    
    def __init__(self) -> None:
        """Initialize the Doctor service."""
        super().__init__()

    @classmethod
    def get_all(cls, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all doctors with their details including user and hospital info."""
        try:
            with get_session() as session:
                query = session.query(
                    UserTable, DoctorTable, HospitalTable
                ).join(
                    DoctorTable, UserTable.id == DoctorTable.user_id
                ).join(
                    HospitalTable, DoctorTable.hospital_id == HospitalTable.id
                )
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(DoctorTable, key):
                            query = query.filter(getattr(DoctorTable, key) == value)
                        elif hasattr(UserTable, key):
                            query = query.filter(getattr(UserTable, key) == value)
                        elif hasattr(HospitalTable, key):
                            query = query.filter(getattr(HospitalTable, key) == value)
                
                results = query.all()
                
                doctor_list = []
                for user, doctor, hospital in results:
                    user_dict = user.to_dict(exclude_fields=['password'])
                    doctor_dict = doctor.to_dict()
                    hospital_dict = hospital.to_dict()
                    
                    # Combine the dictionaries
                    result_dict = {**user_dict, 'doctor': doctor_dict, 'hospital': hospital_dict}
                    doctor_list.append(result_dict)
                
                return doctor_list
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting all doctors: {traceback.format_exc()}")
            raise DoctorError("Failed to get doctors") from e
    
    @classmethod
    def get_doctors_by_hospital_id(cls, hospital_id: str) -> List[Dict]:
        """Get all doctors for a specific hospital."""
        try:
            with get_session() as session:
                doctors = session.query(DoctorTable).filter_by(hospital_id=UUID(hospital_id)).all()
                return [doctor.to_dict() for doctor in doctors]
        except SQLAlchemyError as e:
            logger.error(f"Error getting doctors by hospital: {traceback.format_exc()}")
            raise DoctorError("Failed to get doctors") from e
    
    @classmethod
    def get_doctor_by_userId(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get doctor by user ID."""
        # TODO: Implement actual logic from original Flask handler
        try:
            print("getting doctor by user id ", user_id)
            with get_session() as session:
                doctor = session.query(DoctorTable).filter_by(user_id=UUID(user_id)).first()
                print("doctor_info //////////", doctor)
                return doctor.to_dict() if doctor else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting doctor by user ID: {traceback.format_exc()}")
            raise DoctorError("Failed to get doctor") from e

    @classmethod
    def get_doctor_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get doctor (user + doctor record) by user email."""
        try:
            with get_session() as session:
                user = session.query(UserTable).filter(UserTable.email == email).first()
                if not user:
                    return None

                # Try to get doctor-specific record
                doctor = session.query(DoctorTable).filter_by(user_id=user.id).first()

                user_dict = user.to_dict(exclude_fields=['password'])
                if doctor:
                    return {**user_dict, 'doctor': doctor.to_dict()}

                return user_dict

        except SQLAlchemyError as e:
            logger.error(f"Error getting doctor by email: {traceback.format_exc()}")
            raise DoctorError("Failed to get doctor by email") from e
    
    
    @classmethod
    def create_doctor(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new doctor entry."""
        required_fields = ['department', 'years_of_exp', 'hospital_id', 'username', 'email', 'password']
        
        if not all(field in request_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in request_data]
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        try:
            with get_session() as session:
                # Create user first
                user_id = cls.create_user(
                    email=request_data['email'],
                    username=request_data['username'],
                    password=request_data['password'],
                    user_type='DOCTOR',
                    optional_fields=request_data,
                    session=session
                )
                session.flush()
                # Create doctor entry
                new_doctor = DoctorTable(
                    user_id=UUID(user_id),
                    department=request_data['department'],
                    years_of_exp=request_data['years_of_exp'],
                    hospital_id=UUID(request_data['hospital_id']),
                    signature=request_data.get('signature'),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_doctor)
                session.commit()
                
                # Get complete profile
                return cls.get_profile_by_id(UUID(user_id))
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating doctor: {traceback.format_exc()}")
            raise DoctorError("Failed to create doctor") from e
    
    @classmethod
    def delete_doctor_by_hospital(cls, user_id: str, hospital_id: str) -> bool:
        """Delete a doctor from a specific hospital."""
        try:
            with get_session() as session:
                # Check if doctor exists in the hospital
                doctor = session.query(DoctorTable).filter_by(
                    user_id=UUID(user_id),
                    hospital_id=UUID(hospital_id)
                ).first()
                
                if doctor:
                    # Delete the user (this will cascade to doctor table)
                    user = session.query(UserTable).filter_by(id=doctor.user_id).first()
                    if user:
                        session.delete(user)
                        session.commit()
                        return True
                
                return False
                
        except SQLAlchemyError as e:
            logger.error(f"Error deleting doctor: {traceback.format_exc()}")
            raise DoctorError("Failed to delete doctor") from e
    
    @classmethod
    def validate_doctor_profile_data(cls, data: dict) -> tuple[Optional[List[str]], Optional[Dict]]:
        """Validate the doctor profile data."""
        # First validate user profile data
        errors, validated_data = cls.validate_profile_data(data)
        errors = [] if not errors else errors
        validated_data = {} if not validated_data else validated_data
        
        # Validate doctor-specific fields
        if 'department' in data:
            department = data['department']
            if not isinstance(department, str) or len(department) > 100:
                errors.append("department must be a string with a maximum of 100 characters.")
            else:
                validated_data['department'] = department
        
        if 'years_of_exp' in data:
            years_of_exp = data['years_of_exp']
            if not isinstance(years_of_exp, int) or years_of_exp < 0:
                errors.append("years_of_exp must be an integer >= 0")
            else:
                validated_data['years_of_exp'] = years_of_exp
        
        if 'signature' in data:
            signature = data['signature']
            if not isinstance(signature, str):
                errors.append("signature must be a string")
            else:
                validated_data['signature'] = signature
        
        if errors:
            return errors, None
        return None, validated_data
    
    @classmethod
    def update_signature_by_id(cls, user_id: str, s3_bucket_key: str) -> Optional[Dict]:
        """Update doctor signature in the database."""
        try:
            with get_session() as session:
                doctor = session.query(DoctorTable).filter_by(user_id=UUID(user_id)).first()
                if not doctor:
                    raise DoctorNotFoundError("Doctor not found")
                
                doctor.signature = s3_bucket_key
                doctor.updated_at = datetime.now(timezone.utc)
                
                return doctor.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating signature: {traceback.format_exc()}")
            raise DoctorError("Failed to update signature") from e
    
    @classmethod
    def update_doctor_profile_by_id(cls, user_id: str, data_to_be_updated: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update doctor profile information."""
        try:
            with get_session() as session:
                # Update user profile first
                user_data = cls.update_profile_by_id(UUID(user_id), data_to_be_updated)
                
                # Validate doctor-specific data
                validation_errors, validated_data = cls.validate_doctor_profile_data(data_to_be_updated)
                
                if validation_errors:
                    return None
                
                # Update doctor-specific fields
                if validated_data:
                    doctor = session.query(DoctorTable).filter_by(user_id=UUID(user_id)).first()
                    if not doctor:
                        raise DoctorNotFoundError("Doctor not found")
                    
                    for key, value in validated_data.items():
                        if hasattr(doctor, key):
                            setattr(doctor, key, value)
                    
                    doctor.updated_at = datetime.now(timezone.utc)
                    session.commit()
                    
                    return doctor.to_dict()
                
                return user_data
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating doctor profile: {traceback.format_exc()}")
            raise DoctorError("Failed to update doctor profile") from e
        
    @classmethod
    def search_doctors(cls, query: str, hospital_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search doctors by name, email, username or department."""
        try:
            with get_session() as session:
                # Build the base query
                db_query = session.query(UserTable, DoctorTable).join(
                    DoctorTable, UserTable.id == DoctorTable.user_id
                )
                
                # Apply search filter
                search_filter = (
                    UserTable.name.ilike(f"%{query}%") |
                    UserTable.email.ilike(f"%{query}%") |
                    UserTable.username.ilike(f"%{query}%") |
                    DoctorTable.department.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
                
                # Filter by hospital if specified
                if hospital_id:
                    db_query = db_query.filter(DoctorTable.hospital_id == UUID(hospital_id))
                
                # Apply limit
                results = db_query.limit(limit).all()
                
                # Combine results
                doctors = []
                for user, doctor in results:
                    user_dict = user.to_dict(exclude_fields=['password'])
                    doctor_dict = doctor.to_dict()
                    doctors.append({**user_dict, 'doctor': doctor_dict})
                
                return doctors
                
        except SQLAlchemyError as e:
            logger.error(f"Error searching doctors: {traceback.format_exc()}")
            raise DoctorError("Failed to search doctors") from e
     