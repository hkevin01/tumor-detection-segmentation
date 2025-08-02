"""Performance tests for the Medical Imaging system."""

import pytest
import time
import numpy as np
import torch
from typing import Dict, Any
import psutil
import os
from src.data_preprocessing import MedicalImagePreprocessor
from src.inference.inference import predict_tumor

@pytest.mark.performance
class TestSystemPerformance:
    """Performance test cases for the Medical Imaging system."""

    @pytest.fixture(scope="class")
    def large_dataset(self) -> np.ndarray:
        """Create a large dataset for performance testing."""
        return np.random.rand(100, 256, 256, 256)

    def test_preprocessing_performance(
        self,
        large_dataset: np.ndarray,
        test_metrics: "TestMetrics"
    ):
        """Test preprocessing performance with large datasets."""
        preprocessor = MedicalImagePreprocessor()
        
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss
        
        # Process multiple images
        for i in range(min(10, len(large_dataset))):
            result = preprocessor.preprocess_image(
                large_dataset[i],
                modality="MRI"
            )
            assert result is not None
        
        execution_time = time.time() - start_time
        memory_used = (psutil.Process().memory_info().rss - memory_start) / 1024 / 1024  # MB
        
        # Record metrics
        test_metrics.add_metric("execution_time", execution_time)
        test_metrics.add_metric("memory_usage", memory_used)
        
        # Performance assertions
        assert execution_time < 30.0, "Preprocessing took too long"
        assert memory_used < 4096, "Memory usage too high"

    @pytest.mark.gpu
    def test_model_inference_performance(
        self,
        test_config: Dict[str, Any],
        test_metrics: "TestMetrics"
    ):
        """Test model inference performance."""
        if not torch.cuda.is_available():
            pytest.skip("GPU not available")
        
        # Load model
        model_path = test_config["model_paths"]["tumor_detection"]
        test_input = torch.randn(1, 1, 128, 128, 128).cuda()
        
        # Warmup
        with torch.no_grad():
            for _ in range(5):
                predict_tumor(test_input)
        
        # Measure performance
        start_time = time.time()
        torch.cuda.reset_peak_memory_stats()
        
        with torch.no_grad():
            for _ in range(100):  # Test with 100 inferences
                prediction = predict_tumor(test_input)
                assert prediction is not None
        
        execution_time = time.time() - start_time
        gpu_memory = torch.cuda.max_memory_allocated() / 1024 / 1024  # MB
        
        # Record metrics
        test_metrics.add_metric("gpu_inference_time", execution_time / 100)
        test_metrics.add_metric("gpu_memory_usage", gpu_memory)
        
        # Performance assertions
        assert execution_time / 100 < 0.1, "Inference too slow"
        assert gpu_memory < 8192, "GPU memory usage too high"

    def test_batch_processing_performance(
        self,
        large_dataset: np.ndarray,
        test_metrics: "TestMetrics"
    ):
        """Test batch processing performance."""
        preprocessor = MedicalImagePreprocessor()
        batch_sizes = [1, 4, 8, 16]
        
        for batch_size in batch_sizes:
            start_time = time.time()
            memory_start = psutil.Process().memory_info().rss
            
            # Process batch
            batch = large_dataset[:batch_size]
            results = []
            
            for img in batch:
                result = preprocessor.preprocess_image(img, modality="MRI")
                results.append(result)
            
            execution_time = time.time() - start_time
            memory_used = (psutil.Process().memory_info().rss - memory_start) / 1024 / 1024
            
            # Record metrics
            test_metrics.add_metric(f"batch_{batch_size}_time", execution_time)
            test_metrics.add_metric(f"batch_{batch_size}_memory", memory_used)
            
            # Performance assertions
            assert execution_time < batch_size * 5.0, f"Batch size {batch_size} too slow"

    @pytest.mark.slow
    def test_system_resource_usage(
        self,
        test_metrics: "TestMetrics"
    ):
        """Test overall system resource usage."""
        duration = 60  # Test for 1 minute
        start_time = time.time()
        measurements = []
        
        while time.time() - start_time < duration:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            measurements.append((cpu_percent, memory_percent))
            time.sleep(5)
        
        # Calculate averages
        avg_cpu = np.mean([m[0] for m in measurements])
        avg_memory = np.mean([m[1] for m in measurements])
        
        # Record metrics
        test_metrics.add_metric("avg_cpu_usage", avg_cpu)
        test_metrics.add_metric("avg_memory_usage", avg_memory)
        
        # Resource usage assertions
        assert avg_cpu < 80.0, "CPU usage too high"
        assert avg_memory < 90.0, "Memory usage too high"

    def test_concurrent_processing(
        self,
        large_dataset: np.ndarray,
        test_metrics: "TestMetrics"
    ):
        """Test concurrent processing performance."""
        import concurrent.futures
        
        def process_image(img):
            preprocessor = MedicalImagePreprocessor()
            return preprocessor.preprocess_image(img, modality="MRI")
        
        start_time = time.time()
        
        # Process images concurrently
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(process_image, img)
                for img in large_dataset[:10]
            ]
            results = [f.result() for f in futures]
        
        execution_time = time.time() - start_time
        
        # Record metrics
        test_metrics.add_metric("concurrent_processing_time", execution_time)
        
        assert len(results) == 10, "Not all images processed"
        assert execution_time < 60.0, "Concurrent processing too slow"
