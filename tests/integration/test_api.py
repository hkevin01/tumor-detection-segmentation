"""Integration tests for the Medical Imaging API endpoints (updated)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestMedicalImagingAPI:
    def test_api_health(self, api_client: TestClient):
        """Test API health endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

    def test_infer_overlay_returns_png(
        self, api_client: TestClient, tmp_path: Path
    ):
        """Upload a tiny .npy volume and expect a PNG overlay in response."""
        vol = (np.random.rand(16, 16, 16)).astype(np.float32)
        in_path = tmp_path / "tiny.npy"
        np.save(in_path, vol)

        with open(in_path, "rb") as f:
            files = {"file": ("tiny.npy", f, "application/octet-stream")}
            resp = api_client.post("/api/ai/infer-overlay", files=files)

        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "image/png"
        assert resp.content and len(resp.content) > 100
