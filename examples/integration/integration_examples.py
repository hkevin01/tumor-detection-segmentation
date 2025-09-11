"""
Tumor Detection Library - Integration Examples

This module demonstrates how to use the tumor-detection-segmentation library
in other applications with different integration patterns.
"""

# ==============================================================================
# EXAMPLE 1: Basic Library Usage in External Applications
# ==============================================================================

def example_basic_usage():
    """
    Basic usage patterns for integrating the library into other applications.
    """
    print("=== Basic Library Usage Examples ===\n")

    # Method 1: High-level API functions (easiest)
    from tumor_detection import detect_tumors, segment_tumors

    # Simple detection in your app
    image_path = "path/to/medical/image.nii.gz"
    results = detect_tumors(image_path, threshold=0.5)
    print(f"Detection results: {results}")

    # Simple segmentation in your app
    segmentation = segment_tumors(image_path, post_process=True)
    print(f"Segmentation shape: {segmentation.shape}")


# ==============================================================================
# EXAMPLE 2: Class-Based Integration (more control)
# ==============================================================================

def example_class_based_usage():
    """
    Using library classes for more control and stateful operations.
    """
    print("=== Class-Based Usage Examples ===\n")

    from tumor_detection.api import (ImagePreprocessor, TumorDetector,
                                     TumorSegmenter)

    # Initialize reusable detector (load model once, use multiple times)
    detector = TumorDetector(model_name="unetr_detection", device="auto")

    # Process multiple images efficiently
    image_paths = ["image1.nii.gz", "image2.nii.gz", "image3.nii.gz"]

    for image_path in image_paths:
        # Preprocess
        preprocessor = ImagePreprocessor()
        processed = preprocessor.preprocess(image_path)

        # Detect
        detections = detector.detect(processed)

        # Segment if tumors found
        if detections["num_detections"] > 0:
            segmenter = TumorSegmenter(model_name="unetr_segmentation")
            segmentation = segmenter.segment(processed)
            print(f"Processed {image_path}: {detections['num_detections']} tumors")


# ==============================================================================
# EXAMPLE 3: Service Integration (DICOM, FHIR, Cloud)
# ==============================================================================

def example_service_integration():
    """
    Integrating with medical systems and cloud services.
    """
    print("=== Service Integration Examples ===\n")

    from tumor_detection.services import DicomService, FhirService

    # DICOM/PACS integration
    dicom = DicomService("pacs.hospital.com")
    studies = dicom.find_studies(patient_id="PATIENT_001")

    for study in studies:
        # Download DICOM files
        dicom_files = dicom.download_study(study["study_id"])

        # Process with AI
        from tumor_detection import detect_tumors
        results = detect_tumors(dicom_files[0])

        # Store results in FHIR
        fhir = FhirService("https://fhir.hospital.com")
        observation = fhir.create_imaging_observation(
            patient_id="PATIENT_001",
            results=results,
            study_id=study["study_id"]
        )
        print(f"Created FHIR observation: {observation['id']}")


# ==============================================================================
# EXAMPLE 4: Batch Processing Pipeline
# ==============================================================================

class MedicalImagingPipeline:
    """
    Example of building a processing pipeline using the library components.
    """

    def __init__(self):
        from tumor_detection.api import (ImagePreprocessor, ModelEvaluator,
                                         TumorDetector, TumorSegmenter)

        self.preprocessor = ImagePreprocessor()
        self.detector = TumorDetector(device="auto")
        self.segmenter = TumorSegmenter(device="auto")
        self.evaluator = ModelEvaluator()

    def process_batch(self, image_paths, output_dir):
        """Process a batch of medical images."""
        results = []

        for image_path in image_paths:
            try:
                # Preprocessing
                processed = self.preprocessor.preprocess(image_path)

                # Detection
                detections = self.detector.detect(processed)

                # Segmentation if tumors found
                segmentation = None
                if detections["num_detections"] > 0:
                    segmentation = self.segmenter.segment(processed)

                # Evaluation metrics
                metrics = None
                if segmentation is not None:
                    metrics = self.evaluator.calculate_metrics(
                        segmentation,
                        ground_truth=None  # Would load GT if available
                    )

                results.append({
                    "image_path": image_path,
                    "detections": detections,
                    "segmentation": segmentation,
                    "metrics": metrics
                })

            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue

        return results


