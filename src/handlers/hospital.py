"""Hospital handler with stub implementations for FastAPI migration."""
import traceback
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from ..models import HospitalTable, CounterTable
from ..dependencies import get_db, get_session
from sqlalchemy.exc import SQLAlchemyError
from ..handlers.users import Users
from sqlalchemy import text
from datetime import datetime, timezone
from uuid_extensions import uuid7str



logger = logging.getLogger(__name__)


class HospitalError(Exception):
    """Base exception for Hospital class errors."""
    pass


class HospitalNotFoundError(HospitalError):
    """Raised when a hospital is not found."""
    pass


class ValidationError(HospitalError):
    """Raised when data validation fails."""
    pass


class Hospital(Users):
    """Hospital management service - stub implementation for FastAPI migration."""
    def __init__(self) -> None:
        """Initialize the Hospital handler."""
        super().__init__()

    @classmethod
    def add_logo(cls, hospital_id: str, image_key: str) -> Optional[Dict]:
        """Update hospital logo in the database."""
        try:
            print("ADD logo function")
            with get_session() as session:
                hospital = session.query(HospitalTable).filter_by(id=hospital_id).first()
                if not hospital:
                    raise HospitalNotFoundError("Hospital not found")
                
                hospital.logo = image_key
                hospital.updated_at = datetime.now(timezone.utc)
                
                return hospital.to_dict()
        except SQLAlchemyError as e:
            logger.error(f"Error updating hospital logo: {traceback.format_exc()}")
            raise HospitalError("Failed to update hospital logo") from e
        
    @classmethod
    def get_hospital_by_admin(cls, admin_id: str) -> Optional[Dict]:
        """Fetch hospital details by hospital admin id."""
        try:
            with get_session() as session:
                hospital = session.query(HospitalTable).filter_by(admin=admin_id).first()
                return hospital.to_dict() if hospital else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting hospital by admin: {traceback.format_exc()}")
            raise HospitalError("Failed to retrieve hospital") from e
        
    @classmethod
    def get_hospital_by_id(cls, hospital_id: str) -> Optional[Dict]:
        """Fetch hospital details by hospital id."""
        try:
            with get_session() as session:
                hospital = session.query(HospitalTable).filter_by(id=hospital_id).first()
                return hospital.to_dict() if hospital else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting hospital by id: {traceback.format_exc()}")
            raise HospitalError("Failed to retrieve hospital") from e
    
    @classmethod
    def create_hospital(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hospital entry."""
        required_fields = ['hospital_name', 'admin', 'registration_number', 'email', 'phone']
        
        if not all(field in request_data for field in required_fields):
            raise HospitalError('Missing required fields')
        
        try:
            with get_session() as session:
                # Generate ID
                hospital_id = uuid7str()
                request_data['id'] = hospital_id
                
                # Create hospital object
                new_hospital = HospitalTable(
                    id=UUID(hospital_id),
                    hospital_name=request_data['hospital_name'],
                    admin=UUID(request_data['admin']),
                    registration_number=request_data['registration_number'],
                    email=request_data['email'],
                    phone=request_data['phone'],
                    logo=request_data.get('logo'),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_hospital)
                
                # Create counter record
                new_counter = CounterTable(
                    hospital_id=hospital_id,
                    value=10000
                )
                session.add(new_counter)
                
                return new_hospital.to_dict()
        except SQLAlchemyError as e:
            logger.error(f"Error creating hospital: {traceback.format_exc()}")
            raise HospitalError("Failed to create hospital") from e
    
    @classmethod
    def update_hospital(cls, hospital_id: str, update_data: Dict[str, Any]) -> Dict:
        """Update hospital information."""
        try:
            with get_session() as session:
                hospital = session.query(HospitalTable).filter_by(id=hospital_id).first()
                if not hospital:
                    raise HospitalNotFoundError("Hospital not found")
                
                # Update fields that are provided
                for field, value in update_data.items():
                    if hasattr(hospital, field):
                        setattr(hospital, field, value)
                
                hospital.updated_at = datetime.now(timezone.utc)
                
                return hospital.to_dict()
        except SQLAlchemyError as e:
            logger.error(f"Error updating hospital: {traceback.format_exc()}")
            raise HospitalError("Failed to update hospital") from e
    
    @classmethod
    def delete_hospital(cls, hospital_id: str) -> None:
        """Delete hospital by ID."""
        try:
            with get_session() as session:
                hospital = session.query(HospitalTable).filter_by(id=hospital_id).first()
                if not hospital:
                    raise HospitalNotFoundError("Hospital not found")
                
                # Find and delete associated counter
                counter = session.query(CounterTable).filter_by(hospital_id=hospital_id).first()
                if counter:
                    session.delete(counter)
                
                session.delete(hospital)
        except SQLAlchemyError as e:
            logger.error(f"Error deleting hospital: {traceback.format_exc()}")
            raise HospitalError("Failed to delete hospital") from e
    
    @classmethod
    def get_hospital_counter(cls, hospital_id: str) -> Optional[Dict]:
        """Get counter value for a hospital."""
        try:
            with get_session() as session:
                counter = session.query(CounterTable).filter_by(hospital_id=hospital_id).first()
                return counter.to_dict() if counter else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting hospital counter: {traceback.format_exc()}")
            raise HospitalError("Failed to get hospital counter") from e
    
    @classmethod
    def increment_hospital_counter_optimized(cls, hospital_id: str) -> Dict:
        """Increment counter value for a hospital using database-level atomic operation."""
        try:
            with get_session() as session:
                # PostgreSQL-specific atomic increment
                result = session.execute(
                    text("""
                        UPDATE counters 
                        SET value = value + 1 
                        WHERE hospital_id = :hospital_id 
                        RETURNING *
                    """),
                    {"hospital_id": hospital_id}
                )
                
                row = result.fetchone()
                if not row:
                    raise HospitalError("Counter not found for hospital")
                
                # Convert the result to a dictionary
                return dict(row._mapping)
                
        except SQLAlchemyError as e:
            logger.error(f"Error incrementing hospital counter: {traceback.format_exc()}")
            raise HospitalError("Failed to increment hospital counter") from e
    
    @classmethod
    def get_all_hospitals(cls, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get all hospitals with pagination."""
        try:
            with get_session() as session:
                hospitals = session.query(HospitalTable).limit(limit).offset(offset).all()
                return [hospital.to_dict() for hospital in hospitals]
        except SQLAlchemyError as e:
            logger.error(f"Error getting all hospitals: {traceback.format_exc()}")
            raise HospitalError("Failed to get hospitals") from e
    
    @classmethod
    def search_hospitals(cls, query: str, limit: int = 10) -> List[Dict]:
        """Search hospitals by name, email, or registration number."""
        try:
            with get_session() as session:
                search_filter = (
                    HospitalTable.hospital_name.ilike(f"%{query}%") |
                    HospitalTable.email.ilike(f"%{query}%") |
                    HospitalTable.registration_number.ilike(f"%{query}%")
                )
                hospitals = session.query(HospitalTable).filter(search_filter).limit(limit).all()
                
                return [hospital.to_dict() for hospital in hospitals]
        except SQLAlchemyError as e:
            logger.error(f"Error searching hospitals: {traceback.format_exc()}")
            raise HospitalError("Failed to search hospitals") from e