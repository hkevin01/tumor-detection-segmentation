"""
Custom Pipeline Example

Demonstrates how to build a custom medical imaging pipeline
using the tumor detection and segmentation library.
"""

from tumor_detection.api import (ImagePreprocessor, ModelEvaluator,
                                 TumorDetector, TumorSegmenter)
from tumor_detection.services import DicomService


class CustomMedicalImagingPipeline:
    """
    Custom pipeline combining detection, segmentation, and evaluation.

    This example shows how to build a complete medical imaging workflow
    using the library's API components.
    """

    def __init__(self, config: dict):
        """Initialize pipeline with configuration."""
        self.config = config

        # Initialize components
        self.preprocessor = ImagePreprocessor(
            target_spacing=config.get('target_spacing', (1.0, 1.0, 1.0)),
            target_size=config.get('target_size', (256, 256, 128))
        )

        self.detector = TumorDetector(
            model_name=config.get('detection_model', 'unetr_detection'),
            device=config.get('device', 'auto')
        )

        self.segmenter = TumorSegmenter(
            model_name=config.get('segmentation_model', 'unetr_segmentation'),
            device=config.get('device', 'auto')
        )

        self.evaluator = ModelEvaluator(
            metrics=config.get('metrics', ['dice', 'hausdorff', 'sensitivity']),
            save_results=True
        )

        # Optional DICOM service
        if 'dicom_server' in config:
            self.dicom_service = DicomService(
                server_host=config['dicom_server']['host'],
                server_port=config['dicom_server'].get('port', 11112)
            )
        else:
            self.dicom_service = None

    def process_single_image(self, image_path: str) -> dict:
        """
        Process a single medical image through the complete pipeline.

        Args:
            image_path: Path to the medical image file

        Returns:
            Complete analysis results
        """
        print(f"🔄 Processing image: {image_path}")

        # Step 1: Preprocessing
        print("  📋 Preprocessing...")
        preprocessed = self.preprocessor.preprocess(image_path, normalize=True)

        # Step 2: Detection
        print("  🔍 Running tumor detection...")
        detections = self.detector.detect(
            preprocessed['image'],
            threshold=self.config.get('detection_threshold', 0.5)
        )

        # Step 3: Segmentation (if tumors detected)
        segmentation = None
        if detections['detections']:
            print("  🎯 Running tumor segmentation...")
            segmentation = self.segmenter.segment(
                preprocessed['image'],
                post_process=True
            )

        # Step 4: Compile results
        results = {
            'image_path': image_path,
            'preprocessing': preprocessed['metadata'],
            'detections': detections,
            'segmentation': segmentation,
            'summary': {
                'tumors_detected': len(detections['detections']),
                'has_segmentation': segmentation is not None
            }
        }

        print(f"  ✅ Processing complete. Found {len(detections['detections'])} tumors")
        return results

    def process_dicom_study(self, study_uid: str) -> dict:
        """
        Process a DICOM study from a PACS server.

        Args:
            study_uid: DICOM Study Instance UID

        Returns:
            Analysis results for all series in the study
        """
        if not self.dicom_service:
            raise ValueError("DICOM service not configured")

        print(f"📡 Processing DICOM study: {study_uid}")

        # Retrieve study from PACS
        series_files = self.dicom_service.retrieve_series(study_uid)

        # Process each series
        results = []
        for series_file in series_files:
            series_results = self.process_single_image(str(series_file))
            results.append(series_results)

        # Store results back to PACS
        if any(r['summary']['has_segmentation'] for r in results):
            self.dicom_service.store_results(
                results_path="./analysis_results",
                study_uid=study_uid
            )

        return {
            'study_uid': study_uid,
            'series_processed': len(results),
            'total_tumors': sum(r['summary']['tumors_detected'] for r in results),
            'series_results': results
        }

    def evaluate_against_ground_truth(
        self,
        predictions: list,
        ground_truth: list
    ) -> dict:
        """
        Evaluate pipeline results against ground truth annotations.

        Args:
            predictions: List of prediction results
            ground_truth: List of ground truth annotations

        Returns:
            Evaluation metrics
        """
        print("📊 Evaluating against ground truth...")

        # Extract segmentations for evaluation
        pred_masks = [p['segmentation']['segmentation'] for p in predictions
                      if p['segmentation']]
        gt_masks = ground_truth

        if pred_masks and gt_masks:
            evaluation = self.evaluator.evaluate_segmentation(
                predictions=pred_masks,
                ground_truth=gt_masks
            )

            # Generate report
            report = self.evaluator.generate_report(evaluation)
            print("📋 Evaluation Report:")
            print(report)

            return evaluation
        else:
            print("⚠️ No segmentations available for evaluation")
            return {}


def main():
    """Main example demonstrating the custom pipeline."""

    # Pipeline configuration
    config = {
        'target_spacing': (1.0, 1.0, 1.0),
        'target_size': (256, 256, 128),
        'detection_model': 'unetr_detection',
        'segmentation_model': 'unetr_segmentation',
        'detection_threshold': 0.5,
        'device': 'auto',
        'metrics': ['dice', 'hausdorff', 'sensitivity', 'specificity'],
        # Optional DICOM configuration
        # 'dicom_server': {
        #     'host': 'pacs.hospital.com',
        #     'port': 11112
        # }
    }

    # Create pipeline
    pipeline = CustomMedicalImagingPipeline(config)

    # Example 1: Process single images
    print("🏥 Custom Medical Imaging Pipeline Example")
    print("=" * 60)

    sample_images = [
        "data/patient001/brain_ct.nii.gz",
        "data/patient002/brain_mri.nii.gz",
        "data/patient003/brain_ct.nii.gz"
    ]

    results = []
    for image_path in sample_images:
        # Simulate processing (would work with real files)
        print(f"\nWould process: {image_path}")
        # result = pipeline.process_single_image(image_path)
        # results.append(result)

    # Example 2: DICOM study processing
    print("\n📡 DICOM Study Processing Example:")
    print("Would process DICOM study: 1.2.3.4.5.6.7.8.9")
    # study_results = pipeline.process_dicom_study("1.2.3.4.5.6.7.8.9")

    print("\n✅ Custom pipeline example complete!")
    print("\n💡 This example shows how to:")
    print("  - Combine detection and segmentation workflows")
    print("  - Integrate with DICOM/PACS systems")
    print("  - Add custom preprocessing and evaluation")
    print("  - Build production-ready medical imaging pipelines")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
