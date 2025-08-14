#!/usr/bin/env python3
"""
FastAPI Backend for Medical Imaging GUI
Connects the frontend DICOM viewer with MONAI-based AI models
"""

import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Try importing optional dependencies
try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

import importlib.util as _importlib_util  # type: ignore

SIMPLEITK_AVAILABLE = _importlib_util.find_spec("SimpleITK") is not None

# Import our medical AI backend (optional)
try:
    from .medical_ai_backend import MedicalImagingAI  # type: ignore
except ImportError:  # pragma: no cover
    MedicalImagingAI = None  # type: ignore

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

# In-memory storage for demo (use a database in production)
stored_dicoms: Dict[str, Dict[str, Any]] = {}


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
    try:
        if 'MedicalImagingAI' in globals() and MedicalImagingAI is not None:
            app.state.ai_backend = MedicalImagingAI()  # type: ignore[misc]
            logger.info("Medical Imaging AI backend initialized successfully")
        else:
            app.state.ai_backend = None
            logger.warning(
                "MedicalImagingAI backend not available; running in demo mode"
            )
    except (RuntimeError, ImportError, OSError) as e:  # pragma: no cover
        logger.error("Failed to initialize AI backend: %s", str(e))
        app.state.ai_backend = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Medical Imaging AI API",
        "status": "online",
        "ai_backend_available": (
            getattr(app.state, "ai_backend", None) is not None
        ),
        "pydicom_available": PYDICOM_AVAILABLE,
        "simpleitk_available": SIMPLEITK_AVAILABLE
    }


@app.get("/health")
async def health():
    """Alias for root health check"""
    return await root()


@app.get("/api/health")
async def api_health():
    """Alias for root health check under /api prefix"""
    return await root()


