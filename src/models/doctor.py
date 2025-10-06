from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, Enum, JSON, Text, inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum
from uuid import UUID as PyUUID
from datetime import datetime, date

from ..core.database import Base

class DoctorTable(Base):
    __tablename__ = 'doctor'
    
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    department = Column(String(50))
    years_of_exp = Column(Integer)
    hospital_id = Column(UUID, ForeignKey('hospital.id', ondelete='CASCADE'), unique=False, nullable=False)
    signature = Column(Text)
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