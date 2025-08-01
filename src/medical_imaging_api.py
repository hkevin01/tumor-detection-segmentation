#!/usr/bin/env python3
"""
FastAPI Backend for Medical Imaging GUI
Connects the frontend DICOM viewer with MONAI-based AI models
"""

import os
import io
import uuid
import tempfile
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np

# Try importing optional dependencies
try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

try:
    import SimpleITK as sitk
    SIMPLEITK_AVAILABLE = True
except ImportError:
    SIMPLEITK_AVAILABLE = False

# Import our medical AI backend
from medical_ai_backend import MedicalImagingAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(
    title="Medical Imaging AI API",
    description="REST API for tumor detection and segmentation",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global AI instance
ai_backend = None
stored_dicoms = {}  # In-memory storage for demo (use database in production)


# Pydantic models for API requests/responses
class PredictionRequest(BaseModel):
    dicom_id: str
    model_name: str = "unet"
    inference_params: Optional[Dict[str, Any]] = None


class DicomMetadata(BaseModel):
    patient_id: str
    study_date: str
    modality: str
    series_description: str
    spacing: List[float]
    dimensions: List[int]
    window_center: float
    window_width: float


class TumorPrediction(BaseModel):
    segmentation_mask: List[List[List[float]]]
    confidence_score: float
    tumor_volume: float
    bounding_box: Dict[str, List[int]]
    model_used: str
    inference_time: str


class BatchPredictionRequest(BaseModel):
    dicom_ids: List[str]
    model_name: str = "unet"


# API Routes

@app.on_event("startup")
async def startup_event():
    """Initialize the AI backend on startup"""
    global ai_backend
    
    try:
        ai_backend = MedicalImagingAI()
        logger.info("Medical Imaging AI backend initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize AI backend: %s", str(e))
        ai_backend = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Medical Imaging AI API",
        "status": "online",
        "ai_backend_available": ai_backend is not None,
        "pydicom_available": PYDICOM_AVAILABLE,
        "simpleitk_available": SIMPLEITK_AVAILABLE
    }


