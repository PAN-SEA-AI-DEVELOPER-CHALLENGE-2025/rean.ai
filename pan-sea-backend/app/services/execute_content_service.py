from fastapi import HTTPException
from app.services.audio_service import lesson_service
from app.services.summary_service import summary_service
from app.services.transcription_service import transcription_service
from app.utils.teacher_validation import validate_teacher_owns_class
from app.database.database import db_manager
from app.utils.document_extractor import DocumentExtractor
import logging
import subprocess

class ExecutionService:
    def __init__(self):
        self.lesson_service = lesson_service
        self.summary_service = summary_service
        self.transcription_service = transcription_service
        self.logger = logging.getLogger(__name__)

    async def test_database_connection(self) -> bool:
        """Test database connection to ensure we can connect"""
        try:
            # Simple query to test connection
            result = await db_manager.execute_query("SELECT 1 as test")
            if result and len(result) > 0:
                self.logger.info("Database connection test successful")
                return True
            else:
                self.logger.error("Database connection test failed - no result")
                return False
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False

    async def verify_class_exists(self, class_id: str) -> bool:
        """Verify that the class exists in the database"""
        try:
            query = "SELECT id FROM classes WHERE id = $1"
            result = await db_manager.execute_query(query, class_id)
            exists = result and len(result) > 0
            self.logger.info(f"Class {class_id} exists: {exists}")
            return exists
        except Exception as e:
            self.logger.error(f"Error checking if class exists: {str(e)}")
            return False

    async def log_database_tables(self):
        """Log available database tables for debugging"""
        try:
            query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            result = await db_manager.execute_query(query)
            if result:
                tables = [row['tablename'] for row in result]
                self.logger.info(f"Available database tables: {tables}")
            else:
                self.logger.warning("No tables found in database")
        except Exception as e:
            self.logger.error(f"Error listing database tables: {str(e)}")

    async def get_audio_duration(self, file_path: str) -> int:
        """Get audio duration in seconds using ffprobe"""
        try:
            # Use ffprobe to get audio duration
            cmd = [
                'ffprobe', 
                '-v', 'quiet', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                duration_seconds = float(result.stdout.strip())
                return int(duration_seconds)
            else:
                self.logger.warning(f"Could not get audio duration for {file_path}, using default")
                return 0
                
        except Exception as e:
            self.logger.warning(f"Error getting audio duration: {str(e)}, using default")
            return 0

    async def process_overall(
        self, 
        class_id: str, 
        subject: str,
        lecture_title: str,
        language: str,
        file_path: str,
        current_teacher: dict,
        material_paths: list | None = None,
        material_names: list | None = None,
        ):
        """Upload an audio file to S3, transcribe it, and store metadata in database. (Teachers only)"""
        # Test database connection first
        db_connected = await self.test_database_connection()
        if not db_connected:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Log database info for debugging
        await self.log_database_tables()
        
        # Verify class exists
        class_exists = await self.verify_class_exists(class_id)
        if not class_exists:
            raise HTTPException(status_code=404, detail=f"Class {class_id} not found")
        
        # file validation is performed at the API endpoint where the file is saved to disk

        # Validate language parameter
        if language not in ["english", "khmer"]:
            raise HTTPException(status_code=400, detail="Language must be 'english' or 'khmer'")

        teacher_id = current_teacher.get("id")
        if not teacher_id:
            raise HTTPException(status_code=400, detail="Teacher ID not found in token")

        self.logger.info(f"Audio upload attempt - Teacher ID from token: {teacher_id}, Type: {type(teacher_id)}, Class ID: {class_id}")
        self.logger.info(f"Full teacher data from token: {current_teacher}")

        # Validate teacher owns the class
        await validate_teacher_owns_class(teacher_id, class_id)

        temp_path = file_path

        try:
            self.logger.info(f"Starting audio processing for class {class_id}")
            
            # Get audio duration
            audio_duration = await self.get_audio_duration(temp_path)
            self.logger.info(f"Audio duration: {audio_duration} seconds")
            
            # Upload audio file to S3 and get metadata
            self.logger.info(f"Uploading audio file to S3 for class {class_id}")
            upload_result = await lesson_service.upload_audio_file(
                file_path=temp_path,
                class_id=class_id,
                lecture_title=lecture_title
            )
            
            if not upload_result:
                self.logger.error(f"Failed to upload audio file for class {class_id}")
                raise HTTPException(status_code=500, detail="Failed to upload audio file")
            
            audio_id = upload_result.get("audio_id")
            self.logger.info(f"Audio file uploaded successfully with ID: {audio_id}")
            
            # Transcribe the audio file
            self.logger.info(f"Starting transcription for audio {audio_id}")
            transcription_result = await transcription_service.transcribe_audio(
                file_path=temp_path,
                language=language
            )
            # Update the audio record with transcription
            transcription_text = transcription_result.get("transcription", "")
            self.logger.info(f"Transcription completed for audio {audio_id}, length: {len(transcription_text)} characters")

            # Extract materials text per-file (with caps), then upload and store
            uploaded_materials = []
            materials_text = ""
            per_file_texts: list[str] = []
            try:
                if material_paths:
                    for p in material_paths:
                        try:
                            extracted = DocumentExtractor.extract_text_from_file(p)
                            per_file_texts.append(extracted)
                        except Exception:
                            per_file_texts.append("")
                    try:
                        materials_text = DocumentExtractor.extract_text_from_files(material_paths)
                    except Exception:
                        materials_text = ""
                    self.logger.info(f"Uploading {len(material_paths)} material files for lesson {audio_id}")
                    uploaded_materials = await lesson_service.upload_material_files(
                        file_paths=material_paths,
                        file_names=material_names or [],
                        class_id=class_id,
                        lesson_id=audio_id,
                        extracted_texts=per_file_texts,
                    )
                    # OCR fallback for low-text files (scanned PDFs/images)
                    try:
                        from app.services.textract_service import textract_service
                        ocr_threshold_chars = 1000
                        # Upload already done; use stored S3 key in DB rows
                        for mres in uploaded_materials:
                            try:
                                if not mres.get("success"):
                                    continue
                                mat = mres.get("material", {})
                                s3_key = mat.get("s3_key")
                                if not s3_key:
                                    continue
                                idx = uploaded_materials.index(mres)
                                current_text = per_file_texts[idx] if idx < len(per_file_texts) else ""
                                if current_text and len(current_text) >= ocr_threshold_chars:
                                    continue
                                # Run Textract OCR from S3
                                bucket = lesson_service.s3_service.bucket_name if hasattr(lesson_service, 's3_service') else None
                                if not bucket:
                                    from app.core.s3 import s3_service as _s3
                                    bucket = _s3.bucket_name
                                # For large docs, offload to background queue: page-wise structured extraction
                                pages = await textract_service.extract_pages_s3(bucket=bucket, key=s3_key, include_tables=True)
                                ocr_text = "\n\n".join([p.get("markdown", "") for p in pages]) if pages else await textract_service.extract_text_s3(bucket=bucket, key=s3_key, include_tables=True)
                                if ocr_text and len(ocr_text) > len(current_text):
                                    per_file_texts[idx] = ocr_text[:50000]
                                    # Optionally update DB extracted_text
                                    try:
                                        await db_manager.execute_command(
                                            "UPDATE lesson_materials SET extracted_text = $1 WHERE id = $2",
                                            per_file_texts[idx],
                                            mat.get("id"),
                                        )
                                    except Exception:
                                        pass
                            except Exception:
                                continue
                    except Exception as ocr_e:
                        self.logger.warning(f"OCR fallback failed: {ocr_e}")
            except Exception as mat_upload_e:
                self.logger.warning(f"Material processing failed: {str(mat_upload_e)}")

            # Combine transcription with materials for indexing and summary context
            # Use per-file texts (OCR-enhanced), not only concatenated materials_text
            combined_text = transcription_text
            if per_file_texts:
                annotated = []
                for i, txt in enumerate(per_file_texts):
                    if not txt:
                        continue
                    name = (material_names[i] if material_names and i < len(material_names) else f"material_{i+1}")
                    annotated.append(f"[Material: {name}]\n{txt}")
                if annotated:
                    combined_text = f"{transcription_text}\n\n[Teacher Materials]\n" + "\n\n".join(annotated)
            if len(combined_text) > 200000:
                combined_text = combined_text[:200000]

            if transcription_result:
                self.logger.info(f"Updating audio record with transcription and embeddings for audio {audio_id}")
                update_result = await lesson_service.update_transcription(
                    audio_id=audio_id,
                    transcription=combined_text
                )

                # Always attempt to generate and save a summary regardless of embeddings result
                self.logger.info(f"Generating summary for class {class_id}")
                
                # Generate summary data first without saving
                summary_result = await summary_service.summary_service(
                    transcription=combined_text,
                    class_id=class_id,
                    subject=subject,
                    save_to_db=False  # Don't save yet, we need to add duration
                )
                
                if summary_result:
                    # Add duration to summary data and save to database
                    summary_result["duration"] = audio_duration
                    save_data = {
                        "class_id": class_id,
                        "lesson_id": audio_id,  # Link summary to the lesson
                        "lecture_title": lecture_title,  # Ensure lecture_title is included
                        **summary_result
                    }
                    save_data.pop("created_at", None)  # Remove created_at, let DB handle it
                    
                    saved_summary = await summary_service.create_summary(save_data)
                    if saved_summary:
                        self.logger.info(f"Summary saved successfully for class {class_id}")
                        summary_result = saved_summary
                    else:
                        self.logger.error(f"Failed to save summary for class {class_id}")
                        summary_result = None

                # Excerpt to avoid huge payloads
                excerpt = combined_text[:1000]
                response_data = {
                    **upload_result,
                    "transcription_excerpt": excerpt,
                    "language": language,
                    "embeddings_created": update_result.get("embeddings_updated", False) if update_result else False,
                    "materials": uploaded_materials,
                }

                if summary_result:
                    self.logger.info(f"Summary generated successfully for class {class_id}")
                    response_data["summary"] = summary_result
                else:
                    self.logger.warning(f"Summary generation failed for class {class_id}")
                    response_data["summary_error"] = "Summary service unavailable"

                self.logger.info(f"Audio processing completed successfully for class {class_id}")
                return {
                    "message": "Audio file uploaded and transcribed successfully",
                    "data": response_data
                }
            else:
                # Upload succeeded but transcription failed - still return success but log the error
                error_msg = transcription_result.get("error", "Unknown transcription error") if transcription_result else "Transcription service unavailable"
                self.logger.error(f"Transcription failed for audio {audio_id}: {error_msg}")
                return {
                    "message": "Audio file uploaded successfully but transcription failed",
                    "data": {
                        **upload_result,
                        "transcription_error": error_msg,
                        "language": language
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Upload/transcription failed for class {class_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload/transcription failed: {str(e)}")
        # Note: cleanup of the temporary file is the responsibility of the caller (API endpoint)

execution_service = ExecutionService()