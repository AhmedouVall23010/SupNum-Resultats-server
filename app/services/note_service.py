from typing import Dict, Any, List
from app.db.mongo import notes_collection
from datetime import datetime


class NoteService:
    @staticmethod
    def save_student_notes(student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save or update student notes in MongoDB.
        Uses matricule as the _id (unique identifier) for upsert operation.
        
        Args:
            student_data: Dictionary containing student data with 'matricule' key
        
        Returns:
            Dictionary with operation result
        """
        if "matricule" not in student_data:
            raise ValueError("student_data must contain 'matricule' key")
        
        matricule = student_data["matricule"]
        
        # Check if document exists to preserve created_at
        existing = notes_collection.find_one({"_id": matricule})
        
        # Prepare document with _id as matricule and updated_at timestamp
        document = {
            "_id": matricule,  # Use matricule as _id
            **student_data,
            "updated_at": datetime.utcnow()
        }
        
        # Preserve created_at if document exists, otherwise set it now
        if existing:
            document["created_at"] = existing.get("created_at", datetime.utcnow())
        else:
            document["created_at"] = datetime.utcnow()
        
        # Replace document (upsert: create if not exists, replace if exists)
        # Using replace_one instead of update_one because we need to set _id
        result = notes_collection.replace_one(
            {"_id": matricule},
            document,
            upsert=True
        )
        
        return {
            "matricule": matricule,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            "operation": "updated" if result.matched_count > 0 else "created"
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
    def get_student_notes(matricule: int) -> Dict[str, Any]:
        """
        Get student notes by matricule.
        
        Args:
            matricule: Student matricule number (used as _id)
        
        Returns:
            Student notes document or None if not found
        """
        document = notes_collection.find_one({"_id": matricule})
        if document:
            # Convert _id (matricule) to string for JSON serialization
            document["_id"] = str(document["_id"])
        return document
    
    @staticmethod
    def get_all_notes() -> List[Dict[str, Any]]:
        """
        Get all student notes.
        
        Returns:
            List of all student notes documents
        """
        documents = list(notes_collection.find())
        for doc in documents:
            # Convert _id (matricule) to string for JSON serialization
            doc["_id"] = str(doc["_id"])
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

