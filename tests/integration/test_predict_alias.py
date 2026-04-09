"""Integration tests for ExportWorker CSV and FHIR outputs.

Replaces the former FastAPI predict-alias and overlay-PNG tests.
"""

from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pytest

from gui.workers import ExportWorker


_SAMPLE_RESULT = {
    "study_id": "integ-study-001",
    "model_id": "unet",
    "model": "unet",
    "prediction": "tumor_detected",
    "confidence": 0.88,
    "tumor_volume_voxels": 512.0,
    "class_volumes_cm3": {
        "necrotic_core_cm3": 0.30,
        "enhancing_tumour_cm3": 0.51,
        "peritumoral_edema_cm3": 1.20,
        "whole_tumour_cm3": 2.01,
    },
    "processing_time_seconds": 3.14,
    "mask_path": None,
    "device": "synthetic",
    "volume_shape": [64, 64, 64],
}


@pytest.mark.integration
def test_export_csv_contains_headers(tmp_path: Path) -> None:
    worker = ExportWorker(
        result=_SAMPLE_RESULT,
        export_dir=str(tmp_path),
        export_types=["csv"],
        patient_name="Alice",
    )
    csv_path = worker._export_csv()
    assert csv_path.exists()
    content = csv_path.read_text()
    assert "Metric" in content
    assert "Whole Tumour Volume" in content
    assert "2.01" in content


@pytest.mark.integration
def test_export_fhir_valid_bundle(tmp_path: Path) -> None:
    worker = ExportWorker(
        result=_SAMPLE_RESULT,
        export_dir=str(tmp_path),
        export_types=["fhir"],
        patient_name="Bob",
        patient_id="pat-001",
    )
    fhir_path = worker._export_fhir()
    assert fhir_path.exists()
    bundle = json.loads(fhir_path.read_text())
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    entries = bundle["entry"]
    resource_types = [e["resource"]["resourceType"] for e in entries]
    assert "Patient" in resource_types
    assert "DiagnosticReport" in resource_types
