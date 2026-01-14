import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.db.mongo import db, users_collection

# Get CSV uploads collection
csv_uploads_collection = db.csv_uploads

# Create uploads directory if it doesn't exist
UPLOADS_DIR = "uploads/csv"
os.makedirs(UPLOADS_DIR, exist_ok=True)


def get_user_email(user_id: str) -> Optional[str]:
    """Get user email from user ID"""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return user.get("email")
        return None
    except Exception:
        return None


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


def save_csv_file(file_content: bytes, original_filename: str) -> str:
    """
    Save CSV file to disk and return the saved path
    
    Args:
        file_content: File content as bytes
        original_filename: Original filename
    
    Returns:
        Saved file path
    """
    # Generate unique filename
    filename = generate_unique_filename(original_filename)
    file_path = os.path.join(UPLOADS_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path


def delete_csv_file(file_path: str) -> bool:
    """
    Delete a CSV file from disk
    
    Args:
        file_path: Path to the file to delete
    
    Returns:
        True if file was deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def save_upload_info(
    filename: str,
    saved_path: str,
    uploaded_by: str,
    uploaded_by_email: str,
    year: str,
    students_count: int,
    file_size: int
) -> Dict[str, Any]:
    """
    Save CSV upload information to MongoDB
    
    Args:
        filename: Original filename
        saved_path: Path where file is saved
        uploaded_by: User ID who uploaded the file
        uploaded_by_email: Email of user who uploaded
        year: Year string (e.g., "2024-2025")
        students_count: Number of students processed
        file_size: File size in bytes
    
    Returns:
        Saved document
    """
    upload_info = {
        "filename": filename,
        "saved_path": saved_path,
        "uploaded_by": ObjectId(uploaded_by),
        "uploaded_by_email": uploaded_by_email,
        "uploaded_at": datetime.utcnow(),
        "year": year,
        "students_count": students_count,
        "file_size": file_size
    }
    
    result = csv_uploads_collection.insert_one(upload_info)
    upload_info["_id"] = result.inserted_id
    return upload_info


def get_all_uploads() -> List[Dict[str, Any]]:
    """
    Get all CSV uploads from database
    
    Returns:
        List of all upload documents
    """
    uploads = list(csv_uploads_collection.find().sort("uploaded_at", -1))
    # Convert ObjectId to string for JSON serialization
    for upload in uploads:
        upload["_id"] = str(upload["_id"])
        upload["uploaded_by"] = str(upload["uploaded_by"])
        if isinstance(upload.get("uploaded_at"), datetime):
            upload["uploaded_at"] = upload["uploaded_at"].isoformat()
    return uploads


def get_uploads_by_date_range(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Get CSV uploads filtered by date range
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        List of upload documents in the date range
    """
    query = {
        "uploaded_at": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    uploads = list(csv_uploads_collection.find(query).sort("uploaded_at", -1))
    # Convert ObjectId to string for JSON serialization
    for upload in uploads:
        upload["_id"] = str(upload["_id"])
        upload["uploaded_by"] = str(upload["uploaded_by"])
        if isinstance(upload.get("uploaded_at"), datetime):
            upload["uploaded_at"] = upload["uploaded_at"].isoformat()
    return uploads


def get_upload_by_id(upload_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific upload by ID
    
    Args:
        upload_id: Upload document ID
    
    Returns:
        Upload document or None if not found
    """
    try:
        upload = csv_uploads_collection.find_one({"_id": ObjectId(upload_id)})
        if upload:
            upload["_id"] = str(upload["_id"])
            upload["uploaded_by"] = str(upload["uploaded_by"])
            if isinstance(upload.get("uploaded_at"), datetime):
                upload["uploaded_at"] = upload["uploaded_at"].isoformat()
        return upload
    except Exception:
        return None


def delete_upload(upload_id: str) -> bool:
    """
    Delete an upload record and its associated file
    
    Args:
        upload_id: Upload document ID
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        upload = csv_uploads_collection.find_one({"_id": ObjectId(upload_id)})
        if not upload:
            return False
        
        # Delete file from disk
        saved_path = upload.get("saved_path")
        if saved_path:
            delete_csv_file(saved_path)
        
        # Delete record from database
        result = csv_uploads_collection.delete_one({"_id": ObjectId(upload_id)})
        return result.deleted_count > 0
    except Exception:
        return False


def get_dashboard_stats() -> Dict[str, Any]:
    """
    Get dashboard statistics for the main page
    
    Returns:
        Dictionary containing:
        - total_uploads: Total number of uploaded files
        - total_students: Total number of students
        - last_upload: Information about the last uploaded file
        - recent_uploads: List of recent uploads (last 5)
    """
    from app.db.mongo import notes_collection
    
    # Get total uploads count
    total_uploads = csv_uploads_collection.count_documents({})
    
    # Get total students count
    total_students = notes_collection.count_documents({})
    
    # Get last upload
    last_upload_doc = csv_uploads_collection.find_one(
        sort=[("uploaded_at", -1)]
    )
    last_upload = None
    if last_upload_doc:
        last_upload = {
            "_id": str(last_upload_doc["_id"]),
            "filename": last_upload_doc.get("filename"),
            "uploaded_by_email": last_upload_doc.get("uploaded_by_email"),
            "uploaded_at": last_upload_doc.get("uploaded_at").isoformat() if isinstance(last_upload_doc.get("uploaded_at"), datetime) else None,
            "year": last_upload_doc.get("year"),
            "students_count": last_upload_doc.get("students_count", 0)
        }
    
    # Get recent uploads (last 5)
    recent_uploads_docs = list(csv_uploads_collection.find().sort("uploaded_at", -1).limit(5))
    recent_uploads = []
    for upload in recent_uploads_docs:
        recent_uploads.append({
            "_id": str(upload["_id"]),
            "filename": upload.get("filename"),
            "uploaded_by_email": upload.get("uploaded_by_email"),
            "uploaded_at": upload.get("uploaded_at").isoformat() if isinstance(upload.get("uploaded_at"), datetime) else None,
            "year": upload.get("year"),
            "students_count": upload.get("students_count", 0),
            "file_size": upload.get("file_size", 0)
        })
    
    return {
        "total_uploads": total_uploads,
        "total_students": total_students,
        "last_upload": last_upload,
        "recent_uploads": recent_uploads
    }
