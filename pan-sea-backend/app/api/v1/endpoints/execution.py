from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, status
from typing import Dict, Any, List
from pydantic import BaseModel
from app.services.execute_content_service import execution_service
from app.core.dependencies import get_current_teacher
from app.core.exceptions import PanSeaException
from app.utils.file_optimization import file_optimizer
from app.utils.file_validation import validate_material_file

router = APIRouter()


class ProcessOverallRequest(BaseModel):
    class_id: str
    lecture_title: str
    language: str
    # file will be received directly as a form file in the endpoint function
    current_teacher: dict = Depends(get_current_teacher)


@router.post("/process-overall", response_model=Dict[str, Any])
async def process_overall(
    class_id: str = Form(...),
    lecture_title: str = Form(...),
    language: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    materials: List[UploadFile] = File(
        None,
        description="Optional slides/books (max 3 files): PDF, PPTX, DOCX, TXT",
        max_items=3,
    ),
    current_teacher: dict = Depends(get_current_teacher),
) -> Dict[str, Any]:
    """Process overall content execution for a file and class"""
    import os
    try:
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Save uploaded audio to a temporary location (streamed)
        temp_path = await file_optimizer.stream_upload_to_temp(file)

        # Save optional materials to temporary files
        material_paths: List[str] = []
        material_names: List[str] = []
        try:
            if materials:
                if len(materials) > 3:
                    raise HTTPException(status_code=400, detail="You can upload up to 3 materials files.")
                for m in materials:
                    if not m:
                        continue
                    mat_tmp_path = await file_optimizer.stream_upload_to_temp(m)
                    # Validate file (extension, size, magic, optional AV)
                    err = validate_material_file(mat_tmp_path, original_name=m.filename)
                    if err:
                        # cleanup temp and reject
                        try:
                            if os.path.exists(mat_tmp_path):
                                os.unlink(mat_tmp_path)
                        except Exception:
                            pass
                        raise HTTPException(status_code=400, detail=f"Invalid material '{m.filename}': {err}")
                    material_paths.append(mat_tmp_path)
                    material_names.append(m.filename or os.path.basename(mat_tmp_path))
        except HTTPException:
            # Propagate validation errors
            raise
        except Exception:
            # Non-fatal, continue without materials
            material_paths = []
            material_names = []

        result = await execution_service.process_overall(
            class_id=class_id,
            subject=subject,
            lecture_title=lecture_title,
            language=language,
            file_path=temp_path,
            material_paths=material_paths,
            material_names=material_names,
            current_teacher=current_teacher,
        )

        return {
            "success": True,
            "result": result,
            "message": "Content processed successfully"
        }

    except PanSeaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except HTTPException as e:
        # Re-raise HTTPException from the service to preserve original status code
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # cleanup temp file
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        try:
            if 'material_paths' in locals():
                for p in material_paths or []:
                    try:
                        if p and os.path.exists(p):
                            os.unlink(p)
                    except Exception:
                        pass
        except Exception:
            pass


@router.get("/health", response_model=Dict[str, str])
async def execution_health() -> Dict[str, str]:
    """Health check endpoint for execution service"""
    return {
        "status": "healthy",
        "service": "execution_service"
    }
