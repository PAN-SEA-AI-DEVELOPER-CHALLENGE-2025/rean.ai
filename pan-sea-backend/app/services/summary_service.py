from typing import List, Optional, Dict, Any
from app.core.llm import LLMService
from app.database.database import db_manager
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for class summary operations using PostgreSQL"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def get_summary(self, summary_id: str) -> Optional[Dict[str, Any]]:
        """Get summary by ID"""
        try:
            query = """
                SELECT cs.*, c.class_code as class_title, c.subject as class_subject,
                       u.full_name as teacher_name
                FROM lesson_summaries cs
                JOIN classes c ON cs.class_id::uuid = c.id
                JOIN users u ON c.teacher_id = u.id
                WHERE cs.id = $1
            """
            
            result = await db_manager.execute_query(query, summary_id)
            
            if result:
                summary = dict(result[0])
                # Parse JSON fields
                summary["topics_discussed"] = json.loads(summary.get("topics_discussed", "[]"))
                summary["learning_objectives"] = json.loads(summary.get("learning_objectives", "[]"))
                summary["homework"] = json.loads(summary.get("homework", "[]"))
                summary["announcements"] = json.loads(summary.get("announcements", "[]"))
                summary["key_points"] = json.loads(summary.get("key_points", "[]"))
                summary["study_questions"] = json.loads(summary.get("study_questions", "[]"))
                
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return None
    
    async def get_summaries(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all summaries with pagination"""
        try:
            query = """
                SELECT cs.*, c.class_code as class_title, c.subject as class_subject,
                       u.full_name as teacher_name
                FROM lesson_summaries cs
                JOIN classes c ON cs.class_id::uuid = c.id
                JOIN users u ON c.teacher_id = u.id
                ORDER BY cs.created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            result = await db_manager.execute_query(query, limit, skip)
            summaries = [dict(row) for row in result] if result else []
            
            # Parse JSON fields for each summary
            for summary in summaries:
                summary["topics_discussed"] = json.loads(summary.get("topics_discussed", "[]"))
                summary["learning_objectives"] = json.loads(summary.get("learning_objectives", "[]"))
                summary["homework"] = json.loads(summary.get("homework", "[]"))
                summary["announcements"] = json.loads(summary.get("announcements", "[]"))
                summary["key_points"] = json.loads(summary.get("key_points", "[]"))
                summary["study_questions"] = json.loads(summary.get("study_questions", "[]"))
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting summaries: {str(e)}")
            return []
    
    async def get_class_summaries(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get summaries for a specific class"""
        try:
            query = """
                SELECT cs.*, c.class_code as class_title, c.subject as class_subject,
                       u.full_name as teacher_name
                FROM lesson_summaries cs
                JOIN classes c ON cs.class_id::uuid = c.id
                JOIN users u ON c.teacher_id = u.id
                WHERE cs.class_id = $1
                ORDER BY cs.created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            result = await db_manager.execute_query(query, class_id, limit, skip)
            summaries = [dict(row) for row in result] if result else []
            
            # Parse JSON fields for each summary
            for summary in summaries:
                summary["topics_discussed"] = json.loads(summary.get("topics_discussed", "[]"))
                summary["learning_objectives"] = json.loads(summary.get("learning_objectives", "[]"))
                summary["homework"] = json.loads(summary.get("homework", "[]"))
                summary["announcements"] = json.loads(summary.get("announcements", "[]"))
                summary["key_points"] = json.loads(summary.get("key_points", "[]"))
                summary["study_questions"] = json.loads(summary.get("study_questions", "[]"))
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting class summaries: {str(e)}")
            return []
    
    async def get_lesson_summaries(self, lesson_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get summaries for a specific lesson"""
        try:
            query = """
                SELECT cs.*, c.class_code as class_title, c.subject as class_subject,
                       u.full_name as teacher_name, l.lecture_title as lesson_title
                FROM lesson_summaries cs
                JOIN classes c ON cs.class_id::uuid = c.id
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN lessons l ON cs.lesson_id = l.id
                WHERE cs.lesson_id = CAST($1 AS uuid)
                ORDER BY cs.created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            result = await db_manager.execute_query(query, lesson_id, limit, skip)
            summaries = [dict(row) for row in result] if result else []
            
            # Parse JSON fields for each summary
            for summary in summaries:
                summary["topics_discussed"] = json.loads(summary.get("topics_discussed", "[]"))
                summary["learning_objectives"] = json.loads(summary.get("learning_objectives", "[]"))
                summary["homework"] = json.loads(summary.get("homework", "[]"))
                summary["announcements"] = json.loads(summary.get("announcements", "[]"))
                summary["key_points"] = json.loads(summary.get("key_points", "[]"))
                summary["study_questions"] = json.loads(summary.get("study_questions", "[]"))
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting lesson summaries: {str(e)}")
            return []
    
    async def get_lesson_summary(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent summary for a specific lesson"""
        try:
            query = """
                SELECT cs.*, c.class_code as class_title, c.subject as class_subject,
                       u.full_name as teacher_name, l.lecture_title as lesson_title
                FROM lesson_summaries cs
                JOIN classes c ON cs.class_id::uuid = c.id
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN lessons l ON cs.lesson_id = l.id
                WHERE cs.lesson_id = CAST($1 AS uuid)
                ORDER BY cs.created_at DESC
                LIMIT 1
            """
            
            result = await db_manager.execute_query(query, lesson_id)
            
            if result:
                summary = dict(result[0])
                # Parse JSON fields
                summary["topics_discussed"] = json.loads(summary.get("topics_discussed", "[]"))
                summary["learning_objectives"] = json.loads(summary.get("learning_objectives", "[]"))
                summary["homework"] = json.loads(summary.get("homework", "[]"))
                summary["announcements"] = json.loads(summary.get("announcements", "[]"))
                summary["key_points"] = json.loads(summary.get("key_points", "[]"))
                summary["study_questions"] = json.loads(summary.get("study_questions", "[]"))
                
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting lesson summary: {str(e)}")
            return None
    
    async def delete_summary(self, summary_id: str) -> bool:
        """Delete summary"""
        try:
            query = "DELETE FROM lesson_summaries WHERE id = $1"
            result = await db_manager.execute_command(query, summary_id)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error deleting summary: {str(e)}")
            return False
    
    async def create_summary(self, summary_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new summary in the database"""
        try:
            import uuid
            
            # Convert lists to JSON strings for JSONB fields
            data_to_insert = {
                "id": str(uuid.uuid4()),
                "class_id": summary_data.get("class_id"),
                "lesson_id": summary_data.get("lesson_id"),
                "lecture_title": summary_data.get("lecture_title", "Lecture Summary"),
                "summary": summary_data.get("summary", ""),
                "topics_discussed": json.dumps(summary_data.get("topics_discussed", [])),
                "learning_objectives": json.dumps(summary_data.get("learning_objectives", [])),
                "homework": json.dumps(summary_data.get("homework", [])),
                "announcements": json.dumps(summary_data.get("announcements", [])),
                "duration": summary_data.get("duration", 0),
                "next_class_preview": summary_data.get("next_class_preview")
            }
            
            # Handle optional fields that might not exist in current database
            if "key_points" in summary_data:
                data_to_insert["key_points"] = json.dumps(summary_data.get("key_points", []))
            if "study_questions" in summary_data:
                data_to_insert["study_questions"] = json.dumps(summary_data.get("study_questions", []))
            
            # Build dynamic query based on available fields
            fields = list(data_to_insert.keys())
            placeholders = [f"${i+1}" for i in range(len(fields))]
            
            query = f"""
                INSERT INTO lesson_summaries (
                    {', '.join(fields)}
                ) VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            result = await db_manager.execute_insert_with_returning(
                query,
                *[data_to_insert[field] for field in fields]
            )
            
            if result and len(result) > 0:
                created_summary = dict(result[0])
                # Parse JSON fields back for response with safe handling
                created_summary["topics_discussed"] = json.loads(created_summary.get("topics_discussed") or "[]")
                created_summary["learning_objectives"] = json.loads(created_summary.get("learning_objectives") or "[]")
                created_summary["homework"] = json.loads(created_summary.get("homework") or "[]")
                created_summary["announcements"] = json.loads(created_summary.get("announcements") or "[]")
                # Handle optional fields
                if created_summary.get("key_points"):
                    created_summary["key_points"] = json.loads(created_summary.get("key_points"))
                else:
                    created_summary["key_points"] = []
                if created_summary.get("study_questions"):
                    created_summary["study_questions"] = json.loads(created_summary.get("study_questions"))
                else:
                    created_summary["study_questions"] = []
                return created_summary
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            return None
    
    async def update_summary(self, summary_id: str, summary_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing summary"""
        try:
            # Convert lists to JSON strings for JSONB fields
            data_to_update = {
                "lecture_title": summary_data.get("lecture_title"),
                "lesson_id": summary_data.get("lesson_id"),
                "summary": summary_data.get("summary", ""),
                "topics_discussed": json.dumps(summary_data.get("topics_discussed", [])),
                "learning_objectives": json.dumps(summary_data.get("learning_objectives", [])),
                "homework": json.dumps(summary_data.get("homework", [])),
                "announcements": json.dumps(summary_data.get("announcements", [])),
                "duration": summary_data.get("duration", 0),
                "next_class_preview": summary_data.get("next_class_preview")
            }
            
            # Handle optional fields that might not exist in current database
            if "key_points" in summary_data:
                data_to_update["key_points"] = json.dumps(summary_data.get("key_points", []))
            if "study_questions" in summary_data:
                data_to_update["study_questions"] = json.dumps(summary_data.get("study_questions", []))
            
            # Build dynamic update query based on available fields
            set_clauses = []
            values = []
            param_count = 1
            
            for key, value in data_to_update.items():
                if value is not None:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            # Add updated_at and summary_id
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            values.append(summary_id)
            
            if not set_clauses:
                return await self.get_summary(summary_id)
            
            query = f"""
                UPDATE lesson_summaries 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
                RETURNING *
            """
            
            result = await db_manager.execute_insert_with_returning(query, *values)
            
            if result and len(result) > 0:
                updated_summary = dict(result[0])
                # Parse JSON fields back for response
                updated_summary["topics_discussed"] = json.loads(updated_summary.get("topics_discussed", "[]"))
                updated_summary["learning_objectives"] = json.loads(updated_summary.get("learning_objectives", "[]"))
                updated_summary["homework"] = json.loads(updated_summary.get("homework", "[]"))
                updated_summary["announcements"] = json.loads(updated_summary.get("announcements", "[]"))
                # Handle optional fields
                if "key_points" in updated_summary:
                    updated_summary["key_points"] = json.loads(updated_summary.get("key_points", "[]"))
                else:
                    updated_summary["key_points"] = []
                if "study_questions" in updated_summary:
                    updated_summary["study_questions"] = json.loads(updated_summary.get("study_questions", "[]"))
                else:
                    updated_summary["study_questions"] = []
                return updated_summary
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating summary: {str(e)}")
            return None
    
    async def summary_service(
        self, 
        transcription: str,
        class_id: Optional[str] = None,
        save_to_db: bool = True,
        subject: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate summary from provided transcription text (optionally save to database)"""
        try:
            # Get subject from class if class_id provided and subject not specified
            if class_id and not subject:
                query = "SELECT subject FROM classes WHERE id = $1"
                result = await db_manager.execute_query(query, class_id)
                if result and len(result) > 0:
                    subject = result[0]["subject"]
            
            # Generate summary using LLM
            summary_data = await self.llm_service.generate_class_summary(
                transcription=transcription, 
                subject=subject
            )

            key_points_response = await self.llm_service.extract_key_points(
                transcription=transcription,
                subject=subject
            )

            # Backfill missing fields from key_points_response when summary omitted them
            try:
                fields_to_backfill = [
                    "topics_discussed",
                    "learning_objectives",
                    "homework",
                    "announcements",
                ]
                for field_name in fields_to_backfill:
                    if not summary_data.get(field_name):
                        summary_data[field_name] = (
                            (key_points_response or {}).get(field_name, []) or []
                        )

                if (
                    not summary_data.get("next_class_preview")
                    and (key_points_response or {}).get("next_class_preview") is not None
                ):
                    summary_data["next_class_preview"] = key_points_response.get("next_class_preview")
            except Exception:
                # Non-fatal: if any unexpected structure occurs, continue with available data
                pass

            # Ensure default messages when no homework or announcements are present
            if not summary_data.get("homework"):
                summary_data["homework"] = ["There's no homework in this lesson."]
            if not summary_data.get("announcements"):
                summary_data["announcements"] = ["There's no announcement in this lesson."]

            generate_study_questions = await self.llm_service.generate_study_questions(
                summary=summary_data.get("summary", ""),
                subject=subject
            )

            result = {
                "summary": summary_data.get("summary", ""),
                "topics_discussed": summary_data.get("topics_discussed", []),
                "learning_objectives": summary_data.get("learning_objectives", []),
                "homework": summary_data.get("homework", []),
                "announcements": summary_data.get("announcements", []),
                "next_class_preview": summary_data.get("next_class_preview"),
                "key_points": key_points_response.get("key_points", []) if key_points_response else [],
                "study_questions": generate_study_questions or [],
                "duration": summary_data.get("duration", 0),  # Add duration field with default value
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save to database if requested
            if save_to_db:
                if not class_id:
                    logger.error("class_id is required when saving to database")
                    raise ValueError("class_id is required when saving to database")
                
                # Prepare data for database insertion
                save_data = {
                    "class_id": class_id,
                    **result
                }
                
                # Remove the created_at field since database will auto-generate it
                save_data.pop("created_at", None)
                
                # Save to database
                saved_summary = await self.create_summary(save_data)
                if saved_summary:
                    logger.info(f"Successfully saved summary for class {class_id}")
                    return saved_summary
                else:
                    logger.error("Failed to save summary to database")
                    return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating summary from text: {str(e)}")
            return None


# Global summary service instance
summary_service = SummaryService()
