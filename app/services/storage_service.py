"""
Storage service for handling file uploads.
Supports both local storage and AWS S3 cloud storage.
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from app.core.config import settings

# Storage type: "local" or "s3"
STORAGE_TYPE = settings.STORAGE_TYPE.lower()

# Local storage directory
UPLOADS_DIR = "uploads/csv"
if STORAGE_TYPE == "local":
    os.makedirs(UPLOADS_DIR, exist_ok=True)

# S3 client (lazy import)
_s3_client = None


def get_s3_client():
    """Get or create S3 client (lazy initialization)"""
    global _s3_client
    if _s3_client is None and STORAGE_TYPE == "s3":
        try:
            import boto3
            _s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install it with: pip install boto3"
            )
        except Exception as e:
            raise Exception(f"Failed to initialize S3 client: {str(e)}")
    return _s3_client


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename with timestamp and UUID to prevent collisions
    
    Args:
        original_filename: Original filename
    
    Returns:
        Unique filename
    """
    # Generate timestamp with microsecond precision
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S-%f")
    # Generate UUID for additional uniqueness
    unique_id = str(uuid.uuid4())[:8]
    # Remove any path separators from original filename for security
    safe_filename = os.path.basename(original_filename)
    # Create unique filename with timestamp, UUID, and original name
    filename = f"{timestamp}_{unique_id}_{safe_filename}"
    return filename


def save_file(file_content: bytes, original_filename: str) -> str:
    """
    Save file to storage (local or S3) and return the saved path/key
    
    Args:
        file_content: File content as bytes
        original_filename: Original filename
    
    Returns:
        Saved file path (for local) or S3 key (for S3)
    """
    filename = generate_unique_filename(original_filename)
    
    if STORAGE_TYPE == "local":
        # Local storage
        file_path = os.path.join(UPLOADS_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        return file_path
    
    elif STORAGE_TYPE == "s3":
        # S3 storage
        if not settings.AWS_S3_BUCKET_NAME:
            raise ValueError("AWS_S3_BUCKET_NAME must be set when using S3 storage")
        
        s3_key = f"csv/{filename}"
        s3_client = get_s3_client()
        
        try:
            s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType='text/csv'
            )
            return s3_key
        except Exception as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    else:
        raise ValueError(f"Unknown storage type: {STORAGE_TYPE}")


def delete_file(file_path_or_key: str) -> bool:
    """
    Delete a file from storage
    
    Args:
        file_path_or_key: Path to the file (for local) or S3 key (for S3)
    
    Returns:
        True if file was deleted, False otherwise
    """
    try:
        if STORAGE_TYPE == "local":
            # Local storage
            if os.path.exists(file_path_or_key):
                os.remove(file_path_or_key)
                return True
            return False
        
        elif STORAGE_TYPE == "s3":
            # S3 storage
            s3_client = get_s3_client()
            try:
                s3_client.delete_object(
                    Bucket=settings.AWS_S3_BUCKET_NAME,
                    Key=file_path_or_key
                )
                return True
            except Exception:
                return False
        
        else:
            return False
    
    except Exception:
        return False


def get_file_url(file_path_or_key: str) -> Optional[str]:
    """
    Get URL to access the file (for S3, returns presigned URL)
    
    Args:
        file_path_or_key: Path to the file (for local) or S3 key (for S3)
    
    Returns:
        URL to access the file, or None if not available
    """
    if STORAGE_TYPE == "local":
        # For local storage, return None (files are accessed via API)
        return None
    
    elif STORAGE_TYPE == "s3":
        # Generate presigned URL (valid for 1 hour)
        s3_client = get_s3_client()
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_S3_BUCKET_NAME,
                    'Key': file_path_or_key
                },
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception:
            return None
    
    return None


def file_exists(file_path_or_key: str) -> bool:
    """
    Check if file exists in storage
    
    Args:
        file_path_or_key: Path to the file (for local) or S3 key (for S3)
    
    Returns:
        True if file exists, False otherwise
    """
    try:
        if STORAGE_TYPE == "local":
            return os.path.exists(file_path_or_key)
        
        elif STORAGE_TYPE == "s3":
            s3_client = get_s3_client()
            try:
                s3_client.head_object(
                    Bucket=settings.AWS_S3_BUCKET_NAME,
                    Key=file_path_or_key
                )
                return True
            except Exception:
                return False
        
        return False
    
    except Exception:
        return False
