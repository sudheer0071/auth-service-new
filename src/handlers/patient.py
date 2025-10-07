"""Patient handler with stub implementations for FastAPI migration."""

import traceback
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from uuid_extensions import uuid7str
from ..models import PatientTable, CounterTable
from ..dependencies import get_session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from ..handlers.hospital import Hospital


logger = logging.getLogger(__name__)


class PatientError(Exception):
    """Base exception for Patient class errors."""
    pass


class PatientNotFoundError(PatientError):
    """Raised when a patient is not found."""
    pass


class ValidationError(PatientError):
    """Raised when data validation fails."""
    pass


class Patient:
    """Patient management service - stub implementation for FastAPI migration."""
    
    @classmethod
    def _get_uhid_counter(cls, hospital_id: str) -> int:
        """Get the current value of the UHID counter."""
        try:
            counter_row = Hospital.increment_hospital_counter_optimized(hospital_id=hospital_id)
            return counter_row['value']
        except SQLAlchemyError as e:
            logger.error(f"Error getting UHID counter: {traceback.format_exc()}")
            raise PatientError("Failed to get UHID counter") from e

    @classmethod
    def create_patient(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient in the database."""
        required_fields = ['fullname', 'gender', 'hospital_id']
        
        if not all(field in request_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in request_data]
            raise PatientError(f"Missing required fields: {', '.join(missing_fields)}")
        
        try:
            with get_session() as session:
                # Generate ID
                patient_id = uuid7str()
                request_data['id'] = patient_id
                
                # Set default values
                request_data.setdefault('height', 0)
                request_data.setdefault('weight', 0)
                
                # Get UHID if not provided
                if not request_data.get('uhid'):
                    request_data['uhid'] = str(cls._get_uhid_counter(request_data['hospital_id']))
                
                # Create patient object
                new_patient = PatientTable(
                    id=UUID(patient_id),
                    fullname=request_data['fullname'],
                    gender=request_data['gender'],
                    department=request_data.get('department'),
                    uhid=request_data['uhid'],
                    dob=request_data.get('dob'),
                    height=request_data['height'],
                    weight=request_data['weight'],
                    hospital_id=UUID(request_data['hospital_id']),
                    latest_date=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_patient)
                session.commit()
                
                return new_patient.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating patient: {traceback.format_exc()}")
            raise PatientError("Failed to create patient") from e
    
    @classmethod
    def get_patient(cls, patient_id: str, hospital_id: Optional[str] = None) -> Optional[Dict]:
        """Fetch a patient from the database based on the patient's id."""
        try:
            with get_session() as session:
                query = session.query(PatientTable).filter_by(id=UUID(patient_id))
                
                if hospital_id:
                    query = query.filter_by(hospital_id=UUID(hospital_id))
                
                patient = query.first()
                return patient.to_dict() if patient else None
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting patient: {traceback.format_exc()}")
            raise PatientError("Failed to get patient") from e
    
    @classmethod
    def get_patients_by_hospital_id(cls, search_param: str, hospital_id: str, sort_config: Dict[str, Any] = None) -> List[Dict]:
        """Fetch all patients of a hospital based on the hospital_id."""
        try:
            with get_session() as session:
                query = session.query(PatientTable).filter(
                    PatientTable.hospital_id == UUID(hospital_id),
                    PatientTable.fullname.ilike(f"%{search_param}%")
                )
                
                # Apply sorting
                if sort_config:
                    if sort_config.get("uhid"):
                        query = query.order_by(
                            PatientTable.uhid.asc() if int(sort_config["uhid"]) > 0 
                            else PatientTable.uhid.desc()
                        )
                    if sort_config.get("department"):
                        query = query.order_by(
                            PatientTable.department.asc() if int(sort_config["department"]) > 0 
                            else PatientTable.department.desc()
                        )
                    if sort_config.get("latest_date"):
                        query = query.order_by(
                            PatientTable.latest_date.asc() if int(sort_config["latest_date"]) > 0 
                            else PatientTable.latest_date.desc()
                        )
                
                patients = query.all()
                return [patient.to_dict() for patient in patients]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting patients by hospital: {traceback.format_exc()}")
            raise PatientError("Failed to get patients") from e
    
    @classmethod
    def get_all_patients_ADMIN_PERMISSION(cls, search_param: str, sort_config: Dict[str, Any] = None) -> List[Dict]:
        """Fetch all patients from the database."""
        try:
            with get_session() as session:
                query = session.query(PatientTable).filter(
                    PatientTable.fullname.ilike(f"%{search_param}%")
                )
                
                # Apply sorting
                if sort_config:
                    if sort_config.get("uhid"):
                        query = query.order_by(
                            PatientTable.uhid.asc() if int(sort_config["uhid"]) > 0 
                            else PatientTable.uhid.desc()
                        )
                    if sort_config.get("department"):
                        query = query.order_by(
                            PatientTable.department.asc() if int(sort_config["department"]) > 0 
                            else PatientTable.department.desc()
                        )
                    if sort_config.get("latest_date"):
                        query = query.order_by(
                            PatientTable.latest_date.asc() if int(sort_config["latest_date"]) > 0 
                            else PatientTable.latest_date.desc()
                        )
                
                patients = query.all()
                return [patient.to_dict() for patient in patients]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting all patients: {traceback.format_exc()}")
            raise PatientError("Failed to get patients") from e
    
    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[Dict]:
        """Fetch a patient from the database based on the patient's email."""
        try:
            with get_session() as session:
                # Assuming email column exists in PatientTable
                patient = session.query(PatientTable).filter_by(email=email).first()
                return patient.to_dict() if patient else None
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting patient by email: {traceback.format_exc()}")
            raise PatientError("Failed to get patient") from e
    
    @classmethod
    def get_patient_by_uhid(cls, uhid: str) -> Optional[Dict]:
        """Fetch a patient from the database based on the patient's UHID."""
        try:
            with get_session() as session:
                patient = session.query(PatientTable).filter_by(uhid=uhid).first()
                return patient.to_dict() if patient else None
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting patient by UHID: {traceback.format_exc()}")
            raise PatientError("Failed to get patient") from e
    
    @classmethod
    def delete_patient(cls, patient_id: str, hospital_id: Optional[str] = None) -> str:
        """Delete a patient from the database based on the patient's id."""
        try:
            with get_session() as session:
                query = session.query(PatientTable).filter_by(id=UUID(patient_id))
                
                if hospital_id:
                    query = query.filter_by(hospital_id=UUID(hospital_id))
                
                patient = query.first()
                if not patient:
                    raise PatientNotFoundError("Patient not found")
                
                session.delete(patient)
                session.commit()
                
                # Queue extraction job
                EdfQueue().push_extract({
                    "type": "DELETE",
                    "table": "PATIENT",
                    "id": patient_id
                })
                
                return patient_id
                
        except SQLAlchemyError as e:
            logger.error(f"Error deleting patient: {traceback.format_exc()}")
            raise PatientError("Failed to delete patient") from e
    
    @classmethod
    def update_patient(cls, patient_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a patient in the database based on the patient's id."""
        try:
            with get_session() as session:
                patient = session.query(PatientTable).filter_by(id=UUID(patient_id)).first()
                if not patient:
                    raise PatientNotFoundError("Patient not found")
                
                # Update fields
                for key, value in updated_data.items():
                    if hasattr(patient, key):
                        setattr(patient, key, value)
                
                patient.updated_at = datetime.now(timezone.utc)
                session.commit()
                
                return patient.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating patient: {traceback.format_exc()}")
            raise PatientError("Failed to update patient") from e
    
    @classmethod
    def search_patients(cls, query: str, hospital_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search patients by name, UHID, or department."""
        try:
            with get_session() as session:
                db_query = session.query(PatientTable)
                
                # Apply search filter
                search_filter = (
                    PatientTable.fullname.ilike(f"%{query}%") |
                    PatientTable.uhid.ilike(f"%{query}%") |
                    PatientTable.department.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
                
                # Filter by hospital if specified
                if hospital_id:
                    db_query = db_query.filter(PatientTable.hospital_id == UUID(hospital_id))
                
                # Apply limit
                patients = db_query.limit(limit).all()
                
                return [patient.to_dict() for patient in patients]
                
        except SQLAlchemyError as e:
            logger.error(f"Error searching patients: {traceback.format_exc()}")
            raise PatientError("Failed to search patients") from e