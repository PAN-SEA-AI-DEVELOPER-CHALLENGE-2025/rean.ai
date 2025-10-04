"""
MFA Training Router

API endpoints for training MFA models using TTS datasets.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

from service.mfa_training_service import MFATTSTrainingService
from config.settings import get_config


# Initialize router
router = APIRouter(prefix="/mfa-training", tags=["MFA Training"])
logger = logging.getLogger(__name__)

# Global service instance
config = get_config()
training_service = MFATTSTrainingService(config)


class TrainingRequest(BaseModel):
    """Request model for training operations."""
    force_rebuild: Optional[bool] = False
    num_jobs: Optional[int] = 4


class ValidationResponse(BaseModel):
    """Response model for dataset validation."""
    success: bool
    issues: List[str] = []
    statistics: Dict[str, Any] = {}
    recommendations: List[str] = []
    error: Optional[str] = None


class TrainingResponse(BaseModel):
    """Response model for training operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_training_status():
    """
    Get the current status of MFA training data and models.
    """
    try:
        status = training_service.get_training_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-dataset", response_model=ValidationResponse)
async def validate_tts_dataset():
    """
    Validate the TTS dataset for MFA training compatibility.
    """
    try:
        result = training_service.validate_tts_dataset()
        return ValidationResponse(**result)
    except Exception as e:
        logger.error(f"Failed to validate dataset: {e}")
        return ValidationResponse(
            success=False,
            error=str(e)
        )


@router.post("/prepare-dataset", response_model=TrainingResponse)
async def prepare_dataset_for_training(request: TrainingRequest):
    """
    Prepare the TTS dataset for MFA training.
    Creates the proper directory structure and file organization.
    """
    try:
        result = training_service.prepare_tts_dataset_for_mfa()
        
        if result['success']:
            return TrainingResponse(
                success=True,
                message=f"Dataset prepared successfully. Processed {result['processed_files']} files.",
                data=result
            )
        else:
            return TrainingResponse(
                success=False,
                message="Failed to prepare dataset",
                error=result.get('error')
            )
            
    except Exception as e:
        logger.error(f"Failed to prepare dataset: {e}")
        return TrainingResponse(
            success=False,
            message="Failed to prepare dataset",
            error=str(e)
        )


@router.post("/generate-dictionary", response_model=TrainingResponse)
async def generate_pronunciation_dictionary():
    """
    Generate a Khmer pronunciation dictionary from the TTS dataset.
    """
    try:
        result = training_service.generate_khmer_pronunciation_dictionary()
        
        if result['success']:
            return TrainingResponse(
                success=True,
                message=f"Dictionary generated successfully with {result['word_count']} words.",
                data=result
            )
        else:
            return TrainingResponse(
                success=False,
                message="Failed to generate dictionary",
                error=result.get('error')
            )
            
    except Exception as e:
        logger.error(f"Failed to generate dictionary: {e}")
        return TrainingResponse(
            success=False,
            message="Failed to generate dictionary",
            error=str(e)
        )


@router.post("/train-acoustic-model", response_model=TrainingResponse)
async def train_acoustic_model(
    background_tasks: BackgroundTasks,
    request: TrainingRequest
):
    """
    Train MFA acoustic model using the prepared TTS dataset.
    This is a long-running operation that runs in the background.
    """
    try:
        # Check if dataset is prepared
        status = training_service.get_training_status()
        if not status.get('dataset_prepared', False):
            return TrainingResponse(
                success=False,
                message="Dataset not prepared. Please prepare dataset first.",
                error="Dataset not prepared"
            )
        
        if not status.get('dictionary_generated', False):
            return TrainingResponse(
                success=False,
                message="Dictionary not generated. Please generate dictionary first.",
                error="Dictionary not available"
            )
        
        # Check if model already exists
        if status.get('acoustic_model_trained', False) and not request.force_rebuild:
            return TrainingResponse(
                success=True,
                message="Acoustic model already exists. Use force_rebuild=true to retrain.",
                data={"model_path": status['files'].get('acoustic_model_path')}
            )
        
        # Start training in background
        background_tasks.add_task(
            _train_acoustic_model_background,
            request.dict()
        )
        
        return TrainingResponse(
            success=True,
            message="Acoustic model training started in background. Check status for progress.",
            data={"training_started": True}
        )
        
    except Exception as e:
        logger.error(f"Failed to start acoustic model training: {e}")
        return TrainingResponse(
            success=False,
            message="Failed to start training",
            error=str(e)
        )


