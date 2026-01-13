from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status, Body, Depends
from app.services.csv_service import CSVService
from app.services.note_service import NoteService
from app.services.upload_service import save_csv_file, save_upload_info, get_user_email
from app.core.dependencies import get_current_user_id
from typing import Dict, Any, List
import re

router = APIRouter(prefix="/students", tags=["Students"])


def validate_year_format(year: str) -> bool:
    """Validate year format: YYYY-YYYY"""
    pattern = r'^\d{4}-\d{4}$'
    return bool(re.match(pattern, year))


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    year: str = Query(..., description="Year in format YYYY-YYYY (e.g., 2024-2025)"),
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Upload and process a CSV file containing student grades.
    Saves the file to disk and stores upload information in database.
    
    Args:
        file: CSV file to upload
        year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        current_user_id: Current authenticated user ID (from token)
    
    Returns:
        Dictionary containing processed student data and upload info
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    # Validate year format
    if not validate_year_format(year):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year must be in format YYYY-YYYY (e.g., 2024-2025)"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Get user email
        user_email = get_user_email(current_user_id)
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Save file to disk
        saved_path = save_csv_file(file_content, file.filename)
        
        # Process CSV file
        students_data = CSVService.process_csv_file(file_content, year)
        students_count = len(students_data)
        
        # Save upload information to database
        upload_info = save_upload_info(
            filename=file.filename,
            saved_path=saved_path,
            uploaded_by=current_user_id,
            uploaded_by_email=user_email,
            year=year,
            students_count=students_count,
            file_size=file_size
        )
        
        return {
            "message": "CSV file processed and saved successfully",
            "year": year,
            "students_count": students_count,
            "students": students_data,
            "upload_info": {
                "filename": upload_info["filename"],
                "saved_path": upload_info["saved_path"],
                "uploaded_by": str(upload_info["uploaded_by"]),
                "uploaded_by_email": upload_info["uploaded_by_email"],
                "uploaded_at": upload_info["uploaded_at"].isoformat(),
                "file_size": upload_info["file_size"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}"
        )


@router.post("/save-notes")
async def save_notes(
    students_data: Dict[int, Any] = Body(..., description="Dictionary of students data with matricule as key")
) -> Dict[str, Any]:
    """
    Save or update student notes in MongoDB collection 'notes'.
    Each document uses 'matricule' as the unique identifier.
    Performs upsert operation (create if not exists, update if exists).
    
    Args:
        students_data: Dictionary with matricule as key and student data as value
    
    Returns:
        Dictionary with operation results
    """
    try:
        result = NoteService.save_multiple_students_notes(students_data)
        return {
            "message": "Notes saved successfully",
            "results": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving notes: {str(e)}"
        )


@router.get("/notes")
async def get_all_notes(
    semester: str = Query(None, description="Filter by semester (e.g., S3)"),
    department: str = Query(None, description="Filter by department"),
    year: str = Query(None, description="Filter by year in format YYYY-YYYY (e.g., 2024-2025)")
) -> Dict[str, Any]:
    """
    Get student notes from MongoDB with optional filters.
    
    Query Parameters:
        semester: Filter by semester code (e.g., "S3")
        department: Filter by department name
        year: Filter by year in format "YYYY-YYYY" (e.g., "2024-2025")
    
    Returns:
        Dictionary containing total count and list of filtered student notes documents
    """
    try:
        # Validate year format if provided
        if year is not None and not validate_year_format(year):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year must be in format YYYY-YYYY (e.g., 2024-2025)"
            )
        
        # Get filtered notes
        if semester is not None or department is not None or year is not None:
            notes = NoteService.get_filtered_notes(
                semester=semester,
                department=department,
                year=year
            )
        else:
            notes = NoteService.get_all_notes()
        
        return {
            "total": len(notes),
            "filters": {
                "semester": semester,
                "department": department,
                "year": year
            },
            "notes": notes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notes: {str(e)}"
        )


@router.get("/statistics")
async def get_statistics(
    semester: str = Query(None, description="Filter by semester (e.g., S3)"),
    department: str = Query(None, description="Filter by department"),
    year: str = Query(None, description="Filter by year in format YYYY-YYYY (e.g., 2024-2025)")
) -> Dict[str, Any]:
    """
    Get statistics for students with optional filters.
    
    Query Parameters:
        semester: Filter by semester code (e.g., "S3")
        department: Filter by department name
        year: Filter by year in format "YYYY-YYYY" (e.g., "2024-2025")
    
    Returns:
        Dictionary containing statistics:
        - total_students: Total number of students
        - passed: Number of passed students
        - failed: Number of failed students
        - rattrapage: Number of students eligible for rattrapage
        - passed_percentage: Percentage of passed students
        - failed_percentage: Percentage of failed students
        - rattrapage_percentage: Percentage of students in rattrapage
        - average_distribution: Distribution by average ranges with counts and percentages
        - total_average: Overall average
    """
    try:
        # Validate year format if provided
        if year is not None and not validate_year_format(year):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year must be in format YYYY-YYYY (e.g., 2024-2025)"
            )
        
        statistics = NoteService.get_statistics(
            semester=semester,
            department=department,
            year=year
        )
        
        return {
            "filters": {
                "semester": semester,
                "department": department,
                "year": year
            },
            **statistics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )


@router.get("/notes/{matricule}")
async def get_student_notes(matricule: int) -> Dict[str, Any]:
    """
    Get student notes by matricule.
    
    Args:
        matricule: Student matricule number
    
    Returns:
        Student notes document
    """
    notes = NoteService.get_student_notes(matricule)
    if not notes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notes not found for matricule: {matricule}"
        )
    return notes

