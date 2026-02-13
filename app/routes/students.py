from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status, Depends
from app.services.csv_service import CSVService
from app.services.note_service import NoteService
from app.services.upload_service import (
    save_csv_file, save_upload_info, get_user_email,
    get_all_uploads, get_uploads_by_date_range, get_upload_by_id, delete_upload,
    get_dashboard_stats
)
from app.core.dependencies import (
    get_current_user_id, get_current_user_name, require_role, require_auth, get_token
)
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

router = APIRouter(prefix="/students", tags=["Students"])


def validate_year_format(year: str) -> bool:
    """Validate year format: YYYY-YYYY"""
    pattern = r'^\d{4}-\d{4}$'
    return bool(re.match(pattern, year))


@router.post("/upload-csv", dependencies=[Depends(require_role("admin"))])
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    year: str = Query(..., description="Year in format YYYY-YYYY (e.g., 2024-2025)"),
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Upload and process a CSV file containing student grades.
    Only processes the file and returns the data without saving.
    Use save-notes endpoint to save the file and notes.
    
    Args:
        file: CSV file to upload
        year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        current_user_id: Current authenticated user ID (from token)
    
    Returns:
        Dictionary containing processed student data (without saving)
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
        
        # Process CSV file
        students_data, semester = CSVService.process_csv_file(file_content, year)
        students_count = len(students_data)
        
        return {
            "message": "CSV file processed successfully",
            "year": year,
            "semester": semester,
            "students_count": students_count,
            "students": students_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}"
        )


@router.post("/save-notes", dependencies=[Depends(require_role("admin"))])
async def save_notes(
    file: UploadFile = File(..., description="CSV file to save"),
    year: str = Query(..., description="Year in format YYYY-YYYY (e.g., 2024-2025)"),
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Save CSV file, upload information, and student notes in MongoDB.
    Processes the file, saves it to disk, stores upload info, and saves notes.
    Each document uses 'matricule' as the unique identifier.
    Performs upsert operation (create if not exists, update if exists).
    
    Args:
        file: CSV file to save
        year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        current_user_id: Current authenticated user ID (from token)
    
    Returns:
        Dictionary with operation results including upload info
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
        
        # Process CSV file FIRST (before saving to disk)
        # This ensures we only save valid files
        students_data, semester = CSVService.process_csv_file(file_content, year)
        students_count = len(students_data)
        
        # Save file to disk
        saved_path = save_csv_file(file_content, file.filename)
        
        try:
            # Save upload information to database
            upload_info = save_upload_info(
                filename=file.filename,
                saved_path=saved_path,
                uploaded_by=current_user_id,
                uploaded_by_email=user_email,
                year=year,
                semester=semester,
                students_count=students_count,
                file_size=file_size
            )
        except Exception as db_error:
            # If database save fails, delete the file to prevent orphaned files
            from app.services.upload_service import delete_csv_file
            delete_csv_file(saved_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving upload information: {str(db_error)}"
            )
        
        # Save student notes
        try:
            notes_result = NoteService.save_multiple_students_notes(students_data)
        except Exception as notes_error:
            # If notes save fails, we still keep the file and upload info
            # but report the error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving notes: {str(notes_error)}"
            )
        
        return {
            "message": "File and notes saved successfully",
            "year": year,
            "semester": semester,
            "students_count": students_count,
            "upload_info": {
                "filename": upload_info["filename"],
                "saved_path": upload_info["saved_path"],
                "uploaded_by": str(upload_info["uploaded_by"]),
                "uploaded_by_email": upload_info["uploaded_by_email"],
                "uploaded_at": upload_info["uploaded_at"].isoformat(),
                "year": upload_info["year"],
                "semester": upload_info["semester"],
                "file_size": upload_info["file_size"]
            },
            "notes_results": notes_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file and notes: {str(e)}"
        )


@router.get("/notes", dependencies=[Depends(require_role("admin"))])
async def get_all_notes(
    semester: str = Query(None, description="Filter by semester (e.g., S3)"),
    department: str = Query(None, description="Filter by department"),
    year: str = Query(None, description="Filter by year in format YYYY-YYYY (e.g., 2024-2025)"),
    current_user_id: str = Depends(get_current_user_id)
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


@router.get("/statistics", dependencies=[Depends(require_role("admin"))])
async def get_statistics(
    semester: str = Query(None, description="Filter by semester (e.g., S3)"),
    department: str = Query(None, description="Filter by department"),
    year: str = Query(None, description="Filter by year in format YYYY-YYYY (e.g., 2024-2025)"),
    current_user_id: str = Depends(get_current_user_id)
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


@router.get("/notes/{matricule}", dependencies=[Depends(require_role("admin"))])
async def get_student_notes(
    matricule: int,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
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


@router.get("/my-notes", dependencies=[Depends(require_auth)])
async def get_my_notes(
    token: str = Depends(get_token)
) -> Dict[str, Any]:
    """
    Get current student's notes.
    Protected endpoint for students to access their own results.
    Extracts matricule from token (name field) and returns all student notes.
    
    Returns:
        Student notes document with all details including computed fields
    """
    try:
        # Get name from token (assuming name is matricule)
        name = get_current_user_name(token)
        
        # Try to convert name to int (matricule)
        try:
            matricule = int(name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student identifier in token"
            )
        
        # Get student notes
        notes = NoteService.get_student_notes(matricule)
        
        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No notes found for this student"
            )
        
        return notes
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving student notes: {str(e)}"
        )


@router.patch("/my-notes/{semester}/ispublic", dependencies=[Depends(require_auth)])
async def update_my_semester_ispublic(
    semester: str,
    is_public: bool = Query(..., description="Set isPublic to true or false"),
    token: str = Depends(get_token)
) -> Dict[str, Any]:
    """
    Update isPublic field for a specific semester of the current student.
    Protected endpoint for students to change visibility of their semester results.
    
    Args:
        semester: Semester code (e.g., "S3")
        is_public: Boolean value (true or false) for isPublic field
        token: Authentication token
    
    Returns:
        Dictionary with operation result
    """
    try:
        # Get name from token (assuming name is matricule)
        name = get_current_user_name(token)
        
        # Try to convert name to int (matricule)
        try:
            matricule = int(name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student identifier in token"
            )
        
        # Validate semester format
        if not semester.upper().startswith('S') or len(semester) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid semester format. Expected format: S1, S2, S3, etc."
            )
        
        # Update isPublic
        result = NoteService.update_semester_ispublic(matricule, semester.upper(), is_public)
        
        return {
            "message": f"Semester {semester} visibility updated successfully",
            "matricule": matricule,
            "semester": semester.upper(),
            "isPublic": is_public,
            "updated": result["updated"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating semester visibility: {str(e)}"
        )


@router.get("/public/{matricule}", dependencies=[Depends(require_auth)])
async def get_student_public_notes(
    matricule: int,
    token: str = Depends(get_token)
) -> Dict[str, Any]:
    """
    Get student information and public semester results.
    Protected endpoint for students to view other students' public results.
    Only returns semesters where isPublic = true.
    
    Args:
        matricule: Student matricule number
        token: Authentication token
    
    Returns:
        Student document with only public semesters and computed fields
    """
    try:
        # Get student public notes
        notes = NoteService.get_student_public_notes(matricule)
        
        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with matricule {matricule} not found or has no public results"
            )
        
        return notes
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving student public notes: {str(e)}"
        )


