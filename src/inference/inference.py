"""
Inference module for tumor detection and segmentation.

This module provides functionality for running inference on new medical images
using trained models with support for overlay visualization and TTA.
"""

import argparse
import gc
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import matplotlib.pyplot as plt
    import nibabel as nib
    import numpy as np
    import torch
    from monai.data import decollate_batch
    from monai.inferers import SlidingWindowInferer
    from monai.metrics import DiceMetric
    from monai.transforms import AsDiscrete
    from monai.transforms.compose import Compose
    from monai.transforms.intensity.array import ScaleIntensity
    from monai.transforms.io.array import LoadImage
    from monai.transforms.spatial.array import Resize
    from monai.transforms.utility.array import EnsureChannelFirst, EnsureType
    # SciPy for post-processing
    from scipy import ndimage
    from scipy.ndimage import binary_fill_holes, label
    SCIPY_AVAILABLE = True

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    SCIPY_AVAILABLE = False

# Add repo src to path for training imports when running as a script
sys.path.append(str(Path(__file__).parent.parent))

# Crash prevention utilities
try:
    from src.utils.crash_prevention import (emergency_cleanup,
                                            gpu_safe_context,
                                            log_system_resources,
                                            memory_safe_context,
                                            safe_execution,
                                            start_global_protection,
                                            stop_global_protection)
    CRASH_PREVENTION_AVAILABLE = True
except ImportError:
    CRASH_PREVENTION_AVAILABLE = False
    # Fallback implementations
    from contextlib import contextmanager
    @contextmanager
    def memory_safe_context(*args, **kwargs):
        yield None
    @contextmanager
    def gpu_safe_context(*args, **kwargs):
        yield None
    def safe_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def emergency_cleanup():
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    def log_system_resources(logger=None):
        pass
    def start_global_protection(*args, **kwargs):
        pass
    def stop_global_protection():
        pass

