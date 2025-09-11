"""
Tumor Detection Library - Integration Utilities

This module provides convenient utilities and helpers for integrating
the tumor-detection-segmentation library into other applications.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TumorAnalyzer:
    """
    High-level wrapper for easy integration into other applications.

    This class provides a simplified interface that handles model loading,
    configuration, and common workflows behind the scenes.
    """

    def __init__(
        self,
        device: str = "auto",
        detection_threshold: float = 0.5,
        enable_segmentation: bool = True,
        enable_services: bool = False
    ):
        """
        Initialize the tumor analyzer.

        Args:
            device: Computing device ('auto', 'cpu', 'cuda', 'mps')
            detection_threshold: Minimum confidence for tumor detection
            enable_segmentation: Whether to enable segmentation capabilities
            enable_services: Whether to enable DICOM/FHIR services
        """
        self.device = device
        self.detection_threshold = detection_threshold
        self.enable_segmentation = enable_segmentation
        self.enable_services = enable_services

        # Lazy loading - models loaded when first used
        self._detector = None
        self._segmenter = None
        self._preprocessor = None
        self._services = {}

        print(f"🧠 TumorAnalyzer initialized (device: {device})")

    def analyze(
        self,
        image_path: Union[str, Path],
        include_segmentation: Optional[bool] = None,
        return_raw_data: bool = False
    ) -> Dict[str, Any]:
        """
        Complete tumor analysis of a medical image.

        Args:
            image_path: Path to medical image
            include_segmentation: Override segmentation setting
            return_raw_data: Whether to include raw numpy arrays

        Returns:
            dict: Complete analysis results
        """
        try:
            # Load models if needed
            self._ensure_models_loaded()

            image_path = str(image_path)
            results = {
                "image_path": image_path,
                "status": "success"
            }

            # Step 1: Detection
            from tumor_detection import detect_tumors
            detection_results = detect_tumors(
                image_path,
                threshold=self.detection_threshold
            )

            results.update({
                "detection": detection_results,
                "tumors_detected": detection_results.get("num_detections", 0)
            })

            # Step 2: Segmentation (if tumors found and enabled)
            include_seg = (include_segmentation if include_segmentation is not None
                          else self.enable_segmentation)

            if results["tumors_detected"] > 0 and include_seg:
                from tumor_detection import segment_tumors
                segmentation = segment_tumors(image_path, post_process=True)

                results.update({
                    "segmentation": {
                        "shape": segmentation.shape,
                        "tumor_voxels": int(segmentation.sum()),
                        "volume_mm3": self._estimate_volume(segmentation)
                    }
                })

                if return_raw_data:
                    results["segmentation"]["mask"] = segmentation

            return results

        except Exception as e:
            return {
                "image_path": str(image_path),
                "status": "error",
                "error": str(e)
            }

    def batch_analyze(
        self,
        image_paths: List[Union[str, Path]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images in batch.

        Args:
            image_paths: List of image paths
            show_progress: Whether to show progress bar

        Returns:
            list: Results for each image
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(image_paths, desc="Analyzing images")
            except ImportError:
                iterator = image_paths
                print(f"Analyzing {len(image_paths)} images...")
        else:
            iterator = image_paths

        for image_path in iterator:
            result = self.analyze(image_path)
            results.append(result)

        # Summary statistics
        successful = sum(1 for r in results if r["status"] == "success")
        total_tumors = sum(r.get("tumors_detected", 0) for r in results)

        print(f"✅ Batch analysis complete: {successful}/{len(image_paths)} successful, {total_tumors} total tumors detected")

        return results

    def setup_dicom_service(self, pacs_server: str, port: int = 104) -> bool:
        """
        Set up DICOM/PACS integration.

        Args:
            pacs_server: PACS server address
            port: DICOM port (default 104)

        Returns:
            bool: Success status
        """
        try:
            from tumor_detection.services import DicomService
            self._services["dicom"] = DicomService(pacs_server, port=port)
            print(f"✅ DICOM service connected: {pacs_server}:{port}")
            return True
        except Exception as e:
            print(f"❌ DICOM setup failed: {e}")
            return False

    def setup_fhir_service(self, fhir_server: str) -> bool:
        """
        Set up FHIR integration.

        Args:
            fhir_server: FHIR server URL

        Returns:
            bool: Success status
        """
        try:
            from tumor_detection.services import FhirService
            self._services["fhir"] = FhirService(fhir_server)
            print(f"✅ FHIR service connected: {fhir_server}")
            return True
        except Exception as e:
            print(f"❌ FHIR setup failed: {e}")
            return False

    def find_patient_studies(self, patient_id: str) -> List[Dict]:
        """
        Find studies for a patient (requires DICOM service).

        Args:
            patient_id: Patient identifier

        Returns:
            list: Available studies
        """
        if "dicom" not in self._services:
            raise RuntimeError("DICOM service not configured. Call setup_dicom_service() first.")

        return self._services["dicom"].find_studies(patient_id=patient_id)

    def _ensure_models_loaded(self):
        """Lazy loading of AI models."""
        if self._detector is None:
            from tumor_detection.api import TumorDetector
            self._detector = TumorDetector(device=self.device)

        if self.enable_segmentation and self._segmenter is None:
            from tumor_detection.api import TumorSegmenter
            self._segmenter = TumorSegmenter(device=self.device)

        if self._preprocessor is None:
            from tumor_detection.api import ImagePreprocessor
            self._preprocessor = ImagePreprocessor()

    def _estimate_volume(self, segmentation_mask) -> float:
        """Estimate tumor volume (assumes 1mm³ voxels)."""
        return float(segmentation_mask.sum())


def quick_detect(image_path: Union[str, Path], threshold: float = 0.5) -> Dict:
    """
    Ultra-simple detection function for quick integration.

    Args:
        image_path: Path to medical image
        threshold: Detection threshold

    Returns:
        dict: Detection results
    """
    from tumor_detection import detect_tumors
    return detect_tumors(str(image_path), threshold=threshold)


def quick_segment(image_path: Union[str, Path], post_process: bool = True):
    """
    Ultra-simple segmentation function for quick integration.

    Args:
        image_path: Path to medical image
        post_process: Whether to apply post-processing

    Returns:
        numpy.ndarray: Segmentation mask
    """
    from tumor_detection import segment_tumors
    return segment_tumors(str(image_path), post_process=post_process)


def analyze_folder(
    folder_path: Union[str, Path],
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze all medical images in a folder.

    Args:
        folder_path: Path to folder containing medical images
        output_file: Optional CSV file to save results

    Returns:
        dict: Summary results
    """
    folder_path = Path(folder_path)

    # Find medical images
    image_extensions = ["*.nii.gz", "*.nii", "*.dcm"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(folder_path.glob(ext))

    if not image_files:
        return {"error": "No medical images found in folder"}

    # Analyze with TumorAnalyzer
    analyzer = TumorAnalyzer()
    results = analyzer.batch_analyze(image_files)

    # Summary statistics
    successful = [r for r in results if r["status"] == "success"]
    total_tumors = sum(r.get("tumors_detected", 0) for r in successful)

    summary = {
        "total_images": len(image_files),
        "successful_analyses": len(successful),
        "total_tumors_detected": total_tumors,
        "results": results
    }

    # Save to CSV if requested
    if output_file:
        try:
            import pandas as pd
            df_data = []
            for r in results:
                df_data.append({
                    "image_path": r["image_path"],
                    "status": r["status"],
                    "tumors_detected": r.get("tumors_detected", 0),
                    "error": r.get("error", "")
                })

            df = pd.DataFrame(df_data)
            df.to_csv(output_file, index=False)
            print(f"📊 Results saved to: {output_file}")

        except ImportError:
            print("⚠️  pandas not available, skipping CSV export")

    return summary


def analyze_folder(
    folder_path: Union[str, Path],
    output_csv: Optional[Union[str, Path]] = None,
    file_pattern: str = "*.nii*",
    progress: bool = True
) -> Dict[str, Any]:
    """
    Analyze all medical images in a folder.

    Args:
        folder_path: Path to folder containing medical images
        output_csv: Optional path to save CSV summary
        file_pattern: Glob pattern for image files (default: "*.nii*")
        progress: Show progress bar

    Returns:
        Dictionary with analysis summary and results
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        raise ValueError(f"Folder not found: {folder_path}")

    # Find image files
    image_files = list(folder_path.glob(file_pattern))
    if not image_files:
        print(f"⚠️  No image files found matching pattern: {file_pattern}")
        return {"files_found": 0, "results": []}

    print(f"🔍 Found {len(image_files)} image files to analyze")

    # Initialize analyzer
    from tumor_detection.integration import TumorAnalyzer
    analyzer = TumorAnalyzer()

    results = []
    for i, image_file in enumerate(image_files):
        if progress:
            print(f"Processing {i+1}/{len(image_files)}: {image_file.name}")

        try:
            result = analyzer.analyze(str(image_file))
            result["filename"] = image_file.name
            result["filepath"] = str(image_file)
            results.append(result)
        except Exception as e:
            print(f"❌ Error processing {image_file.name}: {e}")
            results.append({
                "filename": image_file.name,
                "filepath": str(image_file),
                "error": str(e),
                "num_tumors": 0
            })

    # Summary statistics
    successful_analyses = [r for r in results if "error" not in r]
    total_tumors = sum(r.get("num_tumors", 0) for r in successful_analyses)

    summary = {
        "files_found": len(image_files),
        "files_processed": len(results),
        "files_successful": len(successful_analyses),
        "total_tumors_detected": total_tumors,
        "results": results
    }

    # Save to CSV if requested
    if output_csv:
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            df.to_csv(output_csv, index=False)
            print(f"📊 Results saved to: {output_csv}")
        except ImportError:
            print("⚠️  pandas not available for CSV export")
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")

    print(f"✅ Analysis complete: {len(successful_analyses)}/{len(image_files)} files, {total_tumors} tumors total")
    return summary


def check_installation() -> Dict[str, Any]:
    """
    Check the installation status of tumor detection components.

    Returns:
        Dict containing status information for various components
    """
    status = {}

    # Core library
    try:
        import tumor_detection
        status["core_library"] = True
        status["version"] = getattr(tumor_detection, "__version__", "unknown")
    except ImportError:
        status["core_library"] = False
        status["version"] = None

    # API components
    try:
        from tumor_detection.api import ImagePreprocessor, TumorDetector
        status["api_components"] = True
    except ImportError:
        status["api_components"] = False

    # DICOM services
    try:
        from tumor_detection.services import DicomService
        status["dicom_services"] = True
    except ImportError:
        status["dicom_services"] = False

    # CLI tools
    import shutil
    status["cli_tools"] = bool(shutil.which("tumor-detect-train"))

    return status


def print_integration_help():
    """Print helpful integration information."""
    print("🧠 Tumor Detection Library - Integration Help")
    print("=" * 50)

    # Check installation
    status = check_installation()

    if status.get("core_library"):
        print(f"✅ Library installed (version {status.get('version', 'unknown')})")
    else:
        print("❌ Library not installed")
        print("   Run: pip install tumor-detection-segmentation")
        return

    if status.get("api_components"):
        print("✅ API components working")
    else:
        print("❌ API components not working")

    print(f"{'✅' if status.get('dicom_services') else '⚠️'} DICOM services {'available' if status.get('dicom_services') else 'not available'}")
    print(f"{'✅' if status.get('cli_tools') else '⚠️'} CLI tools {'available' if status.get('cli_tools') else 'not available'}")

    print("\n📋 Quick Usage Examples:")
    print("   # Simple detection")
    print("   from tumor_detection.integration import quick_detect")
    print("   results = quick_detect('image.nii.gz')")
    print()
    print("   # Complete analysis")
    print("   from tumor_detection.integration import TumorAnalyzer")
    print("   analyzer = TumorAnalyzer()")
    print("   results = analyzer.analyze('image.nii.gz')")
    print()
    print("   # Analyze folder")
    print("   from tumor_detection.integration import analyze_folder")
    print("   summary = analyze_folder('path/to/images/', 'results.csv')")


if __name__ == "__main__":
    print_integration_help()