@router.patch("/my-notes/ispublic-globale", dependencies=[Depends(require_auth)])
async def update_my_ispublic_globale(
    is_public_globale: bool = Query(..., description="Set isPublicGlobale to true or false"),
    token: str = Depends(get_token)
) -> Dict[str, Any]:
    """
    Update isPublicGlobale field for the current student.
    Protected endpoint for students to change global visibility of their computed statistics.
    When isPublicGlobale is false, computed fields (moyenne_generale_allsemestre, 
    rang_generall_allsemestre, rang_allsemestre_dep) are not returned in public endpoint.
    
    Args:
        is_public_globale: Boolean value (true or false) for isPublicGlobale field
        token: Authentication token
    
    Returns:
        Dictionary with operation result
    """
    try:
        # Get name from token (assuming name is matricule)
        name = get_current_user_name(token)
        
        # Try to convert name to int (matricule)
        try:
            matricule = int(name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student identifier in token"
            )
        
        # Update isPublicGlobale
        result = NoteService.update_ispublic_globale(matricule, is_public_globale)
        
        return {
            "message": "Global visibility updated successfully",
            "matricule": matricule,
            "isPublicGlobale": is_public_globale,
            "updated": result["updated"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating global visibility: {str(e)}"
        )


@router.get("/uploads", dependencies=[Depends(require_role("admin"))])
async def get_uploads(
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get list of all uploaded CSV files with upload information.
    Can filter by date range.
    
    Query Parameters:
        start_date: Optional start date for filtering (ISO format)
        end_date: Optional end date for filtering (ISO format)
    
    Returns:
        Dictionary containing total count and list of uploads
    """
    try:
        if start_date or end_date:
            # Parse dates
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    # Try date only format
                    start_dt = datetime.fromisoformat(start_date)
            else:
                start_dt = datetime.min
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    # Try date only format and set to end of day
                    end_dt = datetime.fromisoformat(end_date)
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_dt = datetime.utcnow()
            
            uploads = get_uploads_by_date_range(start_dt, end_dt)
        else:
            uploads = get_all_uploads()
        
        return {
            "total": len(uploads),
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            },
            "uploads": uploads
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving uploads: {str(e)}"
        )


@router.get("/uploads/{upload_id}", dependencies=[Depends(require_role("admin"))])
async def get_upload_details(
    upload_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get details of a specific upload by ID.
    
    Args:
        upload_id: Upload document ID
    
    Returns:
        Upload document with all details
    """
    upload = get_upload_by_id(upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload not found with ID: {upload_id}"
        )
    return upload


@router.delete("/uploads/{upload_id}", dependencies=[Depends(require_role("admin"))])
async def delete_upload_file(
    upload_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Delete an uploaded CSV file, its database record, and all related notes.
    Extracts year and semester from upload info and deletes all notes
    associated with that semester and year.
    Only admins can delete uploads.
    
    Args:
        upload_id: Upload document ID
        current_user_id: Current authenticated user ID (from token)
    
    Returns:
        Dictionary with deletion results including notes deletion info
    """
    try:
        result = delete_upload(upload_id)
        
        if not result.get("success", False):
            if result.get("message") == "Upload not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Upload not found with ID: {upload_id}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting upload: {result.get('message', 'Unknown error')}"
                )
        
        return {
            "message": "Upload, file, and related notes deleted successfully",
            "upload_id": upload_id,
            "upload_deleted": result.get("upload_deleted", False),
            "file_deleted": result.get("file_deleted", False),
            "notes_deletion": result.get("notes_deletion"),
            "year": result.get("year"),
            "semester": result.get("semester")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting upload: {str(e)}"
        )


@router.get("/dashboard", dependencies=[Depends(require_role("admin"))])
async def get_dashboard(
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the admin main page.
    Returns overview statistics including total uploads, total students, 
    last upload information, and recent uploads list.
    
    Returns:
        Dictionary containing:
        - total_uploads: Total number of uploaded files
        - total_students: Total number of students
        - last_upload: Information about the last uploaded file
        - recent_uploads: List of recent uploads (last 5)
    """
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard statistics: {str(e)}"
        )

