import mimetypes
import os
from ..dependencies import get_azure_blob_client
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from typing import Dict, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def upload_file_to_blob(file_path: str, container_name: str, blob_key: Optional[str] = None, 
                       content_type: Optional[str] = None, metadata: Optional[Dict[str, str]] = None,
                       overwrite: bool = True, progress_callback=None) -> bool:
    """
    Upload a file directly to Azure Blob Storage.
    
    Args:
        file_path (str): Local path to the file to upload
        container_name (str): Name of the Azure container
        blob_key (str, optional): Key/path for the blob. If None, uses the filename
        content_type (str, optional): MIME type. If None, auto-detects from file extension
        metadata (dict, optional): Custom metadata to attach to the blob
        overwrite (bool): Whether to overwrite existing blob (default: True)
        progress_callback: Optional callback function for upload progress
        
    Returns:
        bool: True if successfully uploaded, False otherwise
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Use filename if blob_key not provided
        if blob_key is None:
            blob_key = os.path.basename(file_path)
        
        # Auto-detect content type if not provided
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
        
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        # Check if blob exists and overwrite is False
        if not overwrite and blob_client.exists():
            logger.warning(f"Blob '{blob_key}' already exists and overwrite=False")
            return False
        
        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                content_type=content_type,
                metadata=metadata,
                overwrite=overwrite,
                progress_hook=progress_callback
            )
        
        file_size = os.path.getsize(file_path)
        logger.info(f"Successfully uploaded '{file_path}' to blob '{blob_key}' ({file_size} bytes)")
        return True
        
    except ResourceExistsError:
        logger.error(f"Blob '{blob_key}' already exists and overwrite=False")
        return False
    except Exception as e:
        logger.error(f"Error uploading file '{file_path}' to blob '{blob_key}': {str(e)}")
        return False


def upload_bytes_to_blob(data: bytes, container_name: str, blob_key: str,
                        content_type: str = 'application/octet-stream',
                        metadata: Optional[Dict[str, str]] = None,
                        overwrite: bool = True) -> bool:
    """
    Upload bytes data directly to Azure Blob Storage.
    
    Args:
        data (bytes): Binary data to upload
        container_name (str): Name of the Azure container
        blob_key (str): Key/path for the blob
        content_type (str): MIME type (default: application/octet-stream)
        metadata (dict, optional): Custom metadata to attach to the blob
        overwrite (bool): Whether to overwrite existing blob (default: True)
        
    Returns:
        bool: True if successfully uploaded, False otherwise
    """
    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        # Check if blob exists and overwrite is False
        if not overwrite and blob_client.exists():
            logger.warning(f"Blob '{blob_key}' already exists and overwrite=False")
            return False
        
        # Upload the data
        blob_client.upload_blob(
            data,
            content_type=content_type,
            metadata=metadata,
            overwrite=overwrite
        )
        
        logger.info(f"Successfully uploaded {len(data)} bytes to blob '{blob_key}'")
        return True
        
    except ResourceExistsError:
        logger.error(f"Blob '{blob_key}' already exists and overwrite=False")
        return False
    except Exception as e:
        logger.error(f"Error uploading data to blob '{blob_key}': {str(e)}")
        return False

def download_blob_by_key(container_name: str, blob_key: str, download_path: Optional[str] = None) -> Union[bytes, bool]:
    """
    Download a blob from Azure Blob Storage using the blob key.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path of the blob to download
        download_path (str, optional): Local file path to save the blob. If None, returns blob content as bytes
        
    Returns:
        bytes: Blob content if download_path is None
        bool: True if successfully downloaded to file, False otherwise
    """
    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        # Download blob content
        blob_data = blob_client.download_blob()
        
        if download_path:
            # Save to file
            with open(download_path, "wb") as file:
                file.write(blob_data.readall())
            logger.info(f"Successfully downloaded blob '{blob_key}' to '{download_path}'")
            return True
        else:
            # Return content as bytes
            logger.info(f"Successfully downloaded blob '{blob_key}' content")
            return blob_data.readall()
            
    except ResourceNotFoundError:
        logger.error(f"Blob '{blob_key}' not found in container '{container_name}'")
        return False if download_path else b""
    except Exception as e:
        logger.error(f"Error downloading blob '{blob_key}': {str(e)}")
        return False if download_path else b""


def download_blob_as_text(container_name: str, blob_key: str, encoding: str = 'utf-8') -> str:
    """
    Download a blob as text content.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path of the blob to download
        encoding (str): Text encoding (default: utf-8)
        
    Returns:
        str: Blob content as text, empty string if error
    """
    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        blob_data = blob_client.download_blob()
        content = blob_data.readall().decode(encoding)
        logger.info(f"Successfully downloaded blob '{blob_key}' as text")
        return content
        
    except ResourceNotFoundError:
        logger.error(f"Blob '{blob_key}' not found in container '{container_name}'")
        return ""
    except Exception as e:
        logger.error(f"Error downloading blob '{blob_key}' as text: {str(e)}")
        return ""


def generate_presigned_url(container_name: str, blob_key: str, expiresIn: int = 60, 
                          permissions: str = "r") -> Optional[str]:
    """
    Generate a presigned URL (SAS URL) for accessing a blob in Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path of the blob
        expiresIn (int): Number of seconds until the URL expires (default: 60)
        permissions (str): Permissions for the URL. Options:
            - "r" = read only (default)
            - "w" = write only
            - "a" = add (append)
            - "c" = create
            - "rw" = read and write
            - "rwd" = read, write, and delete
            - "rwac" = read, write, add, and create
            
    Returns:
        str: Presigned URL if successful, None if error
    """
    try:
        blob_service_client = get_azure_blob_client()
        
        # Create BlobSasPermissions object
        sas_permissions = {
            'read': False,
            'write': False,
            'delete': False,
            'add': False,
            'create': False
        }
        
        # Set permissions based on input string (blob-level permissions only)
        if "r" in permissions.lower():
            sas_permissions['read'] = True
        if "w" in permissions.lower():
            sas_permissions['write'] = True
        if "d" in permissions.lower():
            sas_permissions['delete'] = True
        if "a" in permissions.lower():
            sas_permissions['add'] = True
        if "c" in permissions.lower():
            sas_permissions['create'] = True
        
        # Note: 'list' permission is not available for blob-level SAS, only container-level
        
        # Ensure at least one permission is set
        if not any([sas_permissions['read'], sas_permissions['write'], 
                   sas_permissions['delete'], sas_permissions['add'], sas_permissions['create']]):
            logger.warning(f"No valid permissions found in '{permissions}', defaulting to read")
            sas_permissions['read'] = True
        
        # Calculate expiry time
        expiry_time = datetime.utcnow() + timedelta(seconds=expiresIn)
        
        # Get account credentials
        account_name = blob_service_client.account_name
        
        # Get account key from different credential types
        account_key = None
        if hasattr(blob_service_client.credential, 'account_key'):
            account_key = blob_service_client.credential.account_key
        elif hasattr(blob_service_client, '_credential') and hasattr(blob_service_client._credential, 'account_key'):
            account_key = blob_service_client._credential.account_key
        else:
            # Try to get from environment if not available from client
            account_key = os.getenv('AZURE_ACCOUNT_KEY')
        
        if not account_key:
            raise ValueError("Account key not found. SAS generation requires account key authentication.")
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_key,
            account_key=account_key,
            permission=BlobSasPermissions(**sas_permissions),
            expiry=expiry_time,
            start=datetime.utcnow()
        )
        
        # Construct the full URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_key}?{sas_token}"
        print(sas_token)
        
        logger.info(f"Generated presigned URL for blob '{blob_key}' (expires in {expiresIn} seconds)")
        return blob_url
        
    except Exception as e:
        logger.error(f"Error generating presigned URL for blob '{blob_key}': {str(e)}")
        return None

def generate_presigned_urls_batch(container_name: str, blob_keys: list, expiry_hours: int = 1,
                                 permissions: str = "r") -> dict:
    """
    Generate presigned URLs for multiple blobs.
    
    Args:
        container_name (str): Name of the Azure container
        blob_keys (list): List of blob keys/paths
        expiry_hours (int): Number of hours until URLs expire (default: 1)
        permissions (str): Permissions for the URLs (default: "r" for read-only)
        
    Returns:
        dict: Dictionary with blob_key as key and presigned_url as value
    """
    urls = {}
    
    for blob_key in blob_keys:
        url = generate_presigned_url(container_name, blob_key, expiry_hours, permissions)
        if url:
            urls[blob_key] = url
        else:
            urls[blob_key] = None
            
    logger.info(f"Generated {len([url for url in urls.values() if url])} presigned URLs out of {len(blob_keys)} requested")
    return urls


def generate_upload_presigned_url(container_name: str, blob_key: str, expiry_hours: int = 1,
                                 content_type: Optional[str] = None) -> Optional[str]:
    """
    Generate a presigned URL for uploading a blob to Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path where the blob will be stored
        expiry_hours (int): Number of hours until the URL expires (default: 1)
        content_type (str, optional): MIME type of the content to be uploaded
        
    Returns:
        str: Presigned upload URL if successful, None if error
    """
    try:
        blob_service_client = get_azure_blob_client()
        
        # Set permissions for upload (write)
        sas_permissions = BlobSasPermissions(write=True, create=True)
        
        # Calculate expiry time
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Get account name and key from the client
        account_name = blob_service_client.account_name
        account_key = blob_service_client.credential.account_key
        
        # Generate SAS token for upload
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_key,
            account_key=account_key,
            permission=sas_permissions,
            expiry=expiry_time,
            content_type=content_type
        )
        
        # Construct the full URL
        upload_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_key}?{sas_token}"
        
        logger.info(f"Generated presigned upload URL for blob '{blob_key}' (expires in {expiry_hours} hours)")
        return upload_url
        
    except Exception as e:
        logger.error(f"Error generating presigned upload URL for blob '{blob_key}': {str(e)}")
        return None


def delete_blob_by_key(container_name: str, blob_key: str, delete_snapshots: str = "include") -> bool:
    """
    Delete a blob from Azure Blob Storage using the blob key.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path of the blob to delete
        delete_snapshots (str): How to handle snapshots ('include', 'only', or None)
        
    Returns:
        bool: True if successfully deleted, False otherwise
    """
    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        # Delete the blob
        blob_client.delete_blob(delete_snapshots=delete_snapshots)
        logger.info(f"Successfully deleted blob '{blob_key}' from container '{container_name}'")
        return True
        
    except ResourceNotFoundError:
        logger.warning(f"Blob '{blob_key}' not found in container '{container_name}' - already deleted?")
        return True  # Consider as success since the goal (blob not existing) is achieved
    except Exception as e:
        logger.error(f"Error deleting blob '{blob_key}': {str(e)}")
        return False


def delete_multiple_blobs(container_name: str, blob_keys: list, delete_snapshots: str = "include") -> dict:
    """
    Delete multiple blobs from Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        blob_keys (list): List of blob keys/paths to delete
        delete_snapshots (str): How to handle snapshots ('include', 'only', or None)
        
    Returns:
        dict: Results with 'successful', 'failed', and 'not_found' lists
    """
    results = {
        'successful': [],
        'failed': [],
        'not_found': []
    }
    
    for blob_key in blob_keys:
        try:
            blob_service_client = get_azure_blob_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_key
            )
            
            blob_client.delete_blob(delete_snapshots=delete_snapshots)
            results['successful'].append(blob_key)
            logger.info(f"Successfully deleted blob '{blob_key}'")
            
        except ResourceNotFoundError:
            results['not_found'].append(blob_key)
            logger.warning(f"Blob '{blob_key}' not found")
        except Exception as e:
            results['failed'].append(blob_key)
            logger.error(f"Error deleting blob '{blob_key}': {str(e)}")
    
    return results


def delete_blobs_by_prefix(container_name: str, prefix: str, delete_snapshots: str = "include") -> dict:
    """
    Delete all blobs with a specific prefix from Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        prefix (str): Prefix to match blob names (e.g., "logs/2024/")
        delete_snapshots (str): How to handle snapshots ('include', 'only', or None)
        
    Returns:
        dict: Results with 'successful', 'failed', 'total_found', and 'deleted_blobs' lists
    """
    results = {
        'successful': [],
        'failed': [],
        'total_found': 0,
        'deleted_blobs': []
    }
    
    try:
        blob_service_client = get_azure_blob_client()
        container_client = blob_service_client.get_container_client(container_name)
        
        # List all blobs with the specified prefix
        blob_list = container_client.list_blobs(name_starts_with=prefix)
        
        for blob in blob_list:
            results['total_found'] += 1
            blob_name = blob.name
            
            try:
                blob_client = blob_service_client.get_blob_client(
                    container=container_name, 
                    blob=blob_name
                )
                
                blob_client.delete_blob(delete_snapshots=delete_snapshots)
                results['successful'].append(blob_name)
                results['deleted_blobs'].append(blob_name)
                logger.info(f"Successfully deleted blob '{blob_name}' with prefix '{prefix}'")
                
            except Exception as e:
                results['failed'].append(blob_name)
                logger.error(f"Error deleting blob '{blob_name}': {str(e)}")
        
        logger.info(f"Deleted {len(results['successful'])}/{results['total_found']} blobs with prefix '{prefix}'")
        
    except Exception as e:
        logger.error(f"Error listing blobs with prefix '{prefix}': {str(e)}")
    
    return results


def list_blobs_by_prefix(container_name: str, prefix: str, max_results: Optional[int] = None) -> list:
    """
    List all blobs with a specific prefix from Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        prefix (str): Prefix to match blob names
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        list: List of blob names matching the prefix
    """
    try:
        blob_service_client = get_azure_blob_client()
        container_client = blob_service_client.get_container_client(container_name)
        
        # List blobs with the specified prefix
        blob_list = container_client.list_blobs(name_starts_with=prefix)
        
        blob_names = []
        count = 0
        for blob in blob_list:
            if max_results and count >= max_results:
                break
            blob_names.append(blob.name)
            count += 1
        
        logger.info(f"Found {len(blob_names)} blobs with prefix '{prefix}'")
        return blob_names
        
    except Exception as e:
        logger.error(f"Error listing blobs with prefix '{prefix}': {str(e)}")
        return []


def blob_exists(container_name: str, blob_key: str) -> bool:
    """
    Check if a blob exists in Azure Blob Storage.
    
    Args:
        container_name (str): Name of the Azure container
        blob_key (str): Key/path of the blob to check
        
    Returns:
        bool: True if blob exists, False otherwise
    """
    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_key
        )
        
        # Check if blob exists
        return blob_client.exists()
        
    except Exception as e:
        logger.error(f"Error checking if blob '{blob_key}' exists: {str(e)}")
        return False