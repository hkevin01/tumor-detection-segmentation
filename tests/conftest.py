"""Test utilities and fixtures for the medical imaging project."""

import os
import json
import logging
import pytest
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, Generator
import nibabel as nib
import pydicom
from fastapi.testclient import TestClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler('logs/test_logs/test_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_test_config() -> Dict[str, Any]:
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / 'test_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Pytest fixture for test configuration."""
    return load_test_config()

@pytest.fixture(scope="session")
def test_device() -> torch.device:
    """Get the appropriate device for testing."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

@pytest.fixture(scope="session")
def sample_mri(test_config: Dict[str, Any]) -> np.ndarray:
    """Load sample MRI data for testing."""
    mri_path = test_config["test_data"]["mri_sample"]
    try:
        nifti_img = nib.load(mri_path)
        return nifti_img.get_fdata()
    except Exception as e:
        logger.error(f"Failed to load sample MRI: {e}")
        raise

@pytest.fixture(scope="session")
def sample_ct(test_config: Dict[str, Any]) -> np.ndarray:
    """Load sample CT data for testing."""
    ct_path = test_config["test_data"]["ct_sample"]
    try:
        dcm = pydicom.dcmread(ct_path)
        return dcm.pixel_array
    except Exception as e:
        logger.error(f"Failed to load sample CT: {e}")
        raise

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
            logger.info(f"{metric}: {value:.4f}")

@pytest.fixture(scope="session")
def test_metrics() -> TestMetrics:
    """Pytest fixture for test metrics tracking."""
    return TestMetrics()
