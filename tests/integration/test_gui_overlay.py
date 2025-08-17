"""Integration test for GUI backend overlay endpoint.

This test registers a synthetic study and a corresponding prediction with a
stored mask file, then requests the overlay PNG to validate real mask wiring.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.mark.integration
def test_gui_study_overlay_png(tmp_path: Path):
    # Import router and storage directly to avoid spinning the whole app
    # and to keep the test lightweight.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from gui.backend.api.routes import get_router  # type: ignore
    from gui.backend.models import get_storage  # type: ignore

    app = FastAPI()
    app.include_router(get_router(), prefix="/api")

    # Prepare a tiny 3D base volume and save to disk
    base = (np.random.rand(16, 16, 16)).astype(np.float32)
    base_path = tmp_path / "study_base.npy"
    np.save(base_path, base)

    # Register a study pointing to the saved base volume
    storage = get_storage()
    patient_id = storage.add_patient({"name": "Test Patient"})
    study_id = storage.add_study({
        "patient_id": patient_id,
        "study_date": "2025-01-01",
        "modality": "MR",
        "description": "Synthetic study",
        "file_path": str(base_path),
    })

    # Create a tiny spherical-ish mask and save it
    zz, yy, xx = np.indices(base.shape)
    center = np.array(base.shape) // 2
    rad2 = 3 ** 2
    mask = (((zz - center[0]) ** 2 + (yy - center[1]) ** 2 + (xx - center[2]) ** 2) <= rad2).astype(np.float32)
    mask_path = tmp_path / "mask.npy"
    np.save(mask_path, mask)

    # Register a prediction with a mask_path
    storage.add_prediction({
        "study_id": study_id,
        "prediction": "tumor_detected",
        "confidence": 0.9,
        "mask_path": str(mask_path),
        "model_used": "unet_v1",
    })

    client = TestClient(app)
    resp = client.get(f"/api/studies/{study_id}/overlay")
    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "image/png"
    assert resp.content and len(resp.content) > 100
