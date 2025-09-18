from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database.database import db_manager
from app.utils.helpers import convert_uuids_to_strings
import logging

logger = logging.getLogger(__name__)


class ClassService:
    """Service for class operations using PostgreSQL"""
    
    def __init__(self):
        pass
    

    async def create_class(self, class_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new class"""
        try:
            import uuid
            
            # Extract student_ids before inserting class data
            student_ids = class_data.pop('student_ids', [])
            
            # Generate UUID for the class
            class_id = str(uuid.uuid4())
            
            # Insert class
            query = """
                INSERT INTO classes (id, class_code, subject, teacher_id, duration, grade, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """
            
            current_time = datetime.utcnow()
            
            result = await db_manager.execute_insert_with_returning(
                query,
                class_id,
                class_data.get('class_code'),
                class_data.get('subject'),
                class_data.get('teacher_id'),
                class_data.get('duration'),
                class_data.get('grade'),
                current_time,
                current_time
            )
            
            if result:
                created_raw = dict(result[0])
                
                # Convert UUID fields to strings for JSON serialization
                created_raw = convert_uuids_to_strings(created_raw)
                
                class_id = created_raw['id']
                
                # Enroll students if any were provided
                if student_ids:
                    await self._enroll_students(class_id, student_ids)
                
                # Fetch full class with teacher info and students
                full_class = await self.get_class(class_id)
                logger.info(f"Successfully created class: {class_id}")
                return full_class if full_class else created_raw
            else:
                logger.error("Failed to create class")
                return None
                
        except Exception as e:
            logger.error(f"Error creating class: {str(e)}")
            return None

    async def _enroll_students(self, class_id: str, student_ids: List[str]) -> bool:
        """Enroll students in a class using the class_students junction table"""
        try:
            if not student_ids:
                return True
                
            # Prepare enrollment data
            for student_id in student_ids:
                query = """
                    INSERT INTO class_students (class_id, student_id)
                    VALUES ($1, $2)
                    ON CONFLICT (class_id, student_id) DO NOTHING
                """
                await db_manager.execute_command(
                    query, 
                    class_id, 
                    student_id
                )
            
            logger.info(f"Successfully enrolled {len(student_ids)} students in class {class_id}")
            return True
                
        except Exception as e:
            logger.warning(f"Student enrollment failed for class {class_id}: {str(e)}")
            return False

    async def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """Add a single student to a class."""
        try:
            query = """
                INSERT INTO class_students (class_id, student_id)
                VALUES ($1, $2)
                ON CONFLICT (class_id, student_id) DO NOTHING
            """
            result = await db_manager.execute_command(query, class_id, student_id)
            return result is not None
        except Exception as e:
            logger.error(f"Error adding student {student_id} to class {class_id}: {str(e)}")
            return False

    async def remove_student_from_class(self, class_id: str, student_id: str) -> bool:
        """Remove a single student from a class."""
        try:
            query = "DELETE FROM class_students WHERE class_id = $1 AND student_id = $2"
            result = await db_manager.execute_command(query, class_id, student_id)
            return result is not None
        except Exception as e:
            logger.error(f"Error removing student {student_id} from class {class_id}: {str(e)}")
            return False

    async def is_student_enrolled(self, class_id: str, student_id: str) -> bool:
        """Check if a student is enrolled in a class."""
        try:
            query = "SELECT 1 FROM class_students WHERE class_id = $1 AND student_id = $2 LIMIT 1"
            result = await db_manager.execute_query(query, class_id, student_id)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking enrollment for student {student_id} in class {class_id}: {str(e)}")
            return False

    async def list_class_students(self, class_id: str) -> List[Dict[str, Any]]:
        """List students enrolled in a class."""
        try:
            query = """
                SELECT u.id, u.username, u.full_name, u.email
                FROM class_students cs
                JOIN users u ON cs.student_id = u.id
                WHERE cs.class_id = $1
                ORDER BY u.full_name ASC
            """
            result = await db_manager.execute_query(query, class_id)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error listing students for class {class_id}: {str(e)}")
            return []

    async def _update_student_enrollments(self, class_id: str, new_student_ids: List[str]) -> bool:
        """Update student enrollments for a class"""
        try:
            # Remove all existing enrollments
            await db_manager.execute_command(
                "DELETE FROM class_students WHERE class_id = $1", 
                class_id
            )
            
            # Add new enrollments
            if new_student_ids:
                await self._enroll_students(class_id, new_student_ids)
            
            logger.info(f"Successfully updated student enrollments for class {class_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating student enrollments for class {class_id}: {str(e)}")
            return False

    async def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        """Get a class by ID"""
        try:
            # Get class details
            query = """
                SELECT c.*, u.full_name as teacher_name, u.email as teacher_email
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                WHERE c.id = $1
            """
            
            result = await db_manager.execute_query(query, class_id)
            
            if result:
                class_data = dict(result[0])
                
                # Fetch enrolled students
                students_query = """
                    SELECT u.id, u.username, u.full_name, u.email
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = $1
                """
                students_result = await db_manager.execute_query(students_query, class_id)
                
                if students_result:
                    # Return only list of student IDs as strings to match schema
                    class_data['students'] = [str(student.get('id')) for student in students_result if student.get('id') is not None]
                else:
                    class_data['students'] = []
                
                # Convert UUID fields to strings for JSON serialization
                class_data = convert_uuids_to_strings(class_data)
                
                # Ensure teacher_id is explicitly converted to string
                if 'teacher_id' in class_data and class_data['teacher_id'] is not None:
                    class_data['teacher_id'] = str(class_data['teacher_id'])
                
                return class_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting class {class_id}: {str(e)}")
            return None

    async def get_classes(
        self, 
        teacher_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get classes with optional filters"""
        try:
            # Build base query
            base_query = """
                SELECT c.*, u.full_name as teacher_name, u.email as teacher_email
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
            """
            
            where_conditions = []
            params = []
            param_count = 1
            
            if teacher_id:
                where_conditions.append(f"c.teacher_id = ${param_count}")
                params.append(teacher_id)
                param_count += 1
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            # Add LIMIT/OFFSET with correct parameter placeholders
            limit_placeholder = f"${param_count}"
            offset_placeholder = f"${param_count + 1}"
            base_query += f" ORDER BY c.created_at DESC LIMIT {limit_placeholder} OFFSET {offset_placeholder}"
            params.extend([limit, offset])
            
            result = await db_manager.execute_query(base_query, *params)
            classes = [dict(row) for row in result] if result else []
            
            # Fetch students for each class
            for class_data in classes:
                students_query = """
                    SELECT u.id, u.username, u.full_name, u.email
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = $1
                """
                students_result = await db_manager.execute_query(students_query, class_data['id'])
                
                if students_result:
                    class_data['students'] = [str(student.get('id')) for student in students_result if student.get('id') is not None]
                else:
                    class_data['students'] = []
                
                # Convert UUID fields to strings for JSON serialization
                convert_uuids_to_strings(class_data)
            
            return classes
            
        except Exception as e:
            logger.error(f"Error getting classes: {str(e)}")
            return []

    async def get_classes_for_student(
        self,
        student_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get classes that a specific student is enrolled in."""
        try:
            query = """
                SELECT c.*, u.full_name as teacher_name, u.email as teacher_email
                FROM class_students cs
                JOIN classes c ON cs.class_id = c.id
                JOIN users u ON c.teacher_id = u.id
                WHERE cs.student_id = $1
                ORDER BY c.created_at DESC
                LIMIT $2 OFFSET $3
            """
            result = await db_manager.execute_query(query, student_id, limit, offset)
            classes = [dict(row) for row in result] if result else []

            # Attach enrolled students (as IDs) for each class for consistency
            for class_data in classes:
                students_query = """
                    SELECT u.id, u.username, u.full_name, u.email
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = $1
                """
                students_result = await db_manager.execute_query(students_query, class_data['id'])
                if students_result:
                    class_data['students'] = [str(student.get('id')) for student in students_result if student.get('id') is not None]
                else:
                    class_data['students'] = []
                convert_uuids_to_strings(class_data)

            return classes
        except Exception as e:
            logger.error(f"Error getting classes for student {student_id}: {str(e)}")
            return []

    async def update_class(self, class_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a class"""
        try:
            # Extract student_ids before updating class data
            student_ids = update_data.pop('student_ids', None)
            
            # Remove None values
            clean_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not clean_data:
                return await self.get_class(class_id)
            
            # Build update query dynamically
            set_clauses = []
            values = []
            param_count = 1
            
            for key, value in clean_data.items():
                if key in ['class_code', 'subject', 'duration', 'grade']:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            set_clauses.append("updated_at = $" + str(param_count))
            values.append(datetime.utcnow())
            values.append(class_id)
            
            query = f"""
                UPDATE classes 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count + 1}
                RETURNING *
            """
            
            result = await db_manager.execute_insert_with_returning(query, *values)
            
            if result:
                # Update student enrollments if student_ids were provided
                if student_ids is not None:
                    await self._update_student_enrollments(class_id, student_ids)
                
                logger.info(f"Successfully updated class: {class_id}")
                # Return full class with teacher info and students
                full_class = await self.get_class(class_id)
                return full_class if full_class else convert_uuids_to_strings(dict(result[0]))
            else:
                logger.error(f"Failed to update class {class_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating class {class_id}: {str(e)}")
            return None

    async def delete_class(self, class_id: str) -> bool:
        """Delete a class"""
        try:
            # Delete student enrollments first
            await db_manager.execute_command(
                "DELETE FROM class_students WHERE class_id = $1", 
                class_id
            )
            
            # Delete the class
            result = await db_manager.execute_command(
                "DELETE FROM classes WHERE id = $1", 
                class_id
            )
            
            if result:
                logger.info(f"Successfully deleted class: {class_id}")
                return True
            else:
                logger.error(f"Failed to delete class {class_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting class {class_id}: {str(e)}")
            return False

    async def get_classes_by_teacher(self, teacher_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all classes for a specific teacher"""
        try:
            query = """
                SELECT c.*, u.full_name as teacher_name, u.email as teacher_email
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                WHERE c.teacher_id = $1
                ORDER BY c.created_at DESC
                LIMIT $2
            """
            
            result = await db_manager.execute_query(query, teacher_id, limit)
            classes = [dict(row) for row in result] if result else []
            
            # Fetch students for each class
            for class_data in classes:
                students_query = """
                    SELECT u.id, u.username, u.full_name, u.email
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = $1
                """
                students_result = await db_manager.execute_query(students_query, class_data['id'])
                
                if students_result:
                    class_data['students'] = [str(student.get('id')) for student in students_result if student.get('id') is not None]
                else:
                    class_data['students'] = []
                
                # Convert UUID fields to strings for JSON serialization
                convert_uuids_to_strings(class_data)
            
            return classes
            
        except Exception as e:
            logger.error(f"Error getting classes for teacher {teacher_id}: {str(e)}")
            return []


    async def search_classes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search classes by class_code or subject"""
        try:
            search_query = """
                SELECT c.*, u.full_name as teacher_name, u.email as teacher_email
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                WHERE c.class_code ILIKE $1 OR c.subject ILIKE $1
                ORDER BY c.created_at DESC
                LIMIT $2
            """
            
            search_pattern = f"%{query}%"
            result = await db_manager.execute_query(search_query, search_pattern, limit)
            classes = [dict(row) for row in result] if result else []
            
            # Fetch students for each class
            for class_data in classes:
                students_query = """
                    SELECT u.id, u.username, u.full_name, u.email
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = $1
                """
                students_result = await db_manager.execute_query(students_query, class_data['id'])
                
                if students_result:
                    class_data['students'] = [str(student.get('id')) for student in students_result if student.get('id') is not None]
                else:
                    class_data['students'] = []
                
                # Convert UUID fields to strings for JSON serialization
                convert_uuids_to_strings(class_data)
            
            return classes
            
        except Exception as e:
            logger.error(f"Error searching classes: {str(e)}")
            return []


# Global class service instance
class_service = ClassService()
