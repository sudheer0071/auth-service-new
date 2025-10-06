from sqlalchemy import Column, Enum, String, Integer, ForeignKey, DateTime, Date, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
from .users import valid_user_gender  # Import the existing gender enum
import enum
from uuid import UUID as PyUUID
from datetime import datetime, date

class PatientTable(Base):
    __tablename__ = 'patient'

    id = Column(UUID, primary_key=True)
    fullname = Column(String(100), nullable=False)
    gender = Column(Enum(valid_user_gender), nullable=False)
    department = Column(String(50))
    uhid = Column(String(50))
    dob = Column(Date)
    weight = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    hospital_id = Column(UUID, ForeignKey('hospital.id', ondelete='CASCADE'), nullable=False)
    latest_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self, exclude_fields=[]):
        """Convert model instance to dictionary with proper data type conversion."""
        # Get all columns
        columns = inspect(self.__class__).columns.keys()
        
        # Create dictionary
        data = {}
        for column in columns:
            if column not in exclude_fields:
                value = getattr(self, column)
                
                # Convert special types to strings
                if isinstance(value, PyUUID):
                    data[column] = str(value)
                elif isinstance(value, (datetime, date)):
                    data[column] = value.isoformat()
                elif isinstance(value, enum.Enum):  # Handle enums
                    data[column] = value.value
                elif value is None:
                    data[column] = None
                else:
                    data[column] = value
        
        return data