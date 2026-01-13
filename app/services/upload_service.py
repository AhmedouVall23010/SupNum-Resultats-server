import os
from datetime import datetime
from typing import Dict, Any, Optional
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


def save_csv_file(file_content: bytes, original_filename: str) -> str:
    """
    Save CSV file to disk and return the saved path
    
    Args:
        file_content: File content as bytes
        original_filename: Original filename
    
    Returns:
        Saved file path
    """
    # Generate safe filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    # Remove any path separators from original filename for security
    safe_filename = os.path.basename(original_filename)
    # Create unique filename
    filename = f"{timestamp}_{safe_filename}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path


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
