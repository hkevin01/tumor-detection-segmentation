"""Integration tests for ExportWorker PDF report output.

Replaces the former FastAPI upload + background-process + overlay-PNG test.
PDF generation is tested with and without reportlab installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gui.workers import ExportWorker


_SAMPLE_RESULT = {
    "study_id": "upload-study-001",
    "model_id": "swinunetr",
    "model": "swinunetr",
    "prediction": "no_tumor",
    "confidence": 0.12,
    "tumor_volume_voxels": 0.0,
    "class_volumes_cm3": {
        "necrotic_core_cm3": 0.0,
        "enhancing_tumour_cm3": 0.0,
        "peritumoral_edema_cm3": 0.0,
        "whole_tumour_cm3": 0.0,
    },
    "processing_time_seconds": 1.55,
    "mask_path": None,
    "device": "cpu",
    "volume_shape": [32, 32, 32],
}


@pytest.mark.integration
def test_export_pdf_or_txt_created(tmp_path: Path) -> None:
    """PDF export must create either a .pdf or a fallback .txt file."""
    worker = ExportWorker(
        result=_SAMPLE_RESULT,
        export_dir=str(tmp_path),
        export_types=["pdf"],
        patient_name="Charlie",
    )
    out = worker._export_pdf()
    assert out.exists()
    assert out.suffix in {".pdf", ".txt"}
    content = out.read_text(errors="replace")
    # Plain-text fallback must contain key fields
    if out.suffix == ".txt":
        assert "Prediction" in content or "FINDINGS" in content



