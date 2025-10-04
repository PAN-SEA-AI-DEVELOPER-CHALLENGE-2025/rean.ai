from typing import List, Optional, Dict, Any
from app.database.database import db_manager
from app.core.s3 import s3_service
from app.utils.helpers import sanitize_s3_metadata
from app.utils.helpers import sanitize_filename
import logging
import os
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class LessonService:
    """Service for lesson operations using PostgreSQL and AWS S3"""
    
    def __init__(self):
        pass

    async def upload_audio_file(
        self, 
        file_path: str,
        class_id: str, 
        lecture_title: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Upload an audio file to S3 and store metadata in database"""
        try:
            # Generate unique S3 key for the audio file
            file_extension = os.path.splitext(file_path)[1]
            s3_key = f"audio/{class_id}/{uuid.uuid4()}{file_extension}"
            
            # Prepare metadata and sanitize for S3 (S3 only supports ASCII characters in metadata)
            metadata = {
                "class_id": class_id,
                "lecture_title": lecture_title,
                "original_filename": os.path.basename(file_path),
                "upload_timestamp": datetime.utcnow().isoformat()
            }
            sanitized_metadata = sanitize_s3_metadata(metadata)
            
            # Upload audio file to S3
            upload_success = await s3_service.upload_file(
                file_path=file_path,
                s3_key=s3_key,
                content_type="audio/mpeg" if file_extension == ".mp3" else "audio/wav",
                metadata=sanitized_metadata
            )
            
            if not upload_success:
                logger.error(f"Failed to upload audio file to S3: {file_path}")
                return None
            
            # Generate UUID for the audio record
            audio_id = str(uuid.uuid4())
            
            # Insert into audio table with S3 reference
            query = """
                INSERT INTO lessons (id, class_id, lecture_title, s3_key, s3_url, file_size, file_extension, upload_timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            
            result = await db_manager.execute_insert_with_returning(
                query,
                audio_id,
                class_id,
                lecture_title,
                s3_key,
                s3_service.get_file_url(s3_key),
                os.path.getsize(file_path),
                file_extension,
                datetime.utcnow()
            )
            
            if result:
                audio_id = result[0]['id']
                logger.info(f"Successfully uploaded audio file for class {class_id}")
                return {
                    "audio_id": audio_id,
                    "class_id": class_id,
                    "lecture_title": lecture_title,
                    "s3_key": s3_key,
                    "s3_url": s3_service.get_file_url(s3_key),
                    "file_size": os.path.getsize(file_path),
                    "file_extension": file_extension,
                    "message": "Lesson file uploaded successfully to S3"
                }
            else:
                logger.error(f"Failed to save audio file metadata")
                return None

        except Exception as e:
            logger.error(f"Error uploading audio file: {str(e)}")
            return None
    async def upload_material_files(
        self,
        file_paths: List[str],
        file_names: List[str],
        class_id: str,
        lesson_id: str,
        extracted_texts: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Upload lesson materials to S3 and store metadata in database"""
        results: List[Dict[str, Any]] = []
        try:
            for idx, path in enumerate(file_paths or []):
                try:
                    original_name = (file_names[idx] if idx < len(file_names) else None) or os.path.basename(path)
                    safe_name = sanitize_filename(original_name)
                    ext = os.path.splitext(path)[1].lower()
                    s3_key = f"materials/{class_id}/{lesson_id}/{uuid.uuid4()}{ext}"

                    metadata = sanitize_s3_metadata({
                        "class_id": class_id,
                        "lesson_id": str(lesson_id),
                        "original_filename": safe_name,
                    })

                    # Guess a minimal content type based on extension
                    content_type = None
                    if ext == ".pdf":
                        content_type = "application/pdf"
                    elif ext == ".pptx":
                        content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    elif ext == ".docx":
                        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    elif ext == ".txt":
                        content_type = "text/plain"

                    uploaded = await s3_service.upload_file(
                        file_path=path,
                        s3_key=s3_key,
                        content_type=content_type,
                        metadata=metadata,
                    )
                    if not uploaded:
                        results.append({"success": False, "error": "upload_failed", "filename": safe_name})
                        continue

                    insert_q = (
                        """
                        INSERT INTO lesson_materials (
                            id, lesson_id, class_id, filename, s3_key, s3_url, file_size, file_extension, content_type, extracted_text
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                        ) RETURNING *
                        """
                    )
                    mat_id = str(uuid.uuid4())
                    file_size = os.path.getsize(path)
                    row = await db_manager.execute_insert_with_returning(
                        insert_q,
                        mat_id,
                        str(lesson_id),
                        class_id,
                        safe_name,
                        s3_key,
                        s3_service.get_file_url(s3_key),
                        file_size,
                        ext,
                        content_type,
                        (extracted_texts[idx] if extracted_texts and idx < len(extracted_texts) else None),
                    )
                    if row:
                        results.append({"success": True, "material": dict(row[0])})
                    else:
                        results.append({"success": False, "error": "db_insert_failed", "filename": safe_name})
                except Exception as e:
                    logger.error(f"Error uploading material {path}: {str(e)}")
                    results.append({"success": False, "error": str(e)})
            return results
        except Exception as e:
            logger.error(f"Error uploading materials: {str(e)}")
            return results

    async def get_audio_recordings_by_class(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all lessons for a specific class with pagination"""
        try:
            query = "SELECT * FROM lessons WHERE class_id = $1 ORDER BY upload_timestamp DESC LIMIT $2 OFFSET $3"
            result = await db_manager.execute_query(query, class_id, limit, skip)
            
            if result:
                # Convert to list of dictionaries
                recordings = []
                for row in result:
                    recording = dict(row)
                    if recording.get("s3_key"):
                        recording["s3_url"] = s3_service.get_file_url(recording["s3_key"])
                    recordings.append(recording)
                return recordings
            return []
            
        except Exception as e:
            logger.error(f"Error getting lessons for class {class_id}: {str(e)}")
            return []

    async def get_lessons_count_by_class(self, class_id: str) -> int:
        """Get the count of lessons for a specific class"""
        try:
            query = "SELECT COUNT(*) as count FROM lessons WHERE class_id = $1"
            result = await db_manager.execute_query(query, class_id)
            
            if result:
                return result[0]["count"]
            return 0
            
        except Exception as e:
            logger.error(f"Error getting lessons count for class {class_id}: {str(e)}")
            return 0
    
    async def delete_audio_recording(self, audio_id: str) -> bool:
        """Delete an audio recording from both database and S3"""
        try:
            # Get the S3 key before deleting from database
            result = await db_manager.execute_query("SELECT s3_key FROM lessons WHERE id = $1", audio_id)
            
            if result and result[0].get("s3_key"):
                s3_key = result[0]["s3_key"]
                
                # Delete from S3
                s3_delete_success = await s3_service.delete_file(s3_key)
                if not s3_delete_success:
                    logger.warning(f"Failed to delete file from S3: {s3_key}")
            
            # Delete lesson summaries first (they have foreign key constraint to lessons)
            try:
                await db_manager.execute_command(
                    "DELETE FROM lesson_summaries WHERE lesson_id = $1", 
                    audio_id
                )
                logger.info(f"Successfully deleted lesson summaries for audio {audio_id}")
            except Exception as e:
                logger.warning(f"Failed to delete lesson summaries for audio {audio_id}: {str(e)}")
            
            # Delete from database
            delete_result = await db_manager.execute_command("DELETE FROM lessons WHERE id = $1", audio_id)
            
            if delete_result:
                logger.info(f"Successfully deleted audio recording {audio_id}")
                return True
            else:
                logger.error(f"Failed to delete audio recording from database: {audio_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting audio recording {audio_id}: {str(e)}")
            return False
    
    async def download_audio_file(self, audio_id: str, local_path: str) -> bool:
        """Download an audio file from S3 to local storage"""
        try:
            # Get the S3 key from database
            result = await db_manager.execute_query("SELECT s3_key FROM lessons WHERE id = $1", audio_id)
            
            if not result or not result[0].get("s3_key"):
                logger.error(f"Lesson recording {audio_id} not found or missing S3 key")
                return False
            
            s3_key = result[0]["s3_key"]
            
            # Download from S3
            download_success = await s3_service.download_file(s3_key, local_path)
            
            if download_success:
                logger.info(f"Successfully downloaded audio file {audio_id} to {local_path}")
                return True
            else:
                logger.error(f"Failed to download audio file {audio_id} from S3")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading audio file {audio_id}: {str(e)}")
            return False
    
    async def get_audio_file_url(self, audio_id: str, expires_in: int = 3600) -> Optional[str]:
        """Get a presigned URL for an audio file"""
        try:
            # Get the S3 key from database
            result = await db_manager.execute_query("SELECT s3_key FROM lessons WHERE id = $1", audio_id)
            
            if not result or not result[0].get("s3_key"):
                logger.error(f"Lesson recording {audio_id} not found or missing S3 key")
                return None
            
            s3_key = result[0]["s3_key"]
            
            # Generate presigned URL
            url = s3_service.get_file_url(s3_key, expires_in)
            
            if url:
                logger.info(f"Generated presigned URL for audio file {audio_id}")
                return url
            else:
                logger.error(f"Failed to generate presigned URL for audio file {audio_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting audio file URL for {audio_id}: {str(e)}")
            return None

    async def get_audio_recording(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audio recording by ID"""
        try:
            query = "SELECT * FROM lessons WHERE id = $1"
            result = await db_manager.execute_query(query, audio_id)
            
            if result:
                recording = dict(result[0])
                if recording.get("s3_key"):
                    recording["s3_url"] = s3_service.get_file_url(recording["s3_key"])
                return recording
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio recording {audio_id}: {str(e)}")
            return None

    async def update_transcription(self, audio_id: str, transcription: str) -> Optional[Dict[str, Any]]:
        """Update the transcription for an audio recording and generate embeddings"""
        try:
            # First update the transcription
            query = """
                UPDATE lessons 
                SET transcription = $2, updated_at = $3
                WHERE id = $1
                RETURNING *
            """
            
            result = await db_manager.execute_insert_with_returning(
                query,
                audio_id,
                transcription,
                datetime.utcnow()
            )
            
            if not result:
                logger.error(f"Failed to update transcription for audio {audio_id}")
                return {"success": False, "error": "Failed to update transcription in database"}
            
            recording = dict(result[0])
            if recording.get("s3_key"):
                recording["s3_url"] = s3_service.get_file_url(recording["s3_key"])
            
            logger.info(f"Successfully updated transcription for audio {audio_id}")
            
            # Generate embeddings for the transcription
            embeddings_updated = False
            embedding_error = None
            
            try:
                from app.services.rag_service import rag_service
                # Maintain legacy single-vector embedding for backward compatibility
                embedding_json = await rag_service.embed_audio_transcription(transcription)
                if embedding_json:
                    embedding_vector = json.loads(embedding_json)
                    embeddings_updated = await rag_service.store_embedding_vector(
                        audio_id, embedding_vector
                    )
                # New: trigger per-chunk indexing in background (non-blocking for UX)
                try:
                    await rag_service.index_lesson_transcription(audio_id, transcription)
                except Exception as _bg_e:
                    logger.warning(f"Background chunk indexing failed for lesson {audio_id}: {_bg_e}")
                    
            except Exception as embedding_e:
                embedding_error = f"Embedding generation failed: {str(embedding_e)}"
                logger.error(f"Error generating embeddings for audio {audio_id}: {str(embedding_e)}")
            
            return {
                "success": True,
                "embeddings_updated": embeddings_updated,
                "error": embedding_error,
                "recording": recording
            }
                
        except Exception as e:
            logger.error(f"Error updating transcription for audio {audio_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def delete_lessons_by_class(self, class_id: str) -> Dict[str, Any]:
        """Delete all lessons for a specific class from both database and S3"""
        try:
            # First, get all lessons for the class to get their S3 keys
            query = "SELECT id, s3_key FROM lessons WHERE class_id = $1"
            lessons = await db_manager.execute_query(query, class_id)
            
            if not lessons:
                logger.info(f"No lessons found for class {class_id}")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No lessons found for this class"
                }
            
            deleted_count = 0
            failed_deletions = []
            
            # Delete each lesson individually to ensure proper cleanup
            for lesson in lessons:
                lesson_id = lesson["id"]
                s3_key = lesson.get("s3_key")
                
                try:
                    # Delete from S3 if key exists
                    if s3_key:
                        s3_delete_success = await s3_service.delete_file(s3_key)
                        if not s3_delete_success:
                            logger.warning(f"Failed to delete file from S3: {s3_key}")
                    
                    # Delete from database
                    delete_result = await db_manager.execute_command(
                        "DELETE FROM lessons WHERE id = $1", 
                        lesson_id
                    )
                    
                    if delete_result:
                        deleted_count += 1
                        logger.info(f"Successfully deleted lesson {lesson_id}")
                    else:
                        failed_deletions.append(lesson_id)
                        logger.error(f"Failed to delete lesson {lesson_id} from database")
                        
                except Exception as e:
                    failed_deletions.append(lesson_id)
                    logger.error(f"Error deleting lesson {lesson_id}: {str(e)}")
            
            if failed_deletions:
                logger.warning(f"Failed to delete {len(failed_deletions)} lessons: {failed_deletions}")
                return {
                    "success": False,
                    "deleted_count": deleted_count,
                    "failed_count": len(failed_deletions),
                    "failed_lessons": failed_deletions,
                    "message": f"Deleted {deleted_count} lessons, {len(failed_deletions)} failed"
                }
            else:
                logger.info(f"Successfully deleted all {deleted_count} lessons for class {class_id}")
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "message": f"Successfully deleted {deleted_count} lessons"
                }
                
        except Exception as e:
            logger.error(f"Error deleting lessons for class {class_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "message": f"Failed to delete lessons: {str(e)}"
            }

    async def list_lessons_minimal_by_class(self, class_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Return minimal lesson info (id, lecture_title, upload_timestamp) for a class."""
        try:
            query = (
                "SELECT id, lecture_title, upload_timestamp "
                "FROM lessons WHERE class_id = $1 "
                "ORDER BY upload_timestamp DESC LIMIT $2 OFFSET $3"
            )
            rows = await db_manager.execute_query(query, class_id, limit, offset)
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"Error listing minimal lessons for class {class_id}: {str(e)}")
            return []

# Global lesson service instance
lesson_service = LessonService()
