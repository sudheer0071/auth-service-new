from pydantic import BaseModel, field_validator, Field, ValidationError, ConfigDict
from typing import Optional, Dict, Union, List, Tuple
from datetime import datetime
import json
from enum import Enum
import logging
logger = logging.getLogger(__name__)
class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class ProfileUpdateData(BaseModel):
    name: Optional[str] = Field(None, max_length=100, min_length=1)
    profile_pic: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[Gender] = None
    additional_info: Optional[Union[Dict, str]] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

    @field_validator('dob', mode='before')
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("DOB must be a valid date in YYYY-MM-DD format.")
        return v

    @field_validator('gender', mode='before')
    @classmethod
    def validate_gender(cls, v: Optional[Gender]) -> Optional[str]:
        if v is not None:
            return v.upper()
        return v

    @field_validator('additional_info', mode='before')
    @classmethod
    def validate_additional_info(cls, v: Optional[Union[Dict, str]]) -> Optional[str]:
        if v is not None:
            if isinstance(v, dict):
                try:
                    return json.dumps(v)
                except (TypeError, ValueError):
                    raise ValueError("Invalid JSON data in additional_info")
            elif isinstance(v, str):
                return v
            else:
                raise ValueError("Additional_info must be a JSON object (dictionary) or string.")
        return v