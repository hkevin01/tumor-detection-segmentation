"""
Tumor Detection Inference API

High-level programmatic interface for loading models and running inference
on medical imaging data with optional Test Time Augmentation (TTA).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import nibabel as nib
import numpy as np
import torch
from monai.inferers import SlidingWindowInferer

from ..utils.device import auto_device_resolve

# Setup logging
logger = logging.getLogger(__name__)


def load_model(
    model_path: Union[str, Path],
    config_path: Union[str, Path],
    device: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load a trained model from checkpoint with configuration.

    Args:
        model_path: Path to model checkpoint (.pth file)
        config_path: Path to model configuration (.json file)
        device: Target device ('cpu', 'cuda', 'auto', or None for auto)

    Returns:
        Dict containing loaded model, config, and device info

    Example:
        >>> model_info = load_model(
        ...     "models/unetr_brain.pth",
        ...     "config/recipes/unetr_multimodal.json"
        ... )
        >>> prediction = run_inference(model_info, "data/brain_scan.nii.gz")
    """
    model_path = Path(model_path)
    config_path = Path(config_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    # Load configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Resolve device
    if device is None or device == "auto":
        device = auto_device_resolve()
    device = torch.device(device)

    # Load model checkpoint
    checkpoint = torch.load(model_path, map_location=device)

    # Get model from config or checkpoint
    if 'model' in checkpoint:
        model = checkpoint['model']
    else:
        # Initialize model from config and load state dict
        from ..models import get_model  # Import from models module
        model = get_model(config['model'])
        model.load_state_dict(checkpoint['state_dict'])

    model = model.to(device)
    model.eval()

    logger.info(f"Loaded model from {model_path} on device {device}")

    return {
        'model': model,
        'config': config,
        'device': device,
        'model_path': str(model_path),
        'config_path': str(config_path)
    }


def run_inference(
    model_info: Dict[str, Any],
    input_path: Union[str, Path],
    roi_size: Optional[Tuple[int, ...]] = None,
    overlap: float = 0.25,
    tta: bool = False,
    sw_batch_size: int = 1
) -> np.ndarray:
    """
    Run sliding window inference on input image.

    Args:
        model_info: Model info dict from load_model()
        input_path: Path to input NIfTI image
        roi_size: ROI size for sliding window (auto from config if None)
        overlap: Overlap ratio for sliding window
        tta: Whether to use Test Time Augmentation
        sw_batch_size: Batch size for sliding window

    Returns:
        Numpy array with prediction probabilities (C, H, W, D)

    Example:
        >>> model_info = load_model("model.pth", "config.json")
        >>> prediction = run_inference(
        ...     model_info,
        ...     "brain_scan.nii.gz",
        ...     tta=True
        ... )
        >>> mask = np.argmax(prediction, axis=0)  # Get class labels
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    model = model_info['model']
    config = model_info['config']
    device = model_info['device']

    # Get ROI size from config if not specified
    if roi_size is None:
        roi_size = tuple(config.get('inference', {}).get('roi_size', [128, 128, 128]))

    # Load and preprocess image
    image_data = _load_and_preprocess_image(input_path, config)
    image_tensor = torch.from_numpy(image_data).unsqueeze(0).to(device)

    # Setup sliding window inferer
    inferer = SlidingWindowInferer(
        roi_size=roi_size,
        sw_batch_size=sw_batch_size,
        overlap=overlap,
        mode="gaussian",
        sigma_scale=0.125,
        padding_mode="constant",
        cval=0.0,
    )

    # Run inference
    with torch.no_grad():
        if tta:
            # Test Time Augmentation - flip along different axes and average
            predictions = []

            # Original
            pred = inferer(image_tensor, model)
            predictions.append(pred)

            # Flip sagittal (axis=-1)
            pred_flip_s = inferer(torch.flip(image_tensor, [-1]), model)
            pred_flip_s = torch.flip(pred_flip_s, [-1])
            predictions.append(pred_flip_s)

            # Flip coronal (axis=-2)
            pred_flip_c = inferer(torch.flip(image_tensor, [-2]), model)
            pred_flip_c = torch.flip(pred_flip_c, [-2])
            predictions.append(pred_flip_c)

            # Average all predictions
            prediction = torch.mean(torch.stack(predictions), dim=0)
        else:
            # Standard inference
            prediction = inferer(image_tensor, model)

    # Convert to numpy and remove batch dimension
    prediction = prediction.squeeze(0).cpu().numpy()

    logger.info(f"Inference completed for {input_path}, output shape: {prediction.shape}")

    return prediction


def save_mask(
    prediction: np.ndarray,
    output_path: Union[str, Path],
    reference_path: Optional[Union[str, Path]] = None,
    affine: Optional[np.ndarray] = None,
    threshold: float = 0.5
) -> None:
    """
    Save prediction as NIfTI mask file.

    Args:
        prediction: Prediction array (C, H, W, D) or (H, W, D)
        output_path: Path for output NIfTI file
        reference_path: Reference image for affine/header info
        affine: Affine transformation matrix (used if reference_path is None)
        threshold: Threshold for binary masks (unused for multi-class)

    Example:
        >>> prediction = run_inference(model_info, "brain_scan.nii.gz")
        >>> save_mask(
        ...     prediction,
        ...     "segmentation.nii.gz",
        ...     reference_path="brain_scan.nii.gz"
        ... )
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Handle multi-class predictions
    if prediction.ndim == 4 and prediction.shape[0] > 1:
        # Convert probabilities to class labels
        mask = np.argmax(prediction, axis=0).astype(np.uint8)
    elif prediction.ndim == 4 and prediction.shape[0] == 1:
        # Single class probability - threshold
        mask = (prediction[0] > threshold).astype(np.uint8)
    else:
        # Already a mask
        mask = prediction.astype(np.uint8)

    # Get affine matrix
    if reference_path is not None:
        reference_path = Path(reference_path)
        if reference_path.exists():
            ref_img = nib.load(reference_path)
            affine = ref_img.affine
            header = ref_img.header
        else:
            logger.warning(f"Reference image not found: {reference_path}")
            affine = np.eye(4) if affine is None else affine
            header = None
    else:
        affine = np.eye(4) if affine is None else affine
        header = None

    # Create and save NIfTI image
    nifti_img = nib.Nifti1Image(mask, affine, header)
    nib.save(nifti_img, output_path)

    logger.info(f"Saved mask to {output_path}")


def generate_overlays(
    image_path: Union[str, Path],
    prediction: np.ndarray,
    output_dir: Union[str, Path],
    slices: Optional[List[int]] = None,
    ground_truth_path: Optional[Union[str, Path]] = None,
    alpha: float = 0.3
) -> List[Path]:
    """
    Generate overlay visualizations of predictions on original images.

    Args:
        image_path: Path to original image
        prediction: Prediction array (C, H, W, D) or (H, W, D)
        output_dir: Directory to save overlay images
        slices: Specific slices to visualize (auto-select if None)
        ground_truth_path: Optional ground truth for comparison
        alpha: Transparency for overlay

    Returns:
        List of paths to generated overlay images

    Example:
        >>> prediction = run_inference(model_info, "brain_scan.nii.gz")
        >>> overlay_paths = generate_overlays(
        ...     "brain_scan.nii.gz",
        ...     prediction,
        ...     "outputs/overlays/"
        ... )
    """
    import matplotlib.pyplot as plt

    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load original image
    image_img = nib.load(image_path)
    image_data = image_img.get_fdata()

    # Process prediction
    if prediction.ndim == 4:
        if prediction.shape[0] > 1:
            # Multi-class - convert to labels
            pred_mask = np.argmax(prediction, axis=0)
        else:
            # Single class - threshold
            pred_mask = (prediction[0] > 0.5).astype(int)
    else:
        pred_mask = prediction

    # Load ground truth if provided
    gt_mask = None
    if ground_truth_path is not None:
        gt_path = Path(ground_truth_path)
        if gt_path.exists():
            gt_img = nib.load(gt_path)
            gt_mask = gt_img.get_fdata()

    # Auto-select slices if not provided
    if slices is None:
        # Find slices with significant prediction content
        slice_sums = np.sum(pred_mask, axis=(0, 1))
        meaningful_slices = np.where(slice_sums > 0)[0]
        if len(meaningful_slices) > 0:
            # Select a few representative slices
            step = max(1, len(meaningful_slices) // 5)
            slices = meaningful_slices[::step][:5]
        else:
            # Fallback to middle slices
            slices = [image_data.shape[2] // 4,
                     image_data.shape[2] // 2,
                     3 * image_data.shape[2] // 4]

    # Color map for overlays
    colors = ['red', 'blue', 'green', 'yellow', 'purple']

    generated_files = []

    for slice_idx in slices:
        if slice_idx >= image_data.shape[2]:
            continue

        # Create figure
        fig, axes = plt.subplots(1, 2 if gt_mask is None else 3,
                                figsize=(15 if gt_mask is None else 20, 5))
        if gt_mask is None and not isinstance(axes, np.ndarray):
            axes = [axes]
        elif gt_mask is not None and not isinstance(axes, np.ndarray):
            axes = [axes]

        # Original image
        ax_idx = 0
        axes[ax_idx].imshow(image_data[:, :, slice_idx], cmap='gray')
        axes[ax_idx].set_title(f'Original - Slice {slice_idx}')
        axes[ax_idx].axis('off')

        # Prediction overlay
        ax_idx += 1
        axes[ax_idx].imshow(image_data[:, :, slice_idx], cmap='gray')

        # Overlay prediction
        pred_slice = pred_mask[:, :, slice_idx]
        if np.any(pred_slice > 0):
            # Create colored overlay
            overlay = np.zeros((*pred_slice.shape, 4))
            unique_labels = np.unique(pred_slice[pred_slice > 0])

            for i, label in enumerate(unique_labels):
                color_idx = i % len(colors)
                mask = pred_slice == label

                # Set color
                if colors[color_idx] == 'red':
                    overlay[mask] = [1, 0, 0, alpha]
                elif colors[color_idx] == 'blue':
                    overlay[mask] = [0, 0, 1, alpha]
                elif colors[color_idx] == 'green':
                    overlay[mask] = [0, 1, 0, alpha]
                elif colors[color_idx] == 'yellow':
                    overlay[mask] = [1, 1, 0, alpha]
                elif colors[color_idx] == 'purple':
                    overlay[mask] = [1, 0, 1, alpha]

            axes[ax_idx].imshow(overlay)

        axes[ax_idx].set_title(f'Prediction Overlay - Slice {slice_idx}')
        axes[ax_idx].axis('off')

        # Ground truth overlay if available
        if gt_mask is not None:
            ax_idx += 1
            axes[ax_idx].imshow(image_data[:, :, slice_idx], cmap='gray')

            gt_slice = gt_mask[:, :, slice_idx]
            if np.any(gt_slice > 0):
                # Create colored overlay for GT
                gt_overlay = np.zeros((*gt_slice.shape, 4))
                gt_unique = np.unique(gt_slice[gt_slice > 0])

                for i, label in enumerate(gt_unique):
                    color_idx = i % len(colors)
                    mask = gt_slice == label

                    # Set color with different alpha for distinction
                    if colors[color_idx] == 'red':
                        gt_overlay[mask] = [1, 0, 0, alpha + 0.2]
                    elif colors[color_idx] == 'blue':
                        gt_overlay[mask] = [0, 0, 1, alpha + 0.2]
                    elif colors[color_idx] == 'green':
                        gt_overlay[mask] = [0, 1, 0, alpha + 0.2]
                    elif colors[color_idx] == 'yellow':
                        gt_overlay[mask] = [1, 1, 0, alpha + 0.2]
                    elif colors[color_idx] == 'purple':
                        gt_overlay[mask] = [1, 0, 1, alpha + 0.2]

                axes[ax_idx].imshow(gt_overlay)

            axes[ax_idx].set_title(f'Ground Truth - Slice {slice_idx}')
            axes[ax_idx].axis('off')

        plt.tight_layout()

        # Save figure
        output_file = output_dir / f"overlay_slice_{slice_idx:03d}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        generated_files.append(output_file)
        logger.info(f"Generated overlay: {output_file}")

    return generated_files


def _load_and_preprocess_image(
    image_path: Path,
    config: Dict[str, Any]
) -> np.ndarray:
    """Load and preprocess image for inference."""
    # Load image
    image_img = nib.load(image_path)
    image_data = image_img.get_fdata()

    # Ensure 4D (add channel dim if needed)
    if image_data.ndim == 3:
        image_data = image_data[np.newaxis, ...]

    # Normalize (basic intensity normalization)
    for c in range(image_data.shape[0]):
        channel_data = image_data[c]
        if np.std(channel_data) > 0:
            # Z-score normalization
            mean_val = np.mean(channel_data[channel_data > 0])
            std_val = np.std(channel_data[channel_data > 0])
            image_data[c] = (channel_data - mean_val) / (std_val + 1e-8)

    return image_data.astype(np.float32)