@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models"""
    if not ai_backend:
        raise HTTPException(status_code=503, detail="AI backend not available")
    
    try:
        model_info = ai_backend.get_model_info()
        available_models = list(ai_backend.config["models"].keys())
        
        return {
            "available_models": available_models,
            "loaded_models": list(model_info.keys()),
            "model_details": model_info
        }
    except Exception as e:
        logger.error("Error getting model info: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/{model_name}/load")
async def load_model(model_name: str, checkpoint_path: Optional[str] = None):
    """Load a specific AI model"""
    if not ai_backend:
        raise HTTPException(status_code=503, detail="AI backend not available")
    
    try:
        model = ai_backend.load_model(model_name, checkpoint_path)
        return {
            "message": f"Model {model_name} loaded successfully",
            "model_info": {
                "name": model_name,
                "architecture": model.__class__.__name__,
                "parameters": sum(p.numel() for p in model.parameters()),
                "device": str(next(model.parameters()).device)
            }
        }
    except Exception as e:
        logger.error("Error loading model %s: %s", model_name, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dicom/upload")
async def upload_dicom(file: UploadFile = File(...)):
    """Upload and process DICOM file"""
    if not PYDICOM_AVAILABLE:
        # Mock response for demo when pydicom is not available
        dicom_id = str(uuid.uuid4())
        mock_metadata = {
            "patient_id": "DEMO_001",
            "study_date": datetime.now().strftime("%Y%m%d"),
            "modality": "MR",
            "series_description": "T1W_MPRAGE",
            "spacing": [1.0, 1.0, 1.0],
            "dimensions": [256, 256, 128],
            "window_center": 40.0,
            "window_width": 400.0
        }
        
        stored_dicoms[dicom_id] = {
            "filename": file.filename,
            "metadata": mock_metadata,
            "upload_time": datetime.now().isoformat()
        }
        
        return {
            "dicom_id": dicom_id,
            "filename": file.filename,
            "metadata": mock_metadata,
            "message": "DICOM uploaded successfully (demo mode)"
        }
    
    try:
        # Read uploaded file
        content = await file.read()
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Read DICOM metadata
            dicom = pydicom.dcmread(tmp_path)
            
            # Extract metadata
            metadata = {
                "patient_id": getattr(dicom, 'PatientID', 'Unknown'),
                "study_date": getattr(dicom, 'StudyDate', 'Unknown'),
                "modality": getattr(dicom, 'Modality', 'Unknown'),
                "series_description": getattr(dicom, 'SeriesDescription', 'Unknown'),
                "spacing": [1.0, 1.0, 1.0],  # Default values
                "dimensions": list(dicom.pixel_array.shape),
                "window_center": float(getattr(dicom, 'WindowCenter', 40)),
                "window_width": float(getattr(dicom, 'WindowWidth', 400))
            }
            
            # Set proper spacing if available
            if hasattr(dicom, 'PixelSpacing'):
                spacing = list(dicom.PixelSpacing)
                if hasattr(dicom, 'SliceThickness'):
                    spacing.append(float(dicom.SliceThickness))
                else:
                    spacing.append(1.0)
                metadata["spacing"] = spacing
            
            # Generate unique ID for this DICOM
            dicom_id = str(uuid.uuid4())
            
            # Store DICOM data (in production, use proper database)
            stored_dicoms[dicom_id] = {
                "filename": file.filename,
                "file_path": tmp_path,
                "metadata": metadata,
                "upload_time": datetime.now().isoformat()
            }
            
            return {
                "dicom_id": dicom_id,
                "filename": file.filename,
                "metadata": metadata,
                "message": "DICOM uploaded and processed successfully"
            }
            
        except Exception as e:
            # Clean up temporary file on error
            os.unlink(tmp_path)
            raise e
            
    except Exception as e:
        logger.error("Error processing DICOM upload: %s", str(e))
        raise HTTPException(status_code=500, detail=f"DICOM processing failed: {str(e)}")


@app.get("/api/dicom/{dicom_id}")
async def get_dicom_info(dicom_id: str):
    """Get information about a stored DICOM"""
    if dicom_id not in stored_dicoms:
        raise HTTPException(status_code=404, detail="DICOM not found")
    
    dicom_data = stored_dicoms[dicom_id]
    return {
        "dicom_id": dicom_id,
        "filename": dicom_data["filename"],
        "metadata": dicom_data["metadata"],
        "upload_time": dicom_data["upload_time"]
    }


@app.post("/api/ai/predict")
async def predict_tumor(request: PredictionRequest):
    """Run tumor prediction on a DICOM image"""
    if not ai_backend:
        raise HTTPException(status_code=503, detail="AI backend not available")
    
    if request.dicom_id not in stored_dicoms:
        raise HTTPException(status_code=404, detail="DICOM not found")
    
    try:
        dicom_data = stored_dicoms[request.dicom_id]
        
        # For demo purposes, return mock prediction
        # In real implementation, this would call ai_backend.predict_tumor()
        mock_prediction = {
            "segmentation_mask": [[[0.0 for _ in range(64)] for _ in range(128)] for _ in range(128)],
            "confidence_score": 0.87,
            "tumor_volume": 1245.6,
            "bounding_box": {
                "min": [45, 67, 23],
                "max": [89, 112, 67]
            },
            "model_used": request.model_name,
            "inference_time": datetime.now().isoformat(),
            "metadata": dicom_data["metadata"]
        }
        
        # Add some realistic tumor regions to the mock mask
        mask = mock_prediction["segmentation_mask"]
        for z in range(23, 67):
            for y in range(67, 112):
                for x in range(45, 89):
                    if ((x-67)**2 + (y-89)**2 + (z-45)**2) < 20**2:
                        mask[z][y][x] = 1.0
        
        return mock_prediction
        
    except Exception as e:
        logger.error("Error running prediction: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/batch-predict")
async def batch_predict(request: BatchPredictionRequest, background_tasks: BackgroundTasks):
    """Run batch tumor prediction on multiple DICOM images"""
    if not ai_backend:
        raise HTTPException(status_code=503, detail="AI backend not available")
    
    # Validate all DICOM IDs exist
    missing_ids = [dicom_id for dicom_id in request.dicom_ids 
                   if dicom_id not in stored_dicoms]
    
    if missing_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"DICOMs not found: {missing_ids}"
        )
    
    # Generate batch job ID
    batch_id = str(uuid.uuid4())
    
    # For demo, return immediate mock results
    results = []
    for dicom_id in request.dicom_ids:
        dicom_data = stored_dicoms[dicom_id]
        
        result = {
            "dicom_id": dicom_id,
            "filename": dicom_data["filename"],
            "prediction": {
                "confidence_score": np.random.uniform(0.7, 0.95),
                "tumor_volume": np.random.uniform(800, 2000),
                "model_used": request.model_name,
                "inference_time": datetime.now().isoformat()
            }
        }
        results.append(result)
    
    return {
        "batch_id": batch_id,
        "status": "completed",
        "total_dicoms": len(request.dicom_ids),
        "results": results
    }


@app.get("/api/ai/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a batch prediction job"""
    # Mock implementation - in production, track actual batch jobs
    return {
        "batch_id": batch_id,
        "status": "completed",
        "progress": 100,
        "total_dicoms": 5,
        "completed_dicoms": 5,
        "start_time": datetime.now().isoformat(),
        "completion_time": datetime.now().isoformat()
    }