# ==============================================================================
# EXAMPLE 5: Web API Integration
# ==============================================================================

def create_web_api():
    """
    Example of integrating the library into a web API.
    """
    import os
    import tempfile

    from fastapi import FastAPI, File, UploadFile

    from tumor_detection import detect_tumors, segment_tumors

    app = FastAPI(title="Medical Imaging AI API")

    @app.post("/detect")
    async def detect_endpoint(file: UploadFile = File(...)):
        """Detect tumors in uploaded medical image."""
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nii.gz") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            try:
                # Process with library
                results = detect_tumors(temp_file.name, threshold=0.5)
                return {"status": "success", "results": results}
            finally:
                os.unlink(temp_file.name)

    @app.post("/segment")
    async def segment_endpoint(file: UploadFile = File(...)):
        """Segment tumors in uploaded medical image."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nii.gz") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            try:
                segmentation = segment_tumors(temp_file.name, post_process=True)
                # Convert to serializable format
                return {
                    "status": "success",
                    "segmentation_shape": segmentation.shape,
                    "num_tumor_voxels": int(segmentation.sum())
                }
            finally:
                os.unlink(temp_file.name)

    return app


# ==============================================================================
# EXAMPLE 6: Testing and Validation Tools
# ==============================================================================

def example_testing_tools():
    """
    Using the library's testing and validation tools.
    """
    print("=== Testing and Validation Examples ===\n")

    # Import validation tools
    from tools.testing.model_validator import ModelValidator

    # Validate a model
    validator = ModelValidator()

    # Test model performance
    test_images = ["test1.nii.gz", "test2.nii.gz"]
    results = validator.validate_model(
        model_path="models/my_model.pth",
        test_images=test_images,
        metrics=["dice", "iou", "hd95"]
    )

    print(f"Validation results: {results}")


# ==============================================================================
# EXAMPLE 7: Configuration Management
# ==============================================================================

def example_configuration():
    """
    Using the library's configuration system.
    """
    print("=== Configuration Examples ===\n")

    from tumor_detection import load_dataset_config, load_recipe_config

    # Load pre-configured recipes
    model_config = load_recipe_config("config/recipes/unetr_multimodal.json")
    dataset_config = load_dataset_config("config/datasets/msd_task01_brain.json")

    print(f"Model config: {model_config['model']['name']}")
    print(f"Dataset: {dataset_config['dataset']['name']}")

    # Use in your application
    from tumor_detection.api import TumorSegmenter

    segmenter = TumorSegmenter(
        config=model_config,
        device="auto"
    )


if __name__ == "__main__":
    """
    Run all examples to demonstrate integration patterns.
    """
    print("Tumor Detection Library - Integration Examples")
    print("=" * 60)

    try:
        example_basic_usage()
        example_class_based_usage()
        example_service_integration()
        example_testing_tools()
        example_configuration()

        print("\n=== Advanced Integration Examples ===")

        # Batch processing pipeline
        pipeline = MedicalImagingPipeline()
        print("✅ Batch processing pipeline initialized")

        # Web API
        app = create_web_api()
        print("✅ Web API created (use with: uvicorn integration_examples:app)")

        print("\n🎉 All integration examples completed successfully!")

    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("Make sure the tumor-detection-segmentation library is installed:")
        print("pip install tumor-detection-segmentation")
    except Exception as e:
        print(f"❌ Error running examples: {e}")

    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("Make sure the tumor-detection-segmentation library is installed:")
        print("pip install tumor-detection-segmentation")
    except Exception as e:
        print(f"❌ Error running examples: {e}")