@router.post("/full-training-pipeline", response_model=TrainingResponse)
async def run_full_training_pipeline(
    background_tasks: BackgroundTasks,
    request: TrainingRequest
):
    """
    Run the complete training pipeline: prepare dataset, generate dictionary, and train acoustic model.
    """
    try:
        results = {}
        
        # Step 1: Validate dataset
        logger.info("Step 1: Validating TTS dataset...")
        validation_result = training_service.validate_tts_dataset()
        results['validation'] = validation_result
        
        if not validation_result['success']:
            return TrainingResponse(
                success=False,
                message="Dataset validation failed",
                error="Dataset validation failed",
                data=results
            )
        
        # Step 2: Prepare dataset
        logger.info("Step 2: Preparing dataset for MFA training...")
        prepare_result = training_service.prepare_tts_dataset_for_mfa()
        results['preparation'] = prepare_result
        
        if not prepare_result['success']:
            return TrainingResponse(
                success=False,
                message="Dataset preparation failed",
                error=prepare_result.get('error'),
                data=results
            )
        
        # Step 3: Generate dictionary
        logger.info("Step 3: Generating pronunciation dictionary...")
        dict_result = training_service.generate_khmer_pronunciation_dictionary()
        results['dictionary'] = dict_result
        
        if not dict_result['success']:
            return TrainingResponse(
                success=False,
                message="Dictionary generation failed",
                error=dict_result.get('error'),
                data=results
            )
        
        # Step 4: Start acoustic model training in background
        logger.info("Step 4: Starting acoustic model training...")
        background_tasks.add_task(
            _train_acoustic_model_background,
            request.dict()
        )
        
        results['training_started'] = True
        
        return TrainingResponse(
            success=True,
            message="Full training pipeline completed setup. Acoustic model training started in background.",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Failed to run training pipeline: {e}")
        return TrainingResponse(
            success=False,
            message="Training pipeline failed",
            error=str(e)
        )


async def _train_acoustic_model_background(request_data: Dict[str, Any]):
    """
    Background task for training acoustic model.
    """
    try:
        logger.info("Starting background acoustic model training...")
        result = training_service.train_acoustic_model()
        
        if result['success']:
            logger.info(f"Acoustic model training completed: {result['model_path']}")
        else:
            logger.error(f"Acoustic model training failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Background training failed: {e}")


@router.get("/model-info", response_model=Dict[str, Any])
async def get_model_info():
    """
    Get information about available MFA models.
    """
    try:
        # Import here to avoid circular imports
        from service.mfa_service import MFAService
        
        mfa_service = MFAService(config)
        model_status = mfa_service.get_model_status()
        training_status = training_service.get_training_status()
        
        return {
            "success": True,
            "data": {
                "model_status": model_status,
                "training_status": training_status,
                "service_info": mfa_service.get_service_info()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/training-data", response_model=TrainingResponse)
async def clean_training_data():
    """
    Clean up training data and intermediate files.
    """
    try:
        training_dir = Path(config.get('project_root', '.')) / 'mfa_models' / 'training'
        
        if training_dir.exists():
            import shutil
            shutil.rmtree(training_dir)
            training_dir.mkdir(parents=True, exist_ok=True)
            
            return TrainingResponse(
                success=True,
                message="Training data cleaned successfully"
            )
        else:
            return TrainingResponse(
                success=True,
                message="No training data to clean"
            )
            
    except Exception as e:
        logger.error(f"Failed to clean training data: {e}")
        return TrainingResponse(
            success=False,
            message="Failed to clean training data",
            error=str(e)
        )
