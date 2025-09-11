"""
Basic Tumor Detection Example

This example demonstrates the basic usage of the tumor detection API
for processing medical images and detecting tumors.
"""

import numpy as np

from tumor_detection.api import TumorDetector, detect_tumors


def basic_detection_example():
    """Basic example of using the detection API."""

    # Example 1: Single image detection using convenience function
    print("🔍 Basic tumor detection example")

    # Simulate a medical image (in practice, load from DICOM or NIfTI file)
    sample_image = np.random.rand(128, 128, 64).astype(np.float32)

    # Detect tumors using the convenience function
    results = detect_tumors(
        image=sample_image,
        model_name="unetr_detection",
        threshold=0.5
    )

    print("Detection results:")
    print(f"  - Number of detections: {len(results['detections'])}")
    print(f"  - Confidence scores: {results['confidences']}")

    # Example 2: Using the TumorDetector class for multiple images
    print("\n📋 Batch detection example")

    detector = TumorDetector(
        model_name="unetr_detection",
        device="auto"  # Automatically choose GPU if available
    )

    # Simulate multiple images
    images = [
        np.random.rand(128, 128, 64).astype(np.float32) for _ in range(3)
    ]

    # Process batch of images
    batch_results = detector.detect_batch(
        images=images,
        threshold=0.6,
        batch_size=2
    )

    print(f"Processed {len(batch_results)} images")
    for i, result in enumerate(batch_results):
        print(f"  Image {i+1}: {len(result['detections'])} detections")

def detection_with_file_paths():
    """Example using file paths for image loading."""

    print("\n📁 File-based detection example")

    # Example with file paths (would work with actual DICOM/NIfTI files)
    image_paths = [
        "data/patient001/brain_ct.nii.gz",
        "data/patient002/brain_mri.nii.gz"
    ]

    detector = TumorDetector(model_name="unetr_detection")

    # Note: This would work with real files
    print("Would process the following files:")
    for path in image_paths:
        print(f"  - {path}")
        # results = detector.detect(path, threshold=0.5)

def advanced_detection_options():
    """Example showing advanced detection options."""

    print("\n⚙️ Advanced detection options")

    # Create detector with custom settings
    detector = TumorDetector(
        model_name="unetr_detection",
        device="cuda",  # Force GPU usage
        model_path="models/custom_detector.pth"  # Custom model weights
    )

    sample_image = np.random.rand(256, 256, 128).astype(np.float32)

    # Detection with probability maps
    results = detector.detect(
        image=sample_image,
        threshold=0.3,  # Lower threshold for higher sensitivity
        return_probabilities=True  # Get probability maps for visualization
    )

    print("Advanced detection completed:")
    print(f"  - Detections: {len(results['detections'])}")
    print(f"  - Probability map shape: {results['probabilities'].shape if results['probabilities'] is not None else 'None'}")

if __name__ == "__main__":
    print("🏥 Tumor Detection API Examples")
    print("=" * 50)

    try:
        basic_detection_example()
        detection_with_file_paths()
        advanced_detection_options()

        print("\n✅ All examples completed successfully!")
        print("\n💡 Next steps:")
        print("  - Try with real medical images (DICOM/NIfTI format)")
        print("  - Explore different model types and thresholds")
        print("  - Integrate with your medical imaging pipeline")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("Note: Examples use placeholder data. "
              "For real usage, ensure proper model weights and data are available.")
        print("Note: Examples use placeholder data. "
              "For real usage, ensure proper model weights and data are available.")