# Optional: serve manifest.json if present
@app.get("/manifest.json")
async def manifest():
    """Serve frontend manifest file if built"""
    possible_paths = [
        os.path.join(os.getcwd(), "frontend", "public", "manifest.json"),
        os.path.join(os.getcwd(), "frontend", "manifest.json"),
    ]
    for manifest_path in possible_paths:
        if os.path.isfile(manifest_path):
            return FileResponse(manifest_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Manifest not found")


@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models"""
    if getattr(app.state, "ai_backend", None) is None:
        raise HTTPException(status_code=503, detail="AI backend not available")

    try:
        backend = app.state.ai_backend
        model_info = backend.get_model_info()
        available_models = list(backend.config["models"].keys())

        return {
            "available_models": available_models,
            "loaded_models": list(model_info.keys()),
            "model_details": model_info
        }
    except (RuntimeError, ValueError, KeyError) as e:
        logger.error("Error getting model info: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/models/{model_name}/load")
async def load_model(model_name: str, checkpoint_path: Optional[str] = None):
    """Load a specific AI model"""
    if getattr(app.state, "ai_backend", None) is None:
        raise HTTPException(status_code=503, detail="AI backend not available")

    try:
        model = app.state.ai_backend.load_model(model_name, checkpoint_path)
        return {
            "message": f"Model {model_name} loaded successfully",
            "model_info": {
                "name": model_name,
                "architecture": model.__class__.__name__,
                "parameters": sum(p.numel() for p in model.parameters()),
                "device": str(next(model.parameters()).device)
            }
        }
    except (RuntimeError, OSError, ValueError) as e:
        logger.error("Error loading model %s: %s", model_name, str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.dcm'
        ) as tmp_file:
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
                "series_description": getattr(
                    dicom, 'SeriesDescription', 'Unknown'
                ),
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

    except (RuntimeError, OSError, ValueError) as e:
        logger.error("Error processing DICOM upload: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"DICOM processing failed: {str(e)}",
        ) from e


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
    if getattr(app.state, "ai_backend", None) is None:
        raise HTTPException(status_code=503, detail="AI backend not available")

    if request.dicom_id not in stored_dicoms:
        raise HTTPException(status_code=404, detail="DICOM not found")

    try:
        dicom_data: Dict[str, Any] = stored_dicoms[request.dicom_id]

        # For demo purposes, return mock prediction
        # In real implementation, this would call ai_backend.predict_tumor()
        mask_depth = 128
        mask_height = 128
        mask_width = 64
        mock_prediction = {
            "segmentation_mask": [
                [
                    [0.0 for _ in range(mask_width)]
                    for _ in range(mask_height)
                ]
                for _ in range(mask_depth)
            ],
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
        mask: List[List[List[float]]] = mock_prediction["segmentation_mask"]
        for z in range(23, 67):
            for y in range(67, 112):
                for x in range(45, 64):
                    val = (x - 56) ** 2 + (y - 89) ** 2 + (z - 45) ** 2
                    if val < 20 ** 2:
                        mask[z][y][x] = 1.0

        return mock_prediction

    except Exception as e:
        logger.error("Error running prediction: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/ai/batch-predict")
async def batch_predict(request: BatchPredictionRequest):
    """Run batch tumor prediction on multiple DICOM images"""
    if getattr(app.state, "ai_backend", None) is None:
        raise HTTPException(status_code=503, detail="AI backend not available")

    # Validate all DICOM IDs exist
    missing_ids = [
        dicom_id
        for dicom_id in request.dicom_ids
        if dicom_id not in stored_dicoms
    ]

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"DICOMs not found: {missing_ids}",
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


@app.post("/api/ai/infer-overlay")
async def infer_overlay(
    file: UploadFile = File(...),
    model_path: Optional[str] = None,
    config_path: Optional[str] = None,
    device: str = "auto",
):
    """Run inference on an uploaded image and return an overlay PNG.

    If model/config are not provided, a tiny UNet with random weights is
    created dynamically for demonstration purposes.
    """
    try:
        # Lazy imports to avoid module-level lints and optional deps
        from .inference.inference import TumorPredictor  # type: ignore
        from .utils.visualization import save_overlay  # type: ignore
    except ImportError:
        try:
            from src.inference.inference import TumorPredictor  # type: ignore
            from src.utils.visualization import save_overlay  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise HTTPException(
                status_code=503,
                detail=f"Inference utilities unavailable: {e}",
            ) from e

    # Determine suffix from filename
    fname = file.filename or ""
    suffix = ".npy"
    lower = fname.lower()
    if lower.endswith((".nii", ".nii.gz")):
        suffix = ".nii.gz"
    elif lower.endswith(".dcm"):
        suffix = ".dcm"
    elif lower.endswith(".npy"):
        suffix = ".npy"

    # Persist upload to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        in_path = tmp_in.name

    # Prepare model and config if not provided
    try:
        if not model_path or not config_path:
            import json as _json

            import torch as _torch

            from .training.trainer import \
                create_model as _create_model  # type: ignore

            cfg = {
                "model_type": "unet",
                "dimensions": 3,
                "in_channels": 1,
                "out_channels": 2,
                "channels": [8, 16],
                "strides": [2],
                "num_res_units": 1,
                "image_size": [16, 16, 16],
            }
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".json"
            ) as tmp_cfg:
                tmp_cfg.write(_json.dumps(cfg).encode("utf-8"))
                config_path = tmp_cfg.name

            model = _create_model(cfg)
            ckpt = {"model_state_dict": model.state_dict()}
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".pth"
            ) as tmp_mdl:
                _torch.save(ckpt, tmp_mdl.name)
                model_path = tmp_mdl.name

        predictor = TumorPredictor(
            model_path=model_path, config_path=config_path, device=device
        )
        result = predictor.predict_single(in_path)
        pred = result["prediction"]
        base = result["input_image"]

        # Save overlay to temp PNG and return
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".png"
        ) as tmp_png:
            png_path = tmp_png.name
        save_overlay(base, pred, png_path, strategy="middle")
        return FileResponse(
            png_path, media_type="image/png", filename="overlay.png"
        )
    except (RuntimeError, ValueError, OSError) as e:  # pragma: no cover
        logger.exception("Inference failed")
        raise HTTPException(
            status_code=500, detail=f"Inference failed: {e}"
        ) from e


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
                "series_description": dicom_data["metadata"][
                    "series_description"
                ],
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
        raise HTTPException(
            status_code=404,
            detail="One or more DICOMs not found",
        )

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
