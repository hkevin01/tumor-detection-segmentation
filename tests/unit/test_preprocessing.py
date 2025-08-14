"""Unit tests for data preprocessing module."""

import numpy as np
import pytest

from src.data_preprocessing import MedicalImagePreprocessor


@pytest.mark.unit
@pytest.mark.preprocessing
class TestMedicalImagePreprocessor:
    """Test cases for MedicalImagePreprocessor class."""

    @pytest.fixture(scope="class")
    def preprocessor(self) -> MedicalImagePreprocessor:
        """Create a preprocessor instance for testing."""
        return MedicalImagePreprocessor(target_size=(64, 64, 64))

    def test_init(self, preprocessor: MedicalImagePreprocessor):
        """Test preprocessor initialization."""
        assert preprocessor.target_size == (64, 64, 64)
        assert preprocessor.transform is not None

    def test_preprocess_standard_image(
        self, preprocessor: MedicalImagePreprocessor
    ):
        """Test preprocessing of standard image format."""
        # Create a dummy image
        test_image = np.random.rand(256, 256)
        result = preprocessor._preprocess_standard_image(test_image)

        # Check output shape and normalization
        assert result.shape[0] == 1  # Channel dimension
        assert result.dtype == np.float32 or result.dtype == np.float64
        assert np.all(result >= 0) and np.all(result <= 1)

    @pytest.mark.parametrize("shape", [
        (256, 256),
        (128, 128, 128),
        (1, 256, 256)
    ])
    def test_preprocess_image_shapes(
        self,
        preprocessor: MedicalImagePreprocessor,
        shape: tuple,
        test_metrics,
    ):
        """Test preprocessing with different input shapes."""
        test_image = np.random.rand(*shape)
        try:
            result = preprocessor._preprocess_standard_image(test_image)
            # Add success metric
            test_metrics.add_metric("accuracy", 1.0)
        except Exception as e:
            # Add failure metric
            test_metrics.add_metric("accuracy", 0.0)
            raise e

        # Verify output dimensions
        if len(shape) == 2:
            assert result.shape == (1,) + shape
        elif len(shape) == 3 and shape[0] == 1:
            assert result.shape == shape

    @pytest.mark.parametrize("modality", ["MRI", "CT"])
    def test_preprocess_image_modalities(
        self,
        preprocessor: MedicalImagePreprocessor,
        sample_mri: np.ndarray,
        sample_ct: np.ndarray,
        modality: str,
        test_metrics,
        tmp_path,
    ):
        """Test preprocessing with different modalities."""
        image = sample_mri if modality == "MRI" else sample_ct
        # Ensure 2D image for standard image path flow
        if image.ndim == 3:
            image2d = image[0]
        else:
            image2d = image
        # Save to a temporary PNG file and use preprocess_image(path)
        from PIL import Image
        img_u8 = (
            255 * (image2d - np.min(image2d)) / (np.ptp(image2d) + 1e-8)
        ).astype(np.uint8)
        img_path = tmp_path / f"sample_{modality}.png"
        Image.fromarray(img_u8).save(img_path)

        try:
            result = preprocessor.preprocess_image(
                str(img_path), modality=modality
            )
            assert "preprocessed_image" in result
            assert "metadata" in result
            assert result["metadata"]["modality"] == modality

            # Add performance metrics
            test_metrics.add_metric(
                "execution_time",
                pytest.approx(0.1, abs=0.1)  # Example threshold
            )
        except Exception as e:
            test_metrics.add_metric("accuracy", 0.0)
            raise e

    @pytest.mark.slow
    def test_large_image_processing(
        self,
        preprocessor: MedicalImagePreprocessor,
        test_metrics,
    ):
        """Test preprocessing of large images."""
        large_image = np.random.rand(512, 512, 512)

        try:
            # Use internal method with array input to avoid file I/O
            result = preprocessor._preprocess_standard_image(large_image)
            assert result is not None and isinstance(result, np.ndarray)

            # Add memory usage metric
            import psutil  # type: ignore[import-not-found]
            process = psutil.Process()
            memory_used = process.memory_info().rss / 1024 / 1024  # MB
            test_metrics.add_metric("memory_usage", memory_used)
        except Exception as e:
            test_metrics.add_metric("accuracy", 0.0)
            raise e
            raise e
