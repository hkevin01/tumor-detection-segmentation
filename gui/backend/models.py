"""
Database models for the tumor detection application.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json

try:
    from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Fallback base class if SQLAlchemy not available
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
else:
    class Base:
        pass


class StudyStatus(str, Enum):
    """Study processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Patient(Base):
    """Patient information model."""
    
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "patients"
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        date_of_birth = Column(DateTime)
        gender = Column(String(1))
        medical_record_number = Column(String, unique=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow)


class Study(Base):
    """Medical study model."""
    
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "studies"
        
        id = Column(String, primary_key=True)
        patient_id = Column(String, nullable=False)
        study_date = Column(DateTime, nullable=False)
        modality = Column(String(10), nullable=False)  # CT, MR, etc.
        description = Column(Text)
        status = Column(String(20), default=StudyStatus.UPLOADED)
        file_path = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow)


class PredictionResult(Base):
    """AI prediction results model."""
    
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "prediction_results"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        study_id = Column(String, nullable=False)
        model_id = Column(String, nullable=False)
        prediction = Column(String, nullable=False)  # tumor_detected, no_tumor
        confidence = Column(Float)
        tumor_volume = Column(Float)
        coordinates = Column(Text)  # JSON string of coordinates
        processing_time = Column(Float)
        created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """Clinical report model."""
    
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "reports"
        
        id = Column(String, primary_key=True)
        study_id = Column(String, nullable=False)
        template = Column(String, nullable=False)
        findings = Column(Text)  # JSON string of findings
        recommendations = Column(Text)
        report_path = Column(String)
        generated_by = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)


class AIModel(Base):
    """AI model metadata."""
    
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "ai_models"
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text)
        version = Column(String)
        accuracy = Column(Float)
        file_path = Column(String, nullable=False)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)


# Database connection functions
class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str = "sqlite:///tumor_detection.db"):
        """Initialize database connection."""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy not available. Install with: pip install sqlalchemy"
            )
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Pydantic models for API validation (if pydantic available)
try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    
    # Fallback BaseModel
    class BaseModel:
        pass


class PatientCreate(BaseModel):
    """Patient creation schema."""
    if PYDANTIC_AVAILABLE:
        name: str
        date_of_birth: Optional[datetime] = None
        gender: Optional[str] = None
        medical_record_number: Optional[str] = None


class StudyCreate(BaseModel):
    """Study creation schema."""
    if PYDANTIC_AVAILABLE:
        patient_id: str
        study_date: datetime
        modality: str
        description: Optional[str] = None
        file_path: Optional[str] = None


class PredictionRequest(BaseModel):
    """Prediction request schema."""
    if PYDANTIC_AVAILABLE:
        study_id: str
        model_id: str = "unet_v1"


class ReportRequest(BaseModel):
    """Report generation request schema."""
    if PYDANTIC_AVAILABLE:
        study_id: str
        template: str = "standard"


# In-memory storage for when database is not available
class InMemoryStorage:
    """Simple in-memory storage for development."""
    
    def __init__(self):
        self.patients = {}
        self.studies = {}
        self.predictions = {}
        self.reports = {}
        self.models = {
            "unet_v1": {
                "id": "unet_v1",
                "name": "UNet Tumor Segmentation v1.0",
                "description": "Standard UNet architecture for tumor segmentation",
                "version": "1.0",
                "accuracy": 0.92,
                "file_path": "./models/unet_v1.pth",
                "is_active": True,
                "created_at": datetime.now()
            },
            "unet_v2": {
                "id": "unet_v2",
                "name": "UNet Tumor Segmentation v2.0",
                "description": "Enhanced UNet with attention mechanisms",
                "version": "2.0",
                "accuracy": 0.94,
                "file_path": "./models/unet_v2.pth",
                "is_active": True,
                "created_at": datetime.now()
            }
        }
    
    def add_patient(self, patient_data: Dict[str, Any]) -> str:
        """Add patient to storage."""
        patient_id = f"patient_{len(self.patients) + 1:03d}"
        patient_data["id"] = patient_id
        patient_data["created_at"] = datetime.now()
        self.patients[patient_id] = patient_data
        return patient_id
    
    def add_study(self, study_data: Dict[str, Any]) -> str:
        """Add study to storage."""
        study_id = f"study_{len(self.studies) + 1:03d}"
        study_data["id"] = study_id
        study_data["created_at"] = datetime.now()
        study_data["status"] = StudyStatus.UPLOADED
        self.studies[study_id] = study_data
        return study_id
    
    def add_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """Add prediction result to storage."""
        prediction_id = len(self.predictions) + 1
        prediction_data["id"] = prediction_id
        prediction_data["created_at"] = datetime.now()
        self.predictions[prediction_id] = prediction_data
        return prediction_id
    
    def add_report(self, report_data: Dict[str, Any]) -> str:
        """Add report to storage."""
        report_id = f"report_{len(self.reports) + 1:03d}"
        report_data["id"] = report_id
        report_data["created_at"] = datetime.now()
        self.reports[report_id] = report_data
        return report_id
    
    def get_studies(self, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get studies, optionally filtered by patient ID."""
        studies = list(self.studies.values())
        if patient_id:
            studies = [s for s in studies if s.get("patient_id") == patient_id]
        return studies
    
    def get_models(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get AI models."""
        models = list(self.models.values())
        if active_only:
            models = [m for m in models if m.get("is_active", True)]
        return models
    
    def update_study_status(self, study_id: str, status: StudyStatus):
        """Update study status."""
        if study_id in self.studies:
            self.studies[study_id]["status"] = status
            self.studies[study_id]["updated_at"] = datetime.now()


# Global storage instance
storage = InMemoryStorage()


def get_storage():
    """Get storage instance."""
    return storage
