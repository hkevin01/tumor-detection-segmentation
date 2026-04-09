"""Integration tests for the InferenceWorker synthetic segmentation.

Replaces the former FastAPI overlay-PNG endpoint tests. Verifies that the
desktop worker produces a valid 3-class integer mask without any ML deps.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from gui.workers import InferenceWorker


@pytest.mark.integration
def test_synthetic_mask_classes(tmp_path: Path) -> None:
    """InferenceWorker._synthetic_mask must contain classes 1, 2, and 3."""
    worker = InferenceWorker(file_path=str(tmp_path / "dummy.nii"), study_id="test-001")
    volume = np.zeros((32, 32, 32), dtype=np.float32)
    mask = worker._synthetic_mask(volume)
    assert mask.shape == volume.shape
    assert set(np.unique(mask)).issuperset({0, 1, 2, 3})


@pytest.mark.integration
def test_class_volumes_positive(tmp_path: Path) -> None:
    """Class volumes must be positive for a non-empty mask."""
    worker = InferenceWorker(file_path=str(tmp_path / "dummy.nii"), study_id="test-002")
    volume = np.zeros((32, 32, 32), dtype=np.float32)
    mask = worker._synthetic_mask(volume)
    vols = worker._class_volumes(mask, vox_mm3=1.0)
    assert vols["whole_tumour_cm3"] > 0
    assert vols["enhancing_tumour_cm3"] > 0


@pytest.mark.integration
def test_save_mask_creates_file(tmp_path: Path) -> None:
    """_save_mask must write a file to the masks directory."""
    worker = InferenceWorker(file_path=str(tmp_path / "dummy.nii"), study_id="test-003")
    import os; os.chdir(tmp_path)  # keep masks/ inside tmp_path
    mask = np.zeros((16, 16, 16), dtype=np.int32)
    mask[8, 8, 8] = 1
    affine = np.eye(4)
    saved = worker._save_mask(mask, affine, "test-003")
    assert saved.exists()
    assert saved.stat().st_size > 0
