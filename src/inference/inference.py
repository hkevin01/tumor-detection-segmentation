"""
Inference module for tumor detection and segmentation.

This module provides functionality for running inference on new medical images
using trained models.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    import torch
    from monai.transforms.compose import Compose
    from monai.transforms.intensity.array import ScaleIntensity
    from monai.transforms.io.array import LoadImage
    from monai.transforms.spatial.array import Resize
    from monai.transforms.utility.array import EnsureChannelFirst, EnsureType
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# Add repo src to path for training imports when running as a script
sys.path.append(str(Path(__file__).parent.parent))


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

    def predict_single(self, image_path: str) -> Dict[str, Any]:
        """Run inference on a single image.

        Args:
            image_path: Path to input image

        Returns:
            Dictionary containing prediction results
        """
        # Preprocess image: path str -> Tensor (C, ...)
        img_tensor = self.transforms(image_path)
        if not torch.is_tensor(img_tensor):
            # Safety net if transforms didn't convert to tensor
            img_tensor = torch.as_tensor(img_tensor)

        # Add batch dimension and move to device
        image = img_tensor.unsqueeze(0).to(self.device)

        # Run inference
        with torch.no_grad():
            if self.use_tta:
                prediction = self._predict_with_tta(image)
            else:
                logits = self.model(image)
                probs = torch.softmax(logits, dim=1)
                prediction = torch.argmax(probs, dim=1)

        # Convert to numpy for easier handling
        prediction_np = prediction.cpu().numpy().squeeze()
        # Also export the preprocessed input image (channel squeezed)
        # for visualization purposes
        input_np = img_tensor.detach().cpu().numpy()
        if input_np.shape[0] == 1:
            input_np = np.squeeze(input_np, axis=0)

        return {
            "prediction": prediction_np,
            "input_image": input_np,
            "input_shape": image.shape,
            "output_shape": prediction.shape,
            "device": str(self.device),
            "tta": self.use_tta,
        }

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


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(
        description="Run tumor segmentation inference"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to model checkpoint"
    )
    parser.add_argument(
        "--config", type=str, default="config.json", help="Config file path"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Input image or directory"
    )
    parser.add_argument(
        "--output", type=str, default="./results", help="Output directory"
    )
    parser.add_argument(
        "--device", type=str, default="auto", help="Device (auto, cpu, cuda)"
    )
    parser.add_argument(
        "--tta",
        action="store_true",
        help="Enable simple flip-based test-time augmentation",
    )

    args = parser.parse_args()

    if not DEPENDENCIES_AVAILABLE:
        print("Error: Required dependencies not available.")
        print("Please install: pip install -r requirements.txt")
        return

    print("Tumor Segmentation Inference")
    print("=" * 35)
    print(f"Model: {args.model}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")

    try:
        # Create predictor
        predictor = TumorPredictor(
            model_path=args.model,
            config_path=args.config,
            device=args.device,
            tta=bool(args.tta),
        )

        print(f"Using device: {predictor.device}")

        # Run inference
        input_path = Path(args.input)

        if input_path.is_file():
            # Single file inference
            result = predictor.predict_single(str(input_path))

            # Save result
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            np.save(output_path / "prediction.npy", result["prediction"])

            print(f"Prediction saved to: {output_path / 'prediction.npy'}")

        elif input_path.is_dir():
            # Directory inference
            summary = predictor.predict_from_directory(
                input_dir=str(input_path),
                output_dir=args.output,
            )

            print(f"Processed {summary['total_processed']} images")
            print(f"Successful: {summary['successful']}")
            print(f"Failed: {summary['failed']}")

        else:
            print(f"Error: Input path does not exist: {args.input}")
            return

        print("Inference completed!")

    except (RuntimeError, ValueError, OSError) as e:
        print(f"Inference failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
