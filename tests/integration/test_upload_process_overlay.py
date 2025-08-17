"""End-to-end integration: upload -> background process -> overlay.

This test uses the GUI backend router directly, uploads a small .dcm-like file
(using .dicom extension), waits briefly for background processing, then requests
an overlay PNG and validates the response.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.timeout(20)
def test_upload_process_overlay_e2e(tmp_path: Path, monkeypatch):
    # Build app with router
    from gui.backend.api.routes import get_router  # type: ignore
    from gui.backend.models import get_storage  # type: ignore

    app = FastAPI()
    app.include_router(get_router(), prefix="/api")
    client = TestClient(app)

    # Create a small synthetic volume and save as .npy, but upload as .dicom bytes
    vol = (np.random.rand(16, 16, 16)).astype(np.float32)
    vol_path = tmp_path / "vol.npy"
    np.save(vol_path, vol)
    # For upload, DICOM alias requires .dicom extension; send .dicom filename
    data = vol.tobytes()

    files = {"dicom_file": ("test.dicom", data, "application/octet-stream")}
    resp = client.post("/api/dicom/upload", files=files)
    assert resp.status_code == 200
    payload = resp.json()
    study_id = payload["study_id"]

    # Allow background processing to complete; poll study status
    storage = get_storage()
    t0 = time.time()
    while time.time() - t0 < 10:
        status = storage.studies[study_id]["status"]
        if str(status) == "completed" or status.name.lower() == "completed":
            break
        time.sleep(0.2)

    # Request overlay
    oresp = client.get(f"/api/studies/{study_id}/overlay")
    assert oresp.status_code == 200
    assert oresp.headers.get("content-type") == "image/png"
    assert oresp.content and len(oresp.content) > 100
