from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
from uuid import UUID as PyUUID
import enum
from datetime import datetime, date

class HospitalTable(Base):
    __tablename__ = 'hospital'

    id = Column(UUID, primary_key=True)
    hospital_name = Column(String(321), nullable=False)
    admin = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    registration_number = Column(String(50), nullable=False)
    email = Column(String(321), nullable=False)
    phone = Column(String(15), nullable=False)
    logo = Column(Text)
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

class CounterTable(Base):
    __tablename__ = 'counters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(String(100), unique=True, nullable=False)
    value = Column(Integer, nullable=False, default=0)
    
    def to_dict(self, exclude_fields=[]):
            
        # Get all columns
        columns = inspect(self.__class__).columns.keys()
        
        # Create dictionary
        data = {}
        for column in columns:
            if column not in exclude_fields:
                data[column] = getattr(self, column)
        
        return data