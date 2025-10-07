"""Settings handler stub for FastAPI Auth Service."""
import traceback
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from ..dependencies import get_session
from ..models import SettingsTable
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class SettingsError(Exception):
    """Base exception for Settings class errors."""
    pass


class SettingsNotFoundError(SettingsError):
    """Raised when a settings record is not found."""
    pass

class Settings:
    """Settings management service."""
    
    @classmethod
    def create_settings(cls, user_id: str) -> Dict[str, Any]:
        """Create default settings for a user."""
        try:
            with get_session() as session:
                # Check if settings already exist
                existing_settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                if existing_settings:
                    return existing_settings.to_dict()
                
                # Create new settings
                new_settings = SettingsTable(
                    user_id=UUID(user_id),
                    settings={},  # Empty JSON object
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_settings)
                session.commit()
                
                return new_settings.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating settings: {traceback.format_exc()}")
            raise SettingsError("Failed to create settings") from e
    
    @classmethod
    def get_settings(cls, user_id: str) -> Dict[str, Any]:
        """Get settings for a user, creating default settings if not found."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                
                if settings is None:
                    # Create default settings if they don't exist
                    return cls.create_settings(user_id)
                
                return settings.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting settings: {traceback.format_exc()}")
            raise SettingsError("Failed to get settings") from e
    
    @classmethod
    def update_settings(cls, updated_settings: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update settings for a user."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                
                if not settings:
                    # Create settings if they don't exist
                    settings = SettingsTable(
                        user_id=UUID(user_id),
                        settings=updated_settings,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(settings)
                else:
                    # Update existing settings
                    settings.settings = updated_settings
                    settings.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                return settings.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating settings: {traceback.format_exc()}")
            raise SettingsError("Failed to update settings") from e
    
    @classmethod
    def reset_settings(cls, user_id: str) -> Dict[str, Any]:
        """Reset settings to default empty object for a user."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                
                if not settings:
                    # Create default settings if they don't exist
                    return cls.create_settings(user_id)
                
                # Reset to empty settings
                settings.settings = {}
                settings.updated_at = datetime.now(timezone.utc)
                session.commit()
                
                return settings.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error resetting settings: {traceback.format_exc()}")
            raise SettingsError("Failed to reset settings") from e
    
    @classmethod
    def delete_settings(cls, user_id: str) -> None:
        """Delete settings for a user."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                if settings:
                    session.delete(settings)
                    session.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"Error deleting settings: {traceback.format_exc()}")
            raise SettingsError("Failed to delete settings") from e
    
    @classmethod
    def get_specific_setting(cls, user_id: str, setting_key: str) -> Optional[Any]:
        """Get a specific setting value for a user."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                
                if not settings:
                    cls.create_settings(user_id)
                    return None
                
                return settings.settings.get(setting_key)
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting specific setting: {traceback.format_exc()}")
            raise SettingsError("Failed to get specific setting") from e
    
    @classmethod
    def update_specific_setting(cls, user_id: str, setting_key: str, setting_value: Any) -> Dict[str, Any]:
        """Update a specific setting for a user."""
        try:
            with get_session() as session:
                settings = session.query(SettingsTable).filter_by(user_id=UUID(user_id)).first()
                
                if not settings:
                    # Create settings with the specific key-value
                    settings = SettingsTable(
                        user_id=UUID(user_id),
                        settings={setting_key: setting_value},
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(settings)
                else:
                    # Update specific setting
                    settings.settings[setting_key] = setting_value
                    settings.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                return settings.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating specific setting: {traceback.format_exc()}")
            raise SettingsError("Failed to update specific setting") from e

# Create singleton instance
_settings_instance = None

def get_settings_instance() -> Settings:
    """Get or create Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


Settings = get_settings_instance()