try:
    # Import visualization utilities
    from src.training.callbacks.visualization import save_overlay_panel
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TumorPredictor:
    """Class for running inference on medical images."""

    def __init__(
        self,
        model_path: str,
        config_path: str,
        device: str = "auto",
        tta: bool = False,
    ):
        """Initialize predictor.

        Args:
            model_path: Path to trained model checkpoint
            config_path: Path to configuration file
            device: Device to run inference on
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available")

        # Load configuration
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Set device
        if device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        else:
            self.device = torch.device(device)

        # TTA flag
        self.use_tta = bool(tta)

        # Load model
        self.model = self._load_model(model_path)
        self.model.eval()

        # Setup transforms
        self.transforms = self._setup_transforms()

    def save_inference_overlay(
        self,
        image: torch.Tensor,
        prediction: torch.Tensor,
        out_path: Path,
        slices: Optional[List[int]] = None,
        ground_truth: Optional[torch.Tensor] = None,
    ) -> None:
        """
        Save overlay visualization for inference results.
        image: (C, H, W, D) tensor
        prediction: (H, W, D) tensor (class labels) or (C, H, W, D) one-hot
        ground_truth: Optional (H, W, D) or (C, H, W, D) ground truth labels
        """
        if not DEPENDENCIES_AVAILABLE:
            return

        # Convert prediction to one-hot if needed
        if prediction.ndim == 3:
            # Convert class labels to one-hot
            num_classes = int(prediction.max().item()) + 1
            pred_oh = torch.nn.functional.one_hot(
                prediction.long(), num_classes=num_classes
            ).permute(3, 0, 1, 2).float()
        else:
            pred_oh = prediction

        # Convert ground truth to one-hot if provided
        if ground_truth is not None:
            if ground_truth.ndim == 3:
                num_classes = int(ground_truth.max().item()) + 1
                gt_oh = torch.nn.functional.one_hot(
                    ground_truth.long(), num_classes=num_classes
                ).permute(3, 0, 1, 2).float()
            else:
                gt_oh = ground_truth
        else:
            # Create dummy ground truth (all zeros) for overlay function
            gt_oh = torch.zeros_like(pred_oh)

        # Use improved overlay panel if available, otherwise fallback
        if VISUALIZATION_AVAILABLE:
            save_overlay_panel(image, gt_oh, pred_oh, out_path, slices)
        else:
            self._fallback_overlay(image, pred_oh, out_path, slices)

    def _fallback_overlay(
        self,
        image: torch.Tensor,
        prediction: torch.Tensor,
        out_path: Path,
        slices: Optional[List[int]] = None,
    ) -> None:
        """Fallback overlay method if visualization callback unavailable."""
        # Use first channel as background
        img = image[0].detach().cpu().float().numpy()

        # Get class 1 if available, else max over classes
        if prediction.shape[0] > 1:
            pred = prediction[1].detach().cpu().numpy()
        else:
            pred = prediction.max(0).values.detach().cpu().numpy()

        _, _, D = img.shape

        # Default to 3 slices if not specified
        if slices is None:
            slices = [D // 4, D // 2, 3 * D // 4]

        # Ensure slices are valid
        slices = [max(0, min(s, D-1)) for s in slices]

        n_slices = len(slices)
        fig, axes = plt.subplots(1, n_slices, figsize=(6 * n_slices, 6))

        # Ensure axes is always a list for consistent indexing
        if n_slices == 1:
            axes = [axes]

        for i, z in enumerate(slices):
            base = img[..., z]
            base = (base - base.min()) / (base.max() - base.min() + 1e-8)
            pred_slice = pred[..., z]

            axes[i].axis("off")
            axes[i].imshow(base, cmap="gray")
            # Overlay prediction with red color
            axes[i].imshow(
                np.ma.masked_where(pred_slice == 0, pred_slice),
                cmap="Reds", alpha=0.5
            )
            axes[i].set_title(f"Prediction Slice {z}/{D-1}", fontsize=10)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0)
        plt.close()

    def save_nifti_mask(
        self,
        prediction: np.ndarray,
        reference_path: str,
        output_path: Path,
    ) -> None:
        """
        Save prediction as NIfTI file using reference image header.
        """
        if not DEPENDENCIES_AVAILABLE:
            return

        try:
            # Load reference image to get header/affine
            ref_img = nib.load(reference_path)

            # Create new NIfTI image with prediction data
            pred_img = nib.Nifti1Image(
                prediction.astype(np.uint8),
                ref_img.affine,
                ref_img.header
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            nib.save(pred_img, output_path)
        except Exception as e:
            print(f"Warning: Could not save NIfTI mask: {e}")

    def _load_model(self, model_path: str):
        """Load trained model from checkpoint."""
    # Import create_model with support for both package and
    # script execution
        try:
            # When imported as package: src.inference
            from ..training.trainer import create_model  # type: ignore
        except ImportError:
            # When run as a script, fall back to sys.path-based import
            src_path = Path(__file__).parent.parent
            if str(src_path) not in sys.path:
                sys.path.append(str(src_path))
            from training.trainer import create_model  # type: ignore

        # Create model architecture
        model = create_model(self.config)

        # Load trained weights
        checkpoint = torch.load(model_path, map_location=self.device)

        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        model.to(self.device)
        return model

    def _setup_transforms(self):
        """Setup preprocessing transforms for inference."""
        # Use array transforms: path -> Tensor (C,H,W[,D])
        spatial_size = self.config.get("image_size", [128, 128, 128])
        return Compose(
            [
                LoadImage(image_only=True),
                EnsureChannelFirst(),
                Resize(spatial_size),
                ScaleIntensity(),
                EnsureType(data_type="tensor"),
            ]
        )

    @safe_execution(max_retries=2, memory_threshold=0.85, gpu_threshold=0.90)
    def predict_single(self, image_path: str) -> Dict[str, Any]:
        """Run inference on a single image with crash prevention.

        Args:
            image_path: Path to input image

        Returns:
            Dictionary containing prediction results
        """
        logger.info(f"Processing image: {image_path}")

        with memory_safe_context(threshold=0.85):
            with gpu_safe_context(threshold=0.90):
                try:
                    # Preprocess image: path str -> Tensor (C, ...)
                    img_tensor = self.transforms(image_path)
                    if not torch.is_tensor(img_tensor):
                        # Safety net if transforms didn't convert to tensor
                        img_tensor = torch.as_tensor(img_tensor)

                    # Add batch dimension and move to device
                    image = img_tensor.unsqueeze(0).to(self.device, non_blocking=True)

                    logger.info(f"Image shape: {image.shape}, device: {self.device}")
                    log_system_resources(logger)

                    # Run inference with memory management
                    with torch.no_grad():
                        if self.use_tta:
                            logger.info("Running TTA inference")
                            prediction = self._predict_with_tta(image)
                        else:
                            logger.info("Running standard inference")
                            logits = self.model(image)
                            probs = torch.softmax(logits, dim=1)
                            prediction = torch.argmax(probs, dim=1)

                            # Clean up intermediate tensors
                            del logits, probs

                    # Convert to numpy for easier handling
                    prediction_np = prediction.cpu().numpy().squeeze()

                    # Export preprocessed input image for visualization
                    input_np = img_tensor.detach().cpu().numpy()
                    if input_np.shape[0] == 1:
                        input_np = np.squeeze(input_np, axis=0)

                    # Clean up GPU tensors
                    del image, prediction, img_tensor
                    emergency_cleanup()

                    logger.info("Inference completed successfully")

                    return {
                        "prediction": prediction_np,
                        "input_image": input_np,
                        "input_shape": image.shape if 'image' in locals() else None,
                        "output_shape": prediction.shape if 'prediction' in locals() else None,
                        "device": str(self.device),
                        "tta": self.use_tta,
                    }

                except RuntimeError as e:
                    if "out of memory" in str(e).lower():
                        logger.error(f"OOM error during inference: {e}")
                        emergency_cleanup()
                        # Try with reduced precision or other fallbacks
                        raise RuntimeError(f"Inference failed due to memory: {e}")
                    else:
                        raise e
                except Exception as e:
                    logger.error(f"Inference error: {e}")
                    emergency_cleanup()
                    raise e

    def _predict_with_tta(self, image: "torch.Tensor") -> "torch.Tensor":
        """Simple flip-based TTA.

        Applies test-time augmentations by flipping across spatial dims,
        averages class probabilities, and returns argmax segmentation.

        Args:
            image: input tensor of shape (N=1, C, ...spatial)

        Returns:
            Tensor of predicted labels with shape (N=1, ...spatial)
        """
        import torch  # local import for type hints

        n_dims = image.ndim  # expect 5 for NCDHW or 4 for NCHW
        if n_dims not in (4, 5):
            # Fallback to single-pass if unexpected shape
            logits = self.model(image)
            probs = torch.softmax(logits, dim=1)
            return torch.argmax(probs, dim=1)

        # Determine spatial dims positions
        # For NCHW -> spatial dims = (2,3); for NCDHW -> (2,3,4)
        spatial_dims = list(range(2, n_dims))

        # Build flip combinations: empty (identity) + single + pair + all
        flip_sets = [[]]
        for d in spatial_dims:
            flip_sets.append([d])
        if len(spatial_dims) >= 2:
            flip_sets.append(spatial_dims[:2])
        if len(spatial_dims) == 3:
            flip_sets.append([spatial_dims[0], spatial_dims[2]])
            flip_sets.append(spatial_dims[1:])
            flip_sets.append(spatial_dims)

        agg_probs: Optional[torch.Tensor] = None
        for axes in flip_sets:
            if axes:
                x = torch.flip(image, dims=axes)
            else:
                x = image
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            if axes:
                probs = torch.flip(probs, dims=axes)
            agg_probs = probs if agg_probs is None else (agg_probs + probs)

        agg_probs = agg_probs / float(len(flip_sets))
        return torch.argmax(agg_probs, dim=1)

    def predict_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Run inference on multiple images."""
        results: List[Dict[str, Any]] = []

        for image_path in image_paths:
            try:
                result = self.predict_single(image_path)
                result["image_path"] = image_path
                result["status"] = "success"
            except (RuntimeError, ValueError, OSError) as e:
                result = {
                    "image_path": image_path,
                    "status": "error",
                    "error": str(e),
                }

            results.append(result)

        return results

    def predict_from_directory(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        file_pattern: str = "*.nii.gz",
    ) -> Dict[str, Any]:
        """Run inference on all images in a directory."""

        input_path = Path(input_dir)
        image_files = list(input_path.glob(file_pattern))

        if not image_files:
            raise ValueError(
                "No images found matching pattern "
                f"{file_pattern} in {input_dir}"
            )

        print(f"Found {len(image_files)} images to process")

        # Run predictions
        results = self.predict_batch([str(f) for f in image_files])

        # Save results if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save individual predictions
            for result in results:
                if result["status"] == "success":
                    filename = (
                        Path(result["image_path"]).stem + "_prediction.npy"
                    )
                    np.save(output_path / filename, result["prediction"])

            # Save summary
            summary_file = output_path / "prediction_summary.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "total_images": len(image_files),
                        "successful_predictions": sum(
                            1 for r in results if r["status"] == "success"
                        ),
                        "failed_predictions": sum(
                            1 for r in results if r["status"] == "error"
                        ),
                        "results": results,
                    },
                    f,
                    indent=2,
                )

        return {
            "total_processed": len(image_files),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "results": results,
        }