@app.post("/api/export/segmentation/{dicom_id}")
async def export_segmentation(dicom_id: str, file_format: str = "nifti"):
    """Export segmentation mask in specified format"""
    if dicom_id not in stored_dicoms:
        raise HTTPException(status_code=404, detail="DICOM not found")
    
    if file_format not in ["nifti", "dicom"]:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    # Mock export response
    return {
        "dicom_id": dicom_id,
        "format": file_format,
        "download_url": f"/api/download/segmentation/{dicom_id}.{file_format}",
        "file_size_bytes": 2048576,
        "export_time": datetime.now().isoformat()
    }


@app.get("/api/studies/{patient_id}")
async def get_patient_studies(patient_id: str):
    """Get all studies for a patient"""
    # Filter stored DICOMs by patient ID
    patient_studies = []
    
    for dicom_id, dicom_data in stored_dicoms.items():
        if dicom_data["metadata"]["patient_id"] == patient_id:
            patient_studies.append({
                "dicom_id": dicom_id,
                "study_date": dicom_data["metadata"]["study_date"],
                "modality": dicom_data["metadata"]["modality"],
                "series_description": dicom_data["metadata"]["series_description"],
                "upload_time": dicom_data["upload_time"]
            })
    
    return {
        "patient_id": patient_id,
        "total_studies": len(patient_studies),
        "studies": patient_studies
    }


@app.get("/api/compare/{dicom_id1}/{dicom_id2}")
async def compare_studies(dicom_id1: str, dicom_id2: str):
    """Compare two studies for longitudinal analysis"""
    if dicom_id1 not in stored_dicoms or dicom_id2 not in stored_dicoms:
        raise HTTPException(status_code=404, detail="One or more DICOMs not found")
    
    study1 = stored_dicoms[dicom_id1]
    study2 = stored_dicoms[dicom_id2]
    
    # Mock comparison results
    return {
        "comparison_id": str(uuid.uuid4()),
        "study1": {
            "dicom_id": dicom_id1,
            "study_date": study1["metadata"]["study_date"],
            "tumor_volume": 1245.6
        },
        "study2": {
            "dicom_id": dicom_id2,
            "study_date": study2["metadata"]["study_date"],
            "tumor_volume": 1156.8
        },
        "changes": {
            "volume_change_mm3": -88.8,
            "volume_change_percent": -7.1,
            "response_assessment": "Partial Response"
        },
        "comparison_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "medical_imaging_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
