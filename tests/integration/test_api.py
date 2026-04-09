"""Integration tests for the desktop application data models.

Replaces the former FastAPI endpoint tests now that the backend has been
migrated to a PyQt6 desktop application with no HTTP server.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gui.models import AppStorage, Patient, Study, PredictionResult, StudyStatus


@pytest.mark.integration
class TestAppStorageIntegration:
    """Verify AppStorage CRUD round-trips through SQLite."""

    def test_add_and_retrieve_patient(self, tmp_path: Path) -> None:
        storage = AppStorage(db_path=str(tmp_path / "test.db"))
        patient = Patient(name="Alice")
        storage.add_patient(patient)
        assert any(p.patient_id == patient.patient_id for p in storage.get_patients())

    def test_add_and_retrieve_study(self, tmp_path: Path) -> None:
        storage = AppStorage(db_path=str(tmp_path / "test.db"))
        patient = Patient(name="Bob")
        storage.add_patient(patient)
        study = Study(patient_id=patient.patient_id, file_path="/data/scan.nii.gz")
        storage.add_study(study)
        studies = storage.get_studies(patient_id=patient.patient_id)
        assert len(studies) == 1
        assert studies[0].file_path == "/data/scan.nii.gz"

    def test_update_study_status(self, tmp_path: Path) -> None:
        storage = AppStorage(db_path=str(tmp_path / "test.db"))
        patient = Patient(name="Carol")
        storage.add_patient(patient)
        study = Study(patient_id=patient.patient_id, file_path="/data/scan.nii.gz")
        storage.add_study(study)
        storage.update_study_status(study.study_id, StudyStatus.COMPLETED)
        studies = storage.get_studies()
        updated = next(s for s in studies if s.study_id == study.study_id)
        assert updated.status == StudyStatus.COMPLETED.value

    def test_add_and_retrieve_result(self, tmp_path: Path) -> None:
        storage = AppStorage(db_path=str(tmp_path / "test.db"))
        patient = Patient(name="Dave")
        storage.add_patient(patient)
        study = Study(patient_id=patient.patient_id, file_path="/data/scan.nii.gz")
        storage.add_study(study)
        result = PredictionResult(
            study_id=study.study_id,
            model_id="unet",
            prediction="tumor_detected",
            confidence=0.91,
            tumor_volume_voxels=1234.0,
            class_volumes_cm3={"whole_tumour_cm3": 1.23},
        )
        storage.add_result(result)
        retrieved = storage.get_result_for_study(study.study_id)
        assert retrieved is not None
        assert retrieved.prediction == "tumor_detected"
        assert abs(retrieved.confidence - 0.91) < 1e-6


