"""Test utilities and fixtures for the medical imaging project.

Enhancements:
- Ensure the logs directory exists before configuring file logging.
- Make sample data fixtures robust: if configured test files are missing,
  fall back to generating small synthetic arrays so tests can run without
  external data assets.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator

import numpy as np
import pydicom
import pytest
import torch
from fastapi.testclient import TestClient
from nibabel.loadsave import load as nib_load

# Ensure logs directory exists and set up logging
log_dir = Path('logs/test_logs')
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'test_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_test_config() -> Dict[str, Any]:
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / 'test_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session", name="test_config")
def _test_config() -> Dict[str, Any]:
    """Pytest fixture for test configuration."""
    return load_test_config()


@pytest.fixture(scope="session")
def test_device() -> torch.device:
    """Get the appropriate device for testing."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@pytest.fixture(scope="session")
def sample_mri(test_config: Dict[str, Any]) -> np.ndarray:  # noqa: F811
    """Load sample MRI data for testing."""
    mri_path = test_config["test_data"]["mri_sample"]
    try:
        mri_file = Path(mri_path)
        if mri_file.exists():
            nifti_img = nib_load(str(mri_file))
            return nifti_img.get_fdata()  # type: ignore[attr-defined]
        # Fallback: generate a small synthetic 3D volume
        logger.warning(
            "MRI sample not found; generating synthetic volume for tests"
        )
        return np.random.rand(32, 32, 32).astype(np.float32)
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to load or synthesize sample MRI: %s", e)
        # Final fallback to avoid test crashes
        return np.random.rand(16, 16, 16).astype(np.float32)


@pytest.fixture(scope="session")
def sample_ct(test_config: Dict[str, Any]) -> np.ndarray:  # noqa: F811
    """Load sample CT data for testing."""
    ct_path = test_config["test_data"]["ct_sample"]
    try:
        ct_file = Path(ct_path)
        if ct_file.exists():
            dcm = pydicom.dcmread(str(ct_file))
            return dcm.pixel_array
        # Fallback: generate a small synthetic 2D slice
        logger.warning(
            "CT sample not found; generating synthetic slice for tests"
        )
        return (np.random.rand(64, 64) * 1000).astype(np.float32)
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("Failed to load or synthesize sample CT: %s", e)
        # Final fallback to avoid test crashes
        return (np.random.rand(32, 32) * 1000).astype(np.float32)


@pytest.fixture(scope="function")
def api_client() -> Generator:
    """Create a test client for the FastAPI application."""
    from src.medical_imaging_api import app
    with TestClient(app) as client:
        yield client


class TestMetrics:
    """Class for tracking and logging test metrics."""

    def __init__(self):
        self.metrics = {
            "execution_time": [],
            "memory_usage": [],
            "accuracy": [],
            "dice_scores": []
        }

    def add_metric(self, metric_name: str, value: float):
        """Add a metric value to tracking."""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)

    def get_summary(self) -> Dict[str, float]:
        """Get summary statistics of tracked metrics."""
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[f"{name}_mean"] = np.mean(values)
                summary[f"{name}_std"] = np.std(values)
                summary[f"{name}_min"] = np.min(values)
                summary[f"{name}_max"] = np.max(values)
        return summary

    def log_summary(self):
        """Log summary statistics to file."""
        summary = self.get_summary()
        logger.info("Test Metrics Summary:")
        for metric, value in summary.items():
            logger.info("%s: %s", metric, f"{value:.4f}")


@pytest.fixture(scope="session")
def test_metrics() -> TestMetrics:
    """Pytest fixture for test metrics tracking."""
    return TestMetrics()
    return TestMetrics()
