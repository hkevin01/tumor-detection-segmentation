"""Integration test for JSON alias prediction endpoint.

Creates a synthetic study backed by a .npy volume, triggers prediction using
POST /api/ai/predict with a JSON body, then fetches the overlay PNG.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_ai_predict_alias_then_overlay(tmp_path: Path):
    from gui.backend.api.routes import get_router  # type: ignore
    from gui.backend.models import get_storage  # type: ignore

    app = FastAPI()
    app.include_router(get_router(), prefix="/api")
    client = TestClient(app)

    # Prepare a small 3D numpy volume and register a study
    vol = np.random.rand(16, 16, 16).astype(np.float32)
    vol_path = tmp_path / "study.npy"
    np.save(vol_path, vol)

    storage = get_storage()
    patient_id = storage.add_patient({"name": "Alias Patient"})
    study_id = storage.add_study({
        "patient_id": patient_id,
        "study_date": "2025-01-01",
        "modality": "MR",
        "description": "Alias study",
        "file_path": str(vol_path),
    })

    # Trigger prediction using alias endpoint
    resp = client.post(
        "/api/ai/predict",
        json={"study_id": study_id, "model_name": "unet_v1"},
    )
    assert resp.status_code == 200

    # Poll briefly for completion if background used in future
    t0 = time.time()
    while time.time() - t0 < 5:
        status = storage.studies[study_id]["status"]
        if (
            str(status) == "completed"
            or getattr(status, "name", "").lower() == "completed"
        ):
            break
        time.sleep(0.1)

    # Fetch overlay PNG
    oresp = client.get(
        f"/api/studies/{study_id}/overlay?alpha=0.5&cmap=plasma"
    )
    assert oresp.status_code == 200
    assert oresp.headers.get("content-type") == "image/png"
    assert oresp.content and len(oresp.content) > 100
