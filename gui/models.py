"""
Pure Python data models for the tumor detection desktop application.
Replaces the FastAPI/SQLAlchemy-based models with dataclasses + sqlite3.
"""

import json
import sqlite3
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class StudyStatus(str, Enum):
    LOADED = "loaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Patient:
    name: str
    patient_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    medical_record_number: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Study:
    patient_id: str
    file_path: str
    modality: str = "MR"
    description: str = ""
    study_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    study_date: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = StudyStatus.LOADED.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PredictionResult:
    study_id: str
    model_id: str
    prediction: str
    confidence: float
    tumor_volume_voxels: float
    class_volumes_cm3: Dict[str, float] = field(default_factory=dict)
    processing_time_seconds: float = 0.0
    mask_path: Optional[str] = None
    device: str = "cpu"
    model: str = "unet"
    volume_shape: List[int] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class AppStorage:
    """Thread-safe in-memory storage with SQLite persistence."""

    def __init__(self, db_path: str = "tumor_detection.db"):
        self._lock = threading.Lock()
        self._patients: Dict[str, Patient] = {}
        self._studies: Dict[str, Study] = {}
        self._results: Dict[str, PredictionResult] = {}
        self._db_path = str(db_path)
        self._init_db()
        self._load_from_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY, data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS studies (
                    id TEXT PRIMARY KEY, data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY, study_id TEXT NOT NULL, data TEXT NOT NULL
                );
            """)

    def _load_from_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            for (data,) in conn.execute("SELECT data FROM patients"):
                d = json.loads(data)
                self._patients[d["patient_id"]] = Patient(**d)
            for (data,) in conn.execute("SELECT data FROM studies"):
                d = json.loads(data)
                self._studies[d["study_id"]] = Study(**d)
            for (data,) in conn.execute("SELECT data FROM results"):
                d = json.loads(data)
                # Drop keys added after initial schema if present
                d.pop("volume", None)
                d.pop("mask", None)
                d.pop("affine", None)
                self._results[d["result_id"]] = PredictionResult(**d)

    def _persist_patient(self, p: Patient) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO patients VALUES (?, ?)",
                (p.patient_id, json.dumps(asdict(p))),
            )

    def _persist_study(self, s: Study) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO studies VALUES (?, ?)",
                (s.study_id, json.dumps(asdict(s))),
            )

    def _persist_result(self, r: PredictionResult) -> None:
        d = asdict(r)
        # Never persist numpy arrays or large blobs
        for key in ("volume", "mask", "affine"):
            d.pop(key, None)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO results VALUES (?, ?, ?)",
                (r.result_id, r.study_id, json.dumps(d)),
            )

    # --- public API ---

    def add_patient(self, patient: Patient) -> Patient:
        with self._lock:
            self._patients[patient.patient_id] = patient
            self._persist_patient(patient)
        return patient

    def add_study(self, study: Study) -> Study:
        with self._lock:
            self._studies[study.study_id] = study
            self._persist_study(study)
        return study

    def update_study_status(self, study_id: str, status: StudyStatus) -> None:
        with self._lock:
            if study_id in self._studies:
                self._studies[study_id].status = status.value
                self._persist_study(self._studies[study_id])

    def add_result(self, result: PredictionResult) -> PredictionResult:
        with self._lock:
            self._results[result.result_id] = result
            self._persist_result(result)
        return result

    def get_patients(self) -> List[Patient]:
        with self._lock:
            return list(self._patients.values())

    def get_studies(self, patient_id: Optional[str] = None) -> List[Study]:
        with self._lock:
            studies = list(self._studies.values())
            if patient_id:
                studies = [s for s in studies if s.patient_id == patient_id]
            return studies

    def get_result_for_study(self, study_id: str) -> Optional[PredictionResult]:
        with self._lock:
            for r in self._results.values():
                if r.study_id == study_id:
                    return r
        return None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_storage: Optional[AppStorage] = None


def get_storage() -> AppStorage:
    global _storage
    if _storage is None:
        _storage = AppStorage()
    return _storage
