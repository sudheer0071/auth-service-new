"""FastAPI dependencies for database and external services."""

from contextlib import asynccontextmanager, contextmanager
import os
import traceback
import logging
from typing import Generator

from sqlalchemy.orm import Session
from fastapi import Depends
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.exceptions import AzureError

from .core.database import SessionLocal
from .core import config

logger = logging.getLogger(__name__)

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {traceback.format_exc()}")
        raise
    finally:
        db.close()


# Context manager for database sessions (alternative approach)
@contextmanager
def get_session():
    """Context manager for database sessions with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session error: {traceback.format_exc()}")
        raise
    finally:
        session.close()


# Synchronous context manager for handlers
@contextmanager
def get_sync_session():
    """Synchronous context manager for database sessions with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session error: {traceback.format_exc()}")
        raise
    finally:
        session.close()


# Azure Blob Storage dependencies
# Cache for blob service client (singleton pattern)
_blob_service_client = None

def get_azure_blob_client() -> BlobServiceClient:
    """
    Get Azure Blob Service Client with multiple authentication methods.
    
    Priority order:
    1. Connection String (easiest for development)
    2. Account Name + Key (simple but less secure)
    3. Service Principal (Azure AD - recommended for production)
    4. Default Azure Credential (managed identity, Azure CLI, etc.)
    
    Returns:
        BlobServiceClient: Configured Azure Blob Service Client
        
    Raises:
        ValueError: If no valid credentials are found
        AzureError: If authentication fails
    """
    global _blob_service_client
    
    # Return cached client if available
    if _blob_service_client:
        return _blob_service_client
    
    try:
        # Method 1: Connection String (recommended for development)
        if config.AZURE_STORAGE_CONNECTION_STRING:
            logger.info("Using Azure Storage Connection String authentication")
            _blob_service_client = BlobServiceClient.from_connection_string(
                config.AZURE_STORAGE_CONNECTION_STRING
            )
            # Test the connection
            _blob_service_client.get_account_information()
            return _blob_service_client
            
        # Method 2: Account Name + Key
        elif config.AZURE_STORAGE_ACCOUNT_NAME and config.AZURE_STORAGE_ACCOUNT_KEY:
            logger.info("Using Azure Storage Account Name + Key authentication")
            account_url = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            _blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=config.AZURE_STORAGE_ACCOUNT_KEY
            )
            # Test the connection
            _blob_service_client.get_account_information()
            return _blob_service_client
            
        # Method 3: Service Principal (Azure AD) - recommended for production
        elif (config.AZURE_CLIENT_ID and config.AZURE_CLIENT_SECRET and 
              config.AZURE_TENANT_ID and config.AZURE_STORAGE_ACCOUNT_NAME):
            logger.info("Using Azure AD Service Principal authentication")
            credential = ClientSecretCredential(
                tenant_id=config.AZURE_TENANT_ID,
                client_id=config.AZURE_CLIENT_ID,
                client_secret=config.AZURE_CLIENT_SECRET
            )
            account_url = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            _blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
            # Test the connection
            _blob_service_client.get_account_information()
            return _blob_service_client
            
        # Method 4: Default Azure Credential (managed identity, Azure CLI, etc.)
        elif config.AZURE_STORAGE_ACCOUNT_NAME:
            logger.info("Using Default Azure Credential authentication")
            credential = DefaultAzureCredential()
            account_url = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            _blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
            # Test the connection
            _blob_service_client.get_account_information()
            return _blob_service_client
            
        else:
            error_msg = (
                "Azure Storage credentials not configured. Please set one of:\n"
                "1. AZURE_STORAGE_CONNECTION_STRING\n"
                "2. AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY\n"
                "3. AZURE_STORAGE_ACCOUNT_NAME + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET + AZURE_TENANT_ID\n"
                "4. AZURE_STORAGE_ACCOUNT_NAME (with DefaultAzureCredential)"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    except AzureError as e:
        logger.error(f"Azure authentication failed: {e}")
        _blob_service_client = None
        raise AzureError(f"Failed to authenticate with Azure Storage: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Azure client initialization: {e}")
        _blob_service_client = None
        raise ValueError(f"Failed to initialize Azure Blob client: {e}")


def test_azure_connection() -> bool:
    """
    Test the Azure Blob Storage connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        client = get_azure_blob_client()
        account_info = client.get_account_information()
        logger.info(f"Azure Storage connection successful. Account kind: {account_info.get('account_kind')}")
        return True
    except Exception as e:
        logger.error(f"Azure Storage connection test failed: {e}")
        return False


def reset_azure_client():
    """
    Reset the cached Azure Blob Service Client.
    Useful for testing or when credentials change.
    """
    global _blob_service_client
    _blob_service_client = None
    logger.info("Azure Blob Service Client cache cleared")


# FastAPI dependency function for Azure Blob Storage client
async def get_azure_blob_dependency() -> BlobServiceClient:
    """
    FastAPI dependency function for Azure Blob Storage client.
    """
    return get_azure_blob_client()