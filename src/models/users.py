from sqlalchemy import Column, String, Date, DateTime, Enum, JSON, Text, inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum
from uuid import UUID as PyUUID
from datetime import datetime, date

from ..core.database import Base

class valid_user_type(str, enum.Enum):
    ADMIN = "ADMIN"
    HOSPITAL = "HOSPITAL"
    DOCTOR = "DOCTOR"

class valid_user_gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class UserTable(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    email = Column(String(321), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    name = Column(String(100))
    gender = Column('gender', Enum(valid_user_gender))
    dob = Column(Date)
    profile_pic = Column(Text)
    additional_info = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_type = Column(Enum(valid_user_type), nullable=False)
    
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