class EnhancedTumorPredictor(TumorPredictor):
    """Enhanced predictor with sliding window inference and overlay support."""

    def __init__(
        self,
        model_path: str,
        config_path: str,
        device: str = "auto",
        tta: bool = False,
        sw_overlap: float = 0.25,
    ):
        super().__init__(model_path, config_path, device, tta)
        self.sw_overlap = sw_overlap

        # Get roi_size from config for sliding window inference
        self.roi_size = tuple(
            self.config.get("model", {}).get("img_size", [128, 128, 128])
        )

    def predict_single_enhanced(
        self,
        image_path: str,
        output_dir: str,
        save_overlays: bool = False,
    ) -> Dict[str, Any]:
        """Enhanced single image prediction with sliding window and overlays."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Load and preprocess image
        img_tensor = self.transforms(image_path)
        if not torch.is_tensor(img_tensor):
            img_tensor = torch.as_tensor(img_tensor)

        # Add batch dimension
        image = img_tensor.unsqueeze(0).to(self.device)

        # Sliding window inference
        inferer = SlidingWindowInferer(
            roi_size=self.roi_size,
            sw_batch_size=1,
            overlap=self.sw_overlap,
        )

        with torch.no_grad():
            if self.use_tta:
                # TTA with sliding window
                logits = self._predict_with_tta_sliding(image, inferer)
            else:
                logits = inferer(image, self.model)

            probs = torch.softmax(logits, dim=1)
            prediction = torch.argmax(probs, dim=1)

        # Convert to numpy
        pred_np = prediction.cpu().numpy().squeeze()

        # Generate case ID from filename
        case_id = Path(image_path).stem

        # Save NIfTI mask
        mask_path = output_path / f"{case_id}_mask.nii.gz"
        self.save_nifti_mask(pred_np, image_path, mask_path)

        # Save overlay if requested
        if save_overlays:
            overlay_dir = output_path / "inference_overlays"
            overlay_dir.mkdir(parents=True, exist_ok=True)
            overlay_path = overlay_dir / f"{case_id}_overlay.png"
            self.save_inference_overlay(
                img_tensor, prediction.squeeze(), overlay_path
            )

        return {
            "case_id": case_id,
            "image_path": image_path,
            "mask_path": str(mask_path),
            "overlay_path": str(overlay_path) if save_overlays else None,
            "prediction_shape": pred_np.shape,
            "status": "success",
        }

    def predict_from_directory_enhanced(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str = "*.nii.gz",
        save_overlays: bool = False,
    ) -> Dict[str, Any]:
        """Enhanced directory inference with sliding window and overlays."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Create subdirectories
        masks_dir = output_path / "masks"
        if save_overlays:
            overlays_dir = output_path / "overlays"
            overlays_dir.mkdir(parents=True, exist_ok=True)
        masks_dir.mkdir(parents=True, exist_ok=True)

        image_files = list(input_path.glob(file_pattern))
        if not image_files:
            raise ValueError(f"No images found with pattern {file_pattern}")

        print(f"Found {len(image_files)} images to process")

        results = []
        for img_file in image_files:
            try:
                result = self.predict_single_enhanced(
                    str(img_file),
                    str(output_path),
                    save_overlays=save_overlays,
                )
                results.append(result)
                print(f"✓ Processed: {result['case_id']}")
            except Exception as e:
                results.append({
                    "case_id": img_file.stem,
                    "image_path": str(img_file),
                    "status": "error",
                    "error": str(e),
                })
                print(f"✗ Failed: {img_file.stem} - {e}")

        # Save summary
        summary = {
            "total_processed": len(image_files),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "results": results,
        }

        summary_file = output_path / "inference_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def predict_from_datalist(
        self,
        datalist_path: str,
        output_dir: str,
        save_overlays: bool = False,
    ) -> Dict[str, Any]:
        """Predict from MONAI-style datalist JSON."""
        with open(datalist_path, "r", encoding="utf-8") as f:
            datalist = json.load(f)

        if "validation" in datalist:
            cases = datalist["validation"]
        elif "test" in datalist:
            cases = datalist["test"]
        else:
            cases = datalist.get("data", [])

        results = []
        for case in cases:
            image_path = case.get("image", case.get("images", [None])[0])
            if image_path is None:
                continue

            try:
                result = self.predict_single_enhanced(
                    image_path,
                    output_dir,
                    save_overlays=save_overlays,
                )
                results.append(result)
                print(f"✓ Processed: {result['case_id']}")
            except Exception as e:
                results.append({
                    "case_id": Path(image_path).stem,
                    "image_path": image_path,
                    "status": "error",
                    "error": str(e),
                })
                print(f"✗ Failed: {Path(image_path).stem} - {e}")

        return {
            "total_processed": len(cases),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "results": results,
        }

    def _predict_with_tta_sliding(
        self,
        image: torch.Tensor,
        inferer: SlidingWindowInferer
    ) -> torch.Tensor:
        """TTA with sliding window inference."""
        n_dims = image.ndim
        if n_dims not in (4, 5):
            return inferer(image, self.model)

        spatial_dims = list(range(2, n_dims))
        flip_sets = [[]]

        # Add single axis flips
        for d in spatial_dims:
            flip_sets.append([d])

        # Add multi-axis flips for 3D
        if len(spatial_dims) >= 2:
            flip_sets.append(spatial_dims[:2])
        if len(spatial_dims) == 3:
            flip_sets.append([spatial_dims[0], spatial_dims[2]])
            flip_sets.append(spatial_dims[1:])
            flip_sets.append(spatial_dims)

        agg_logits: Optional[torch.Tensor] = None
        for axes in flip_sets:
            if axes:
                x = torch.flip(image, dims=axes)
            else:
                x = image

            logits = inferer(x, self.model)

            if axes:
                logits = torch.flip(logits, dims=axes)

            if agg_logits is None:
                agg_logits = logits
            else:
                agg_logits = agg_logits + logits

        if agg_logits is not None:
            return agg_logits / float(len(flip_sets))
        else:
            return inferer(image, self.model)



    def apply_postprocessing(
        self,
        prediction: np.ndarray,
        fill_holes: bool = False,
        largest_component: bool = False,
        min_component_size: int = 100
    ) -> np.ndarray:
        """Apply morphological post-processing to prediction."""
        if not SCIPY_AVAILABLE:
            print("Warning: SciPy not available, skipping post-processing")
            return prediction

        result = prediction.copy()

        # Fill holes
        if fill_holes:
            try:
                result = binary_fill_holes(result > 0).astype(result.dtype)
            except Exception as e:
                print(f"Warning: Hole filling failed: {e}")

        # Keep largest connected component
        if largest_component:
            try:
                labeled, num_features = label(result > 0)
                if num_features > 1:
                    component_sizes = [(labeled == i).sum() for i in range(1, num_features + 1)]
                    largest_label = np.argmax(component_sizes) + 1
                    result = (labeled == largest_label).astype(result.dtype)
            except Exception as e:
                print(f"Warning: Largest component extraction failed: {e}")

        # Remove small components
        if min_component_size > 0:
            try:
                labeled, num_features = label(result > 0)
                for i in range(1, num_features + 1):
                    component_mask = labeled == i
                    if component_mask.sum() < min_component_size:
                        result[component_mask] = 0
            except Exception as e:
                print(f"Warning: Small component removal failed: {e}")

        return result


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(
        description="Run tumor segmentation inference"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to model checkpoint"
    )
    parser.add_argument(
        "--config", type=str, required=True, help="Config file path"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input image file, directory, or datalist.json"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./results",
        help="Output directory"
    )
    parser.add_argument(
        "--device", type=str, default="auto", help="Device (auto, cpu, cuda)"
    )
    parser.add_argument(
        "--tta",
        action="store_true",
        help="Enable test-time augmentation",
    )
    parser.add_argument(
        "--amp",
        action="store_true",
        help="Enable automatic mixed precision",
    )
    parser.add_argument(
        "--save-overlays",
        action="store_true",
        help="Save overlay visualizations",
    )
    parser.add_argument(
        "--sw-overlap",
        type=float,
        default=0.25,
        help="Sliding window overlap (0-1)",
    )


    parser.add_argument(
        "--postproc",
        action="store_true",
        help="Enable post-processing operations"
    )
    parser.add_argument(
        "--fill-holes",
        action="store_true",
        help="Fill holes in segmentation masks"
    )
    parser.add_argument(
        "--largest-component",
        action="store_true",
        help="Keep only largest connected component"
    )
    parser.add_argument(
        "--min-component-size",
        type=int,
        default=100,
        help="Minimum component size (voxels) to keep"
    )

    args = parser.parse_args()

    if not DEPENDENCIES_AVAILABLE:
        print("Error: Required dependencies not available.")
        print("Please install: pip install -r requirements.txt")
        return

    print("Tumor Segmentation Inference")
    print("=" * 35)
    print(f"Model: {args.model}")
    print(f"Config: {args.config}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output_dir}")
    print(f"TTA: {args.tta}")
    print(f"Save overlays: {args.save_overlays}")

    try:
        # Create enhanced predictor
        predictor = EnhancedTumorPredictor(
            model_path=args.model,
            config_path=args.config,
            device=args.device,
            tta=args.tta,
            sw_overlap=args.sw_overlap,
        )

        print(f"Using device: {predictor.device}")

        # Run inference
        input_path = Path(args.input)
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if input_path.suffix == '.json':
            # Datalist inference
            summary = predictor.predict_from_datalist(
                datalist_path=str(input_path),
                output_dir=str(output_path),
                save_overlays=args.save_overlays,
            )
        elif input_path.is_file():
            # Single file inference
            summary = predictor.predict_single_enhanced(
                image_path=str(input_path),
                output_dir=str(output_path),
                save_overlays=args.save_overlays,
            )
        elif input_path.is_dir():
            # Directory inference
            summary = predictor.predict_from_directory_enhanced(
                input_dir=str(input_path),
                output_dir=str(output_path),
                save_overlays=args.save_overlays,
            )
        else:
            print(f"Error: Input path does not exist: {args.input}")
            return

        print(f"Processed {summary.get('total_processed', 0)} images")
        print(f"Successful: {summary.get('successful', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print("Inference completed!")

    except Exception as e:
        print(f"Inference failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
