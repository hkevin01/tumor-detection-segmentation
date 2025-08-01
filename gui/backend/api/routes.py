"""
API routes for the tumor detection application.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
import uuid

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from models import get_storage, StudyStatus

# Initialize logger
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter() if FASTAPI_AVAILABLE else None


async def process_dicom_file(file_path: str, study_id: str) -> Dict[str, Any]:
    """
    Process DICOM file and run tumor detection.
    This is a placeholder that should be replaced with actual inference logic.
    """
    try:
        # Simulate processing time
        await asyncio.sleep(2)
        
        # TODO: Replace with actual inference
        # from inference.inference import TumorPredictor
        # predictor = TumorPredictor(model_path="./models/unet_v1.pth")
        # result = predictor.predict_single(file_path)
        
        # Placeholder result
        result = {
            "study_id": study_id,
            "prediction": "tumor_detected",
            "confidence": 0.85,
            "tumor_volume": 12.5,
            "coordinates": [[100, 150, 75], [120, 170, 85]],
            "processing_time": 2.0,
            "model_used": "unet_v1"
        }
        
        # Store prediction result
        storage = get_storage()
        prediction_id = storage.add_prediction(result)
        result["prediction_id"] = prediction_id
        
        # Update study status
        storage.update_study_status(study_id, StudyStatus.COMPLETED)
        
        logger.info(f"Processing completed for study: {study_id}")
        return result
        
    except Exception as e:
        logger.error(f"Processing failed for study {study_id}: {e}")
        storage = get_storage()
        storage.update_study_status(study_id, StudyStatus.FAILED)
        raise


if FASTAPI_AVAILABLE:
    
    @router.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "tumor-detection-api"
        }
    
    @router.post("/upload")
    async def upload_dicom(
        file: UploadFile = File(...),
        patient_id: Optional[str] = None
    ):
        """Upload DICOM file for processing."""
        try:
            # Validate file type
            if not file.filename.lower().endswith(('.dcm', '.dicom')):
                raise HTTPException(
                    status_code=400,
                    detail="Only DICOM files (.dcm, .dicom) are supported"
                )
            
            # Create upload directory
            upload_dir = Path("./uploads") / datetime.now().strftime("%Y%m%d")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            new_filename = f"{file_id}{file_extension}"
            file_path = upload_dir / new_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Create patient if not exists
            storage = get_storage()
            if not patient_id:
                patient_data = {
                    "name": f"Patient_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "medical_record_number": f"MRN_{file_id[:8].upper()}"
                }
                patient_id = storage.add_patient(patient_data)
            
            # Create study record
            study_data = {
                "patient_id": patient_id,
                "study_date": datetime.now(),
                "modality": "CT",  # Default, should be extracted from DICOM
                "description": f"Study for {file.filename}",
                "file_path": str(file_path)
            }
            study_id = storage.add_study(study_data)
            
            # Start async processing
            asyncio.create_task(process_dicom_file(str(file_path), study_id))
            
            logger.info(f"File uploaded: {file_path}")
            
            return {
                "message": "File uploaded successfully",
                "study_id": study_id,
                "patient_id": patient_id,
                "filename": file.filename,
                "file_path": str(file_path),
                "size": len(content),
                "upload_time": datetime.now().isoformat(),
                "status": "processing"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/studies")
    async def get_studies(patient_id: Optional[str] = None):
        """Get list of studies."""
        try:
            storage = get_storage()
            studies = storage.get_studies(patient_id)
            
            # Add AI results status
            for study in studies:
                # Check if there are prediction results for this study
                predictions = [
                    p for p in storage.predictions.values() 
                    if p.get("study_id") == study["id"]
                ]
                study["has_ai_results"] = len(predictions) > 0
                study["latest_prediction"] = predictions[-1] if predictions else None
            
            return {
                "studies": studies,
                "count": len(studies),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get studies: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/studies/{study_id}")
    async def get_study(study_id: str):
        """Get specific study details."""
        try:
            storage = get_storage()
            
            if study_id not in storage.studies:
                raise HTTPException(status_code=404, detail="Study not found")
            
            study = storage.studies[study_id]
            
            # Get predictions for this study
            predictions = [
                p for p in storage.predictions.values()
                if p.get("study_id") == study_id
            ]
            
            # Get reports for this study
            reports = [
                r for r in storage.reports.values()
                if r.get("study_id") == study_id
            ]
            
            return {
                "study": study,
                "predictions": predictions,
                "reports": reports,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get study {study_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/predict")
    async def predict_tumor(study_id: str, model_id: str = "unet_v1"):
        """Run tumor detection on a study."""
        try:
            storage = get_storage()
            
            if study_id not in storage.studies:
                raise HTTPException(status_code=404, detail="Study not found")
            
            study = storage.studies[study_id]
            file_path = study.get("file_path")
            
            if not file_path or not Path(file_path).exists():
                raise HTTPException(
                    status_code=400, 
                    detail="Study file not found"
                )
            
            # Update study status
            storage.update_study_status(study_id, StudyStatus.PROCESSING)
            
            # Process the file
            result = await process_dicom_file(file_path, study_id)
            
            return {
                "message": "Prediction completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/reports")
    async def generate_report(study_id: str, template: str = "standard"):
        """Generate clinical report for a study."""
        try:
            storage = get_storage()
            
            if study_id not in storage.studies:
                raise HTTPException(status_code=404, detail="Study not found")
            
            # Get latest prediction for this study
            predictions = [
                p for p in storage.predictions.values()
                if p.get("study_id") == study_id
            ]
            
            if not predictions:
                raise HTTPException(
                    status_code=400,
                    detail="No AI results available for this study"
                )
            
            latest_prediction = predictions[-1]
            
            # Generate report data
            report_data = {
                "study_id": study_id,
                "template": template,
                "findings": {
                    "tumor_detected": latest_prediction.get("prediction") == "tumor_detected",
                    "confidence": latest_prediction.get("confidence"),
                    "tumor_volume": latest_prediction.get("tumor_volume"),
                    "coordinates": latest_prediction.get("coordinates"),
                    "model_used": latest_prediction.get("model_used")
                },
                "recommendations": _generate_recommendations(latest_prediction),
                "generated_by": "AI System",
                "report_path": f"./reports/{study_id}_report.pdf"
            }
            
            # Store report
            report_id = storage.add_report(report_data)
            
            logger.info(f"Report generated for study: {study_id}")
            
            return {
                "message": "Report generated successfully",
                "report_id": report_id,
                "report": report_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/models")
    async def get_available_models():
        """Get list of available AI models."""
        try:
            storage = get_storage()
            models = storage.get_models()
            
            return {
                "models": models,
                "count": len(models),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/patients")
    async def get_patients():
        """Get list of patients."""
        try:
            storage = get_storage()
            patients = list(storage.patients.values())
            
            # Add study count for each patient
            for patient in patients:
                patient_studies = [
                    s for s in storage.studies.values()
                    if s.get("patient_id") == patient["id"]
                ]
                patient["study_count"] = len(patient_studies)
            
            return {
                "patients": patients,
                "count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get patients: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # DICOM Viewer Endpoints
    @router.get("/studies/{study_id}/series")
    async def get_study_series(study_id: str):
        """Get DICOM series information for a study."""
        try:
            storage = get_storage()
            
            if study_id not in storage.studies:
                raise HTTPException(status_code=404, detail="Study not found")
            
            study = storage.studies[study_id]
            
            # Mock series data - in real implementation, parse DICOM metadata
            series_data = [
                {
                    "series_instance_uid": f"{study_id}_series_001",
                    "series_number": 1,
                    "modality": "CT",
                    "series_description": "CT Chest with contrast",
                    "slice_count": 150,
                    "slice_thickness": 1.25,
                    "pixel_spacing": [0.5, 0.5],
                    "image_orientation": [1, 0, 0, 0, 1, 0],
                    "image_position": [0, 0, 0]
                }
            ]
            
            return {
                "study_instance_uid": study_id,
                "series": series_data,
                "count": len(series_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get series for study {study_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/series/{series_instance_uid}/images")
    async def get_series_images(series_instance_uid: str):
        """Get DICOM image information for a series."""
        try:
            # Mock image data - in real implementation, parse DICOM directory
            images_data = []
            
            # Generate mock image URLs for Cornerstone
            for i in range(150):  # Mock 150 slices
                images_data.append({
                    "sop_instance_uid": f"{series_instance_uid}_image_{i:03d}",
                    "instance_number": i + 1,
                    "slice_location": i * 1.25,
                    "image_url": f"/api/dicom/images/{series_instance_uid}/{i:03d}.dcm",
                    "wado_uri": f"wadouri:/api/dicom/images/{series_instance_uid}/{i:03d}.dcm"
                })
            
            return {
                "series_instance_uid": series_instance_uid,
                "images": images_data,
                "count": len(images_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get images for series {series_instance_uid}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/dicom/images/{series_instance_uid}/{image_name}")
    async def get_dicom_image(series_instance_uid: str, image_name: str):
        """Serve DICOM image file for viewing."""
        try:
            from fastapi.responses import FileResponse
            
            # In real implementation, map to actual DICOM file
            # For now, return a placeholder or the study file
            storage = get_storage()
            
            # Find study containing this series
            study_id = series_instance_uid.split('_series_')[0]
            if study_id in storage.studies:
                study_file = storage.studies[study_id].get("file_path")
                if study_file and Path(study_file).exists():
                    return FileResponse(
                        path=study_file,
                        media_type="application/dicom",
                        headers={"Content-Disposition": f"inline; filename={image_name}"}
                    )
            
            raise HTTPException(status_code=404, detail="DICOM image not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to serve DICOM image: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/ai/predictions/{series_instance_uid}")
    async def get_ai_predictions(series_instance_uid: str):
        """Get AI predictions for a series."""
        try:
            storage = get_storage()
            
            # Find study containing this series
            study_id = series_instance_uid.split('_series_')[0]
            
            # Get predictions for this study
            predictions = [
                p for p in storage.predictions.values()
                if p.get("study_id") == study_id
            ]
            
            # Mock tumor detections for visualization
            detections = []
            if predictions:
                prediction = predictions[-1]
                if prediction.get("prediction") == "tumor_detected":
                    coordinates = prediction.get("coordinates", [])
                    confidence = prediction.get("confidence", 0.85)
                    
                    for i, coord in enumerate(coordinates):
                        detections.append({
                            "x": 25,  # percentage from left
                            "y": 30,  # percentage from top
                            "width": 15,  # percentage width
                            "height": 20,  # percentage height
                            "confidence": confidence,
                            "type": "Tumor",
                            "slice_index": i % 75,  # distribute across slices
                            "probability_map": f"/api/ai/probability_maps/{study_id}_{i}.png"
                        })
            
            return {
                "series_instance_uid": series_instance_uid,
                "detections": detections,
                "count": len(detections),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI predictions for series {series_instance_uid}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/ai/analyze")
    async def analyze_series(request: Dict[str, Any]):
        """Trigger AI analysis for a series."""
        try:
            series_instance_uid = request.get("series_instance_uid")
            model_name = request.get("model_name", "tumor_detection_v1")
            
            if not series_instance_uid:
                raise HTTPException(status_code=400, detail="series_instance_uid required")
            
            # Find study containing this series
            study_id = series_instance_uid.split('_series_')[0]
            
            # Create analysis task
            task_id = str(uuid.uuid4())
            
            # Start background processing (mock)
            asyncio.create_task(process_series_analysis(task_id, study_id, model_name))
            
            return {
                "task_id": task_id,
                "status": "started",
                "estimated_time": "2-5 minutes",
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start AI analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/ai/results/{task_id}")
    async def get_ai_results(task_id: str):
        """Get AI analysis results by task ID."""
        try:
            # Mock results - in real implementation, check task status
            await asyncio.sleep(0.1)  # Simulate checking
            
            # Mock completed analysis
            return {
                "task_id": task_id,
                "status": "completed",
                "detections": [
                    {
                        "x": 25,
                        "y": 30,
                        "width": 15,
                        "height": 20,
                        "confidence": 0.89,
                        "type": "Tumor",
                        "slice_index": 45
                    }
                ],
                "findings": {
                    "tumor_count": 1,
                    "max_confidence": 0.89,
                    "recommendations": [
                        "High confidence tumor detection",
                        "Recommend immediate oncology consultation",
                        "Consider follow-up imaging in 3 months"
                    ],
                    "risk_level": "high"
                },
                "processing_time": 3.2,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI results for task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def process_series_analysis(task_id: str, study_id: str, model_name: str):
    """Background task to process series analysis."""
    try:
        # Simulate processing time
        await asyncio.sleep(3)
        logger.info(f"Completed analysis task {task_id} for study {study_id}")
    except Exception as e:
        logger.error(f"Analysis task {task_id} failed: {e}")


def _generate_recommendations(prediction: Dict[str, Any]) -> str:
    """Generate clinical recommendations based on prediction results."""
    if prediction.get("prediction") == "tumor_detected":
        confidence = prediction.get("confidence", 0)
        volume = prediction.get("tumor_volume", 0)
        
        if confidence > 0.9:
            urgency = "immediate"
        elif confidence > 0.7:
            urgency = "prompt"
        else:
            urgency = "routine"
        
        if volume > 20:
            size_desc = "large"
        elif volume > 5:
            size_desc = "moderate"
        else:
            size_desc = "small"
        
        return (
            f"Tumor detected with {confidence:.1%} confidence. "
            f"{size_desc.capitalize()} tumor volume: {volume:.1f}cc. "
            f"Recommend {urgency} follow-up and consultation with oncology."
        )
    else:
        return (
            "No tumor detected in current study. "
            "Continue routine screening as per clinical guidelines."
        )


# Export router
def get_router():
    """Get the API router."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not available")
    return router
