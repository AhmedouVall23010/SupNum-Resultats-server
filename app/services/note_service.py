from typing import Dict, Any, List, Optional, Tuple
from app.db.mongo import notes_collection
from datetime import datetime
import re


class NoteService:
    @staticmethod
    def get_niveau_from_semester(semester: str) -> str:
        """
        Determine niveau (L1, L2, L3) from semester number.
        
        Args:
            semester: Semester string (e.g., "S1", "S2", "S3", etc.)
        
        Returns:
            Niveau string ("L1", "L2", or "L3")
        """
        # Extract semester number from string (e.g., "S3" -> 3)
        match = re.search(r'S(\d+)', semester.upper())
        if not match:
            return "L1"  # Default to L1 if can't parse
        
        semester_num = int(match.group(1))
        
        if semester_num <= 2:
            return "L1"
        elif semester_num <= 4:
            return "L2"
        else:
            return "L3"
    
    @staticmethod
    def compare_niveaux(niveau1: str, niveau2: str) -> int:
        """
        Compare two niveaux.
        
        Args:
            niveau1: First niveau (e.g., "L1")
            niveau2: Second niveau (e.g., "L2")
        
        Returns:
            -1 if niveau1 < niveau2, 0 if equal, 1 if niveau1 > niveau2
        """
        niveau_order = {"L1": 1, "L2": 2, "L3": 3}
        order1 = niveau_order.get(niveau1.upper(), 0)
        order2 = niveau_order.get(niveau2.upper(), 0)
        
        if order1 < order2:
            return -1
        elif order1 > order2:
            return 1
        else:
            return 0
    
    @staticmethod
    def extract_niveau_from_string(niveau_str: str) -> Optional[Tuple[str, str]]:
        """
        Extract niveau and year from niveau string.
        Format: "L1 – 2024-2025" or "L1 - 2024-2025"
        
        Args:
            niveau_str: Niveau string (e.g., "L1 – 2024-2025")
        
        Returns:
            Tuple of (niveau, year) or None if can't parse
        """
        if not niveau_str:
            return None
        
        # Match pattern: L1/L2/L3 followed by dash and year
        match = re.match(r'(L[123])\s*[–-]\s*(\d{4}-\d{4})', niveau_str.strip())
        if match:
            return (match.group(1), match.group(2))
        return None
    
    @staticmethod
    def calculate_niveau(semester: str, year: str) -> str:
        """
        Calculate niveau string from semester and year.
        Format: "L1 – 2024-2025"
        
        Args:
            semester: Semester string (e.g., "S3")
            year: Year string (e.g., "2024-2025")
        
        Returns:
            Niveau string (e.g., "L2 – 2024-2025")
        """
        niveau = NoteService.get_niveau_from_semester(semester)
        return f"{niveau} – {year}"
    
    @staticmethod
    def get_next_year(year: str) -> str:
        """
        Get next academic year.
        
        Args:
            year: Year string in format "2024-2025"
        
        Returns:
            Next year string (e.g., "2025-2026")
        """
        try:
            start_year, end_year = year.split('-')
            next_start = str(int(start_year) + 1)
            next_end = str(int(end_year) + 1)
            return f"{next_start}-{next_end}"
        except:
            return year
    
    @staticmethod
    def check_promotion_to_l2(student_doc: Dict[str, Any]) -> bool:
        """
        Check if student can be promoted to L2.
        Condition: (moyenne_generale S1 + moyenne_generale S2) / 2 >= 10 
                   AND (credit_total S1 + credit_total S2) >= 39
        
        Args:
            student_doc: Student document from database
        
        Returns:
            True if student can be promoted to L2, False otherwise
        """
        s1_data = student_doc.get("S1", {})
        s2_data = student_doc.get("S2", {})
        
        # Check if both S1 and S2 exist
        if not s1_data or not s2_data:
            return False
        
        # Get moyenne_generale for S1 and S2
        moy_s1 = NoteService.parse_moyenne(s1_data.get("moyenne_generale", 0))
        moy_s2 = NoteService.parse_moyenne(s2_data.get("moyenne_generale", 0))
        
        # Get credit_total for S1 and S2
        credit_s1 = s1_data.get("credit_total", 0)
        credit_s2 = s2_data.get("credit_total", 0)
        
        # Convert credits to int if needed
        try:
            credit_s1 = int(float(str(credit_s1).replace(',', '.')))
        except:
            credit_s1 = 0
        
        try:
            credit_s2 = int(float(str(credit_s2).replace(',', '.')))
        except:
            credit_s2 = 0
        
        # Calculate average
        avg_moy = (moy_s1 + moy_s2) / 2
        
        # Check conditions
        return avg_moy >= 10 and (credit_s1 + credit_s2) >= 39
    
    @staticmethod
    def check_promotion_to_l3(student_doc: Dict[str, Any]) -> bool:
        """
        Check if student can be promoted to L3.
        Condition: (moyenne_generale S3 + moyenne_generale S4) / 2 >= 10 
                   AND (credit_total S1 + credit_total S2) >= 39 
                   AND (credit_total S3 + credit_total S4) >= 60
        
        Args:
            student_doc: Student document from database
        
        Returns:
            True if student can be promoted to L3, False otherwise
        """
        s1_data = student_doc.get("S1", {})
        s2_data = student_doc.get("S2", {})
        s3_data = student_doc.get("S3", {})
        s4_data = student_doc.get("S4", {})
        
        # Check if all required semesters exist
        if not s1_data or not s2_data or not s3_data or not s4_data:
            return False
        
        # Get moyenne_generale for S3 and S4
        moy_s3 = NoteService.parse_moyenne(s3_data.get("moyenne_generale", 0))
        moy_s4 = NoteService.parse_moyenne(s4_data.get("moyenne_generale", 0))
        
        # Get credit_total for all semesters
        credit_s1 = s1_data.get("credit_total", 0)
        credit_s2 = s2_data.get("credit_total", 0)
        credit_s3 = s3_data.get("credit_total", 0)
        credit_s4 = s4_data.get("credit_total", 0)
        
        # Convert credits to int if needed
        try:
            credit_s1 = int(float(str(credit_s1).replace(',', '.')))
            credit_s2 = int(float(str(credit_s2).replace(',', '.')))
            credit_s3 = int(float(str(credit_s3).replace(',', '.')))
            credit_s4 = int(float(str(credit_s4).replace(',', '.')))
        except:
            return False
        
        # Calculate average for S3 and S4
        avg_moy = (moy_s3 + moy_s4) / 2
        
        # Check conditions
        credits_l1 = credit_s1 + credit_s2
        credits_l2 = credit_s3 + credit_s4
        
        return avg_moy >= 10 and credits_l1 >= 39 and credits_l2 >= 60
    
    @staticmethod
    def should_update_niveau(current_niveau: Optional[str], new_semester: str, new_year: str, student_doc: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if niveau should be updated based on business rules with promotion conditions.
        
        Special rules:
        - S2: Check promotion to L2: (moy S1 + moy S2)/2 >= 10 AND (credits S1 + credits S2) >= 39
          - If promoted: L2 – next_year
          - If not: L1 – current_year
        - S4: Check promotion to L3: (moy S3 + moy S4)/2 >= 10 AND (credits S1+S2) >= 39 AND (credits S3+S4) >= 60
          - If promoted: L3 – next_year
          - If not: L2 – current_year
        
        Args:
            current_niveau: Current niveau string (e.g., "L1 – 2024-2025") or None
            new_semester: New semester being added (e.g., "S2", "S4")
            new_year: Year of new semester (e.g., "2024-2025")
            student_doc: Student document with all semesters
        
        Returns:
            Tuple of (should_update: bool, new_niveau: str)
        """
        # Special handling for S2 (promotion to L2)
        if new_semester.upper() == "S2":
            can_promote = NoteService.check_promotion_to_l2(student_doc)
            if can_promote:
                # Promoted to L2, use next year
                next_year = NoteService.get_next_year(new_year)
                return (True, f"L2 – {next_year}")
            else:
                # Not promoted, stay in L1 with current year
                return (True, f"L1 – {new_year}")
        
        # Special handling for S4 (promotion to L3)
        if new_semester.upper() == "S4":
            can_promote = NoteService.check_promotion_to_l3(student_doc)
            if can_promote:
                # Promoted to L3, use next year
                next_year = NoteService.get_next_year(new_year)
                return (True, f"L3 – {next_year}")
            else:
                # Not promoted, stay in L2 with current year
                return (True, f"L2 – {new_year}")
        
        # For other semesters, use default logic
        new_niveau_level = NoteService.get_niveau_from_semester(new_semester)
        new_niveau_str = NoteService.calculate_niveau(new_semester, new_year)
        
        # If no current niveau, set to new niveau
        if not current_niveau:
            return (True, new_niveau_str)
        
        # Extract current niveau level and year
        current_info = NoteService.extract_niveau_from_string(current_niveau)
        if not current_info:
            # If can't parse current, update to new
            return (True, new_niveau_str)
        
        current_niveau_level, current_year = current_info
        
        # Compare niveaux
        comparison = NoteService.compare_niveaux(current_niveau_level, new_niveau_level)
        
        if comparison < 0:
            # New niveau is higher, update
            return (True, new_niveau_str)
        elif comparison > 0:
            # New niveau is lower, don't update (business rule: can't go back)
            return (False, current_niveau)
        else:
            # Same niveau level, check if same year
            if current_year == new_year:
                # Same niveau and year, keep current
                return (False, current_niveau)
            else:
                # Same niveau but different year, update to new year
                return (True, new_niveau_str)
    @staticmethod
    def save_student_notes(student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save or update student notes in MongoDB.
        Uses matricule as the _id (unique identifier) for upsert operation.
        Merges new data with existing data instead of replacing it completely.
        This allows adding new semesters without losing existing ones.
        
        Args:
            student_data: Dictionary containing student data with 'matricule' key
        
        Returns:
            Dictionary with operation result
        """
        if "matricule" not in student_data:
            raise ValueError("student_data must contain 'matricule' key")
        
        matricule = student_data["matricule"]
        
        # Check if document exists
        existing = notes_collection.find_one({"_id": matricule})
        
        if existing:
            # Document exists: merge new data with existing data
            # Create update document that merges data instead of replacing
            update_doc = {
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
            
            # Update basic fields (department, prenom, nom) if provided
            for field in ["department", "prenom", "nom"]:
                if field in student_data:
                    update_doc["$set"][field] = student_data[field]
            
            # Find semester and year from student_data to calculate niveau
            new_semester = None
            new_year = None
            
            # Merge semester data: add or update semesters without replacing existing ones
            # Find all semester keys (S1, S2, S3, etc.) in student_data
            for key, value in student_data.items():
                if key not in ["matricule", "department", "prenom", "nom"] and isinstance(value, dict):
                    # This is a semester (e.g., S3, S4)
                    # Use dot notation to set/update the semester data
                    update_doc["$set"][key] = value
                    
                    # Extract semester and year for niveau calculation
                    if not new_semester and "year" in value:
                        new_semester = key
                        new_year = value.get("year")
            
            # Calculate and update niveau if semester data is present
            if new_semester and new_year:
                # Get updated document with new semester to check promotion conditions
                # We need to merge the new semester data with existing data for checks
                temp_doc = existing.copy()
                temp_doc.update(update_doc.get("$set", {}))
                
                current_niveau = existing.get("niveau")
                should_update, new_niveau = NoteService.should_update_niveau(
                    current_niveau, new_semester, new_year, temp_doc
                )
                
                if should_update:
                    update_doc["$set"]["niveau"] = new_niveau
            
            # Perform update
            result = notes_collection.update_one(
                {"_id": matricule},
                update_doc,
                upsert=False
            )
            
            operation = "updated"
        else:
            # Document doesn't exist: create new one
            document = {
                "_id": matricule,
                **student_data,
                "isPublicGlobale": False,  # Default value for new students
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Calculate and set niveau for new document
            # Find semester and year from student_data
            new_semester = None
            new_year = None
            
            for key, value in student_data.items():
                if key not in ["matricule", "department", "prenom", "nom"] and isinstance(value, dict):
                    if "year" in value:
                        new_semester = key
                        new_year = value.get("year")
                        break
            
            if new_semester and new_year:
                # For new students, check promotion conditions
                should_update, new_niveau = NoteService.should_update_niveau(
                    None, new_semester, new_year, document
                )
                document["niveau"] = new_niveau
            
            result = notes_collection.insert_one(document)
            operation = "created"
        
        # Prepare return value
        if existing:
            # For update_one result
            return {
                "matricule": matricule,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": None,
                "operation": operation
            }
        else:
            # For insert_one result
            return {
                "matricule": matricule,
                "matched_count": 0,
                "modified_count": 0,
                "upserted_id": str(result.inserted_id) if result.inserted_id else None,
                "operation": operation
            }
    
    @staticmethod
    def save_multiple_students_notes(students_data: Dict[int, Any]) -> Dict[str, Any]:
        """
        Save or update multiple students' notes in MongoDB.
        
        Args:
            students_data: Dictionary with matricule as key and student data as value
        
        Returns:
            Dictionary with operation results
        """
        results = {
            "total": len(students_data),
            "created": 0,
            "updated": 0,
            "errors": []
        }
        
        for matricule, student_data in students_data.items():
            try:
                result = NoteService.save_student_notes(student_data)
                if result["operation"] == "created":
                    results["created"] += 1
                else:
                    results["updated"] += 1
            except Exception as e:
                results["errors"].append({
                    "matricule": matricule,
                    "error": str(e)
                })
        
        return results
    
    @staticmethod
    def parse_moyenne(moy) -> float:
        """Convert moyenne from string to float"""
        if moy is None:
            return 0.0
        try:
            if isinstance(moy, str):
                moy = moy.replace(',', '.')
            return float(moy)
        except:
            return 0.0
    
    @staticmethod
    def calculate_moyenne_generale_allsemestre(student_doc: Dict[str, Any]) -> float:
        """
        Calculate moyenne_generale_allsemestre from all semesters.
        moyenne_generale_allsemestre = (sum of all moyenne_generale) / count of semesters
        
        Args:
            student_doc: Student document from database
        
        Returns:
            Average of all moyenne_generale values, or 0.0 if no semesters
        """
        semesters = []
        for key, value in student_doc.items():
            if key not in ["_id", "matricule", "department", "prenom", "nom", "niveau", 
                          "created_at", "updated_at"]:
                if isinstance(value, dict) and "moyenne_generale" in value:
                    moy = NoteService.parse_moyenne(value.get("moyenne_generale"))
                    if moy > 0:  # Only count semesters with valid moyenne
                        semesters.append(moy)
        
        if not semesters:
            return 0.0
        
        return round(sum(semesters) / len(semesters), 2)
    
    @staticmethod
    def calculate_all_semester_ranks(all_students: List[Dict[str, Any]]) -> Dict[int, Dict[str, int]]:
        """
        Calculate ranks for all students based on moyenne_generale_allsemestre.
        Ranks are calculated separately by niveau (L3 first, then L2, then L1).
        
        Args:
            all_students: List of all student documents
        
        Returns:
            Dictionary with matricule as key and ranks as value
        """
        if not all_students:
            return {}
        
        # Calculate moyenne_generale_allsemestre for all students
        students_with_stats = []
        for student in all_students:
            moyenne_allsemestre = NoteService.calculate_moyenne_generale_allsemestre(student)
            niveau = student.get("niveau", "")
            
            # Extract niveau level (L1, L2, L3)
            niveau_info = NoteService.extract_niveau_from_string(niveau)
            niveau_level = niveau_info[0] if niveau_info else "L1"
            
            # Ensure matricule is int
            matricule = student["_id"]
            if isinstance(matricule, str):
                try:
                    matricule = int(matricule)
                except:
                    pass
            
            students_with_stats.append({
                "matricule": matricule,
                "department": student.get("department", ""),
                "moyenne_allsemestre": moyenne_allsemestre,
                "niveau_level": niveau_level
            })
        
        # Group students by niveau
        students_by_niveau = {}
        for student_info in students_with_stats:
            niveau_level = student_info["niveau_level"]
            if niveau_level not in students_by_niveau:
                students_by_niveau[niveau_level] = []
            students_by_niveau[niveau_level].append(student_info)
        
        # Calculate general ranks (all students, sorted by niveau then moyenne)
        # Order: L3 first, then L2, then L1
        all_students_sorted = []
        for niveau_level in ["L3", "L2", "L1"]:
            if niveau_level in students_by_niveau:
                niveau_students = sorted(
                    students_by_niveau[niveau_level],
                    key=lambda x: x["moyenne_allsemestre"],
                    reverse=True
                )
                all_students_sorted.extend(niveau_students)
        
        # Create ranks dictionary
        ranks = {}
        for rank, student_info in enumerate(all_students_sorted, start=1):
            matricule = student_info["matricule"]
            if matricule not in ranks:
                ranks[matricule] = {}
            ranks[matricule]["rang_generall_allsemestre"] = rank
        
        # Calculate department ranks (by niveau and department)
        for niveau_level in ["L3", "L2", "L1"]:
            if niveau_level not in students_by_niveau:
                continue
            
            # Group by department
            dept_students = {}
            for student_info in students_by_niveau[niveau_level]:
                dept = student_info["department"]
                if dept not in dept_students:
                    dept_students[dept] = []
                dept_students[dept].append(student_info)
            
            # Calculate ranks for each department
            for dept, dept_list in dept_students.items():
                dept_list_sorted = sorted(
                    dept_list,
                    key=lambda x: x["moyenne_allsemestre"],
                    reverse=True
                )
                
                for rank, student_info in enumerate(dept_list_sorted, start=1):
                    matricule = student_info["matricule"]
                    if matricule not in ranks:
                        ranks[matricule] = {}
                    ranks[matricule]["rang_allsemestre_dep"] = rank
        
        return ranks
    
    @staticmethod
    def add_computed_fields(student_doc: Dict[str, Any], all_students: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add computed fields to student document.
        These fields are calculated dynamically and not stored in database.
        
        Args:
            student_doc: Student document
            all_students: Optional list of all students for rank calculation
        
        Returns:
            Student document with computed fields added
        """
        # Calculate moyenne_generale_allsemestre
        moyenne_allsemestre = NoteService.calculate_moyenne_generale_allsemestre(student_doc)
        student_doc["moyenne_generale_allsemestre"] = moyenne_allsemestre
        
        # Calculate ranks if all_students provided
        if all_students:
            ranks = NoteService.calculate_all_semester_ranks(all_students)
            matricule = student_doc.get("_id") or student_doc.get("matricule")
            # Convert to int if it's a string (for comparison with ranks dict keys)
            if isinstance(matricule, str):
                try:
                    matricule = int(matricule)
                except:
                    pass
            
            if matricule in ranks:
                student_doc["rang_generall_allsemestre"] = ranks[matricule].get("rang_generall_allsemestre", 0)
                student_doc["rang_allsemestre_dep"] = ranks[matricule].get("rang_allsemestre_dep", 0)
            else:
                student_doc["rang_generall_allsemestre"] = 0
                student_doc["rang_allsemestre_dep"] = 0
        else:
            student_doc["rang_generall_allsemestre"] = 0
            student_doc["rang_allsemestre_dep"] = 0
        
        return student_doc
    
    @staticmethod
    def get_student_public_notes(matricule: int) -> Optional[Dict[str, Any]]:
        """
        Get student notes with only public semesters (isPublic = true).
        Returns student information and only semesters that are marked as public.
        
        Args:
            matricule: Student matricule number (used as _id)
        
        Returns:
            Student notes document with only public semesters, or None if not found
        """
        document = notes_collection.find_one({"_id": matricule})
        if not document:
            return None
        
        # Convert _id (matricule) to string for JSON serialization
        document["_id"] = str(document["_id"])
        
        # Get isPublicGlobale value
        is_public_globale = document.get("isPublicGlobale", False)
        
        # Filter semesters to only include public ones
        filtered_doc = {
            "_id": document["_id"],
            "matricule": document.get("matricule"),
            "department": document.get("department"),
            "prenom": document.get("prenom"),
            "nom": document.get("nom"),
            "niveau": document.get("niveau")
        }
        
        # Add only public semesters
        for key, value in document.items():
            if key not in ["_id", "matricule", "department", "prenom", "nom", "niveau", 
                          "created_at", "updated_at", "isPublicGlobale"]:
                if isinstance(value, dict) and value.get("isPublic") is True:
                    filtered_doc[key] = value
        
        # Add computed fields only if isPublicGlobale is true
        if is_public_globale:
            # Get all students for rank calculation (needed for computed fields)
            all_students = list(notes_collection.find())
            for s in all_students:
                s["_id"] = str(s["_id"])
            
            # Add computed fields
            filtered_doc = NoteService.add_computed_fields(filtered_doc, all_students)
        # If isPublicGlobale is false, don't include computed fields at all
        
        return filtered_doc
    
    @staticmethod
    def get_student_notes(matricule: int) -> Dict[str, Any]:
        """
        Get student notes by matricule.
        Includes computed fields: moyenne_generale_allsemestre, rang_generall_allsemestre, rang_allsemestre_dep.
        
        Args:
            matricule: Student matricule number (used as _id)
        
        Returns:
            Student notes document with computed fields or None if not found
        """
        document = notes_collection.find_one({"_id": matricule})
        if document:
            # Convert _id (matricule) to string for JSON serialization
            document["_id"] = str(document["_id"])
            
            # Get all students for rank calculation
            all_students = list(notes_collection.find())
            # Convert _id to string for consistency
            for s in all_students:
                s["_id"] = str(s["_id"])
            
            # Add computed fields
            document = NoteService.add_computed_fields(document, all_students)
        
        return document
    
    @staticmethod
    def get_all_notes() -> List[Dict[str, Any]]:
        """
        Get all student notes.
        Includes computed fields: moyenne_generale_allsemestre, rang_generall_allsemestre, rang_allsemestre_dep.
        
        Returns:
            List of all student notes documents with computed fields
        """
        documents = list(notes_collection.find())
        # Convert _id (matricule) to string for JSON serialization
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        
        # Add computed fields to all documents
        for doc in documents:
            NoteService.add_computed_fields(doc, documents)
        
        return documents
    
    @staticmethod
    def get_filtered_notes(
        semester: str = None,
        department: str = None,
        year: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get filtered student notes by semester, department, and/or year.
        
        Args:
            semester: Semester code (e.g., "S3")
            department: Department name
            year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        
        Returns:
            List of filtered student notes documents
        """
        # Get all documents
        documents = list(notes_collection.find())
        filtered_docs = []
        
        for doc in documents:
            # Filter by department
            if department is not None:
                if doc.get("department") != department:
                    continue
            
            # Filter by semester and/or year
            if semester is not None or year is not None:
                # Check if the document has the specified semester
                if semester is not None and semester not in doc:
                    continue
                
                # If semester is specified, check year within that semester
                if semester is not None:
                    semester_data = doc.get(semester, {})
                    if year is not None:
                        if semester_data.get("year") != year:
                            continue
                else:
                    # If only year is specified, check all semesters
                    if year is not None:
                        found_year = False
                        for key, value in doc.items():
                            if isinstance(value, dict) and value.get("year") == year:
                                found_year = True
                                break
                        if not found_year:
                            continue
            
            # Convert _id (matricule) to string for JSON serialization
            doc["_id"] = str(doc["_id"])
            filtered_docs.append(doc)
        
        # Add computed fields to filtered documents
        # Get all students for rank calculation
        all_students = list(notes_collection.find())
        for s in all_students:
            s["_id"] = str(s["_id"])
        
        for doc in filtered_docs:
            NoteService.add_computed_fields(doc, all_students)
        
        return filtered_docs
    
    @staticmethod
    def get_statistics(
        semester: str = None,
        department: str = None,
        year: str = None
    ) -> Dict[str, Any]:
        """
        Get statistics for filtered students.
        
        Args:
            semester: Semester code (e.g., "S3")
            department: Department name
            year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        
        Returns:
            Dictionary containing statistics
        """
        # Get filtered notes
        notes = NoteService.get_filtered_notes(semester, department, year)
        
        if not notes:
            return {
                "total_students": 0,
                "passed": 0,
                "failed": 0,
                "rattrapage": 0,
                "passed_percentage": 0.0,
                "failed_percentage": 0.0,
                "rattrapage_percentage": 0.0,
                "average_distribution": [],
                "total_average": 0.0
            }
        
        total_students = len(notes)
        passed = 0
        failed = 0
        rattrapage = 0
        total_average_sum = 0.0
        average_count = 0
        
        # توزيع المعدلات لكل رقم من 0 إلى 20
        average_distribution_dict = {str(i): 0 for i in range(21)}  # 0 إلى 20
        
        for note in notes:
            # تحديد البيانات حسب semester
            semester_data = None
            if semester:
                semester_data = note.get(semester, {})
            else:
                # إذا لم يتم تحديد semester، نأخذ أول semester موجود
                for key, value in note.items():
                    if isinstance(value, dict) and "moyenne_generale" in value:
                        semester_data = value
                        break
            
            if not semester_data:
                continue
            
            # الحصول على المعدل العام
            moyenne_generale = semester_data.get("moyenne_generale", 0)
            decision = semester_data.get("decision", "")
            credit_total = semester_data.get("credit_total", 0)
            
            # تحويل المعدل إلى رقم
            try:
                if isinstance(moyenne_generale, str):
                    moyenne_generale = float(moyenne_generale.replace(',', '.'))
                else:
                    moyenne_generale = float(moyenne_generale)
            except:
                moyenne_generale = 0.0
            
            # حساب المعدل في التوزيع (تقريب إلى أقرب رقم صحيح)
            if moyenne_generale >= 0:
                # تقريب المعدل إلى أقرب رقم صحيح
                moyenne_rounded = int(round(moyenne_generale))
                # التأكد من أن المعدل بين 0 و 20
                moyenne_rounded = max(0, min(20, moyenne_rounded))
                
                total_average_sum += moyenne_generale
                average_count += 1
                
                # إضافة إلى التوزيع
                average_distribution_dict[str(moyenne_rounded)] += 1
            
            # تحديد النجاح/الرسوب/الدورة
            decision_upper = str(decision).upper() if decision else ""
            
            # الناجحون: decision يحتوي على "ADMIS" أو المعدل >= 10 و credit_total >= 30
            if "ADMIS" in decision_upper or (moyenne_generale >= 10 and credit_total >= 30):
                passed += 1
            # الدورة: decision يحتوي على "RATTRAPAGE" أو المعدل < 10 و credit_total < 30
            elif "RATTRAPAGE" in decision_upper or (moyenne_generale < 10 and credit_total < 30):
                rattrapage += 1
            # الراسبون: الباقي
            else:
                failed += 1
        
        # حساب النسب المئوية
        passed_percentage = (passed / total_students * 100) if total_students > 0 else 0.0
        failed_percentage = (failed / total_students * 100) if total_students > 0 else 0.0
        rattrapage_percentage = (rattrapage / total_students * 100) if total_students > 0 else 0.0
        total_average = (total_average_sum / average_count) if average_count > 0 else 0.0
        
        # تحويل التوزيع إلى قائمة مع النسب (لكل رقم من 0 إلى 20)
        average_distribution = []
        for i in range(21):  # من 0 إلى 20
            count = average_distribution_dict[str(i)]
            percentage = (count / average_count * 100) if average_count > 0 else 0.0
            average_distribution.append({
                "average": i,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        return {
            "total_students": total_students,
            "passed": passed,
            "failed": failed,
            "rattrapage": rattrapage,
            "passed_percentage": round(passed_percentage, 2),
            "failed_percentage": round(failed_percentage, 2),
            "rattrapage_percentage": round(rattrapage_percentage, 2),
            "average_distribution": average_distribution,
            "total_average": round(total_average, 2)
        }
    
    @staticmethod
    def delete_notes_by_semester_and_year(semester: str, year: str) -> Dict[str, Any]:
        """
        Delete all notes associated with a specific semester and year.
        Removes the semester field from all student documents that have it.
        
        Args:
            semester: Semester code (e.g., "S3")
            year: Year string in format "YYYY-YYYY" (e.g., "2024-2025")
        
        Returns:
            Dictionary with deletion results
        """
        # Find all documents that have this semester with this year
        query = {
            f"{semester}.year": year
        }
        
        # Use $unset to remove the semester field from matching documents
        result = notes_collection.update_many(
            query,
            {
                "$unset": {semester: ""},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "semester": semester,
            "year": year,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    
    @staticmethod
    def update_semester_ispublic(matricule: int, semester: str, is_public: bool) -> Dict[str, Any]:
        """
        Update isPublic field for a specific semester of a student.
        
        Args:
            matricule: Student matricule number
            semester: Semester code (e.g., "S3")
            is_public: Boolean value for isPublic field
        
        Returns:
            Dictionary with operation result
        """
        # Check if student document exists
        student_doc = notes_collection.find_one({"_id": matricule})
        if not student_doc:
            raise ValueError(f"Student with matricule {matricule} not found")
        
        # Check if semester exists
        if semester not in student_doc:
            raise ValueError(f"Semester {semester} not found for student {matricule}")
        
        # Update isPublic field using dot notation
        result = notes_collection.update_one(
            {"_id": matricule},
            {
                "$set": {
                    f"{semester}.isPublic": is_public,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Failed to update semester {semester} for student {matricule}")
        
        return {
            "matricule": matricule,
            "semester": semester,
            "isPublic": is_public,
            "updated": result.modified_count > 0
        }
    
    @staticmethod
    def update_ispublic_globale(matricule: int, is_public_globale: bool) -> Dict[str, Any]:
        """
        Update isPublicGlobale field for a student.
        
        Args:
            matricule: Student matricule number
            is_public_globale: Boolean value for isPublicGlobale field
        
        Returns:
            Dictionary with operation result
        """
        # Check if student document exists
        student_doc = notes_collection.find_one({"_id": matricule})
        if not student_doc:
            raise ValueError(f"Student with matricule {matricule} not found")
        
        # Update isPublicGlobale field
        result = notes_collection.update_one(
            {"_id": matricule},
            {
                "$set": {
                    "isPublicGlobale": is_public_globale,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Failed to update isPublicGlobale for student {matricule}")
        
        return {
            "matricule": matricule,
            "isPublicGlobale": is_public_globale,
            "updated": result.modified_count > 0
        }

