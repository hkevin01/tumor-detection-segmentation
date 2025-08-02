"""Integration tests for the Medical Imaging API endpoints."""

import pytest
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
import nibabel as nib
import pydicom
from datetime import datetime

@pytest.mark.integration
@pytest.mark.api
class TestMedicalImagingAPI:
    """Test cases for Medical Imaging API endpoints."""

    @pytest.fixture(scope="class")
    def test_image(self) -> io.BytesIO:
        """Create a test image for API testing."""
        # Create a simple test image
        img_array = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    def test_api_health(self, api_client: TestClient):
        """Test API health endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_analyze_standard_image(
        self,
        api_client: TestClient,
        test_image: io.BytesIO,
        test_metrics: "TestMetrics"
    ):
        """Test image analysis endpoint with standard image format."""
        start_time = datetime.now()
        
        files = {"file": ("test.png", test_image, "image/png")}
        response = api_client.post(
            "/api/analyze",
            files=files,
            params={"modality": "MRI"}
        )
        
        # Record execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        test_metrics.add_metric("execution_time", execution_time)
        
        assert response.status_code == 200
        result = response.json()
        assert "result_id" in result
        assert "prediction" in result
        
        # Add success metric
        test_metrics.add_metric("accuracy", 1.0)

    @pytest.mark.parametrize("format", ["nii.gz", "dcm"])
    def test_analyze_medical_formats(
        self,
        api_client: TestClient,
        test_config: dict,
        format: str,
        test_metrics: "TestMetrics"
    ):
        """Test image analysis endpoint with medical image formats."""
        sample_path = (
            test_config["test_data"]["mri_sample"]
            if format == "nii.gz"
            else test_config["test_data"]["ct_sample"]
        )
        
        with open(sample_path, "rb") as f:
            files = {"file": (f"test.{format}", f, f"application/{format}")}
            response = api_client.post(
                "/api/analyze",
                files=files,
                params={"modality": "MRI" if format == "nii.gz" else "CT"}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert "prediction" in result
        if format == "nii.gz":
            assert "tumor_volume" in result["prediction"]
        
        # Add metrics
        test_metrics.add_metric("accuracy", 1.0)

    def test_results_retrieval(
        self,
        api_client: TestClient,
        test_metrics: "TestMetrics"
    ):
        """Test retrieval of analysis results."""
        # First, analyze an image to get a result_id
        test_image = self.test_image()
        files = {"file": ("test.png", test_image, "image/png")}
        analyze_response = api_client.post(
            "/api/analyze",
            files=files,
            params={"modality": "MRI"}
        )
        
        result_id = analyze_response.json()["result_id"]
        
        # Now try to retrieve the results
        start_time = datetime.now()
        response = api_client.get(f"/api/results/{result_id}")
        
        # Record retrieval time
        retrieval_time = (datetime.now() - start_time).total_seconds()
        test_metrics.add_metric("execution_time", retrieval_time)
        
        assert response.status_code == 200
        result = response.json()
        assert "prediction" in result

    @pytest.mark.slow
    def test_concurrent_requests(
        self,
        api_client: TestClient,
        test_image: io.BytesIO,
        test_metrics: "TestMetrics"
    ):
        """Test handling of concurrent API requests."""
        import asyncio
        import aiohttp
        import time
        
        async def make_request(session, i):
            files = {"file": ("test.png", test_image, "image/png")}
            async with session.post(
                "http://localhost:8000/api/analyze",
                data={"file": test_image, "modality": "MRI"}
            ) as response:
                return await response.json()
        
        async def run_concurrent_requests():
            async with aiohttp.ClientSession() as session:
                tasks = [
                    make_request(session, i)
                    for i in range(5)  # Test with 5 concurrent requests
                ]
                start_time = time.time()
                responses = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                return responses, total_time
        
        responses, total_time = asyncio.run(run_concurrent_requests())
        
        # Add performance metrics
        test_metrics.add_metric("concurrent_execution_time", total_time)
        assert len(responses) == 5
        for response in responses:
            assert "result_id" in response
