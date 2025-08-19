"""
Visualization callbacks for training monitoring.

This module provides callback functions for saving visualization outputs
during training and validation.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import torch


def save_overlay_panel(
    image: torch.Tensor,
    label_oh: torch.Tensor,
    pred_oh: torch.Tensor,
    out_path: Path,
    slices: Optional[List[int]] = None,
) -> None:
    """
    Save overlay panel with multiple slices.

    Args:
        image: (C, H, W, D) input image tensor
        label_oh: (C_out, H, W, D) one-hot ground truth tensor
        pred_oh: (C_out, H, W, D) one-hot prediction tensor
        out_path: Output file path
        slices: List of z indices to visualize. If None, uses [25%, 50%, 75%]
    """
    # Use first channel as background
    img = image[0].detach().cpu().float().numpy()
    _, _, D = img.shape

    # Default to evenly spaced slices
    if slices is None:
        slices = [D // 4, D // 2, 3 * D // 4]

    # Ensure slices are valid
    slices = [max(0, min(s, D-1)) for s in slices]

    # Get class 1 if available, else max over classes
    if label_oh.shape[0] > 1:
        gt = label_oh[1].detach().cpu().numpy()
        pr = pred_oh[1].detach().cpu().numpy()
    else:
        gt = label_oh.max(0).values.detach().cpu().numpy()
        pr = pred_oh.max(0).values.detach().cpu().numpy()

    n_slices = len(slices)
    fig, axes = plt.subplots(1, n_slices, figsize=(6 * n_slices, 6))

    # Ensure axes is always a list
    if n_slices == 1:
        axes = [axes]

    for i, z in enumerate(slices):
        base = img[..., z]
        base = (base - base.min()) / (base.max() - base.min() + 1e-8)

        gt_slice = gt[..., z]
        pr_slice = pr[..., z]

        axes[i].axis("off")
        axes[i].imshow(base, cmap="gray")

        # Overlay ground truth (green) and prediction (red)
        axes[i].imshow(
            np.ma.masked_where(gt_slice == 0, gt_slice),
            cmap="Greens", alpha=0.3
        )
        axes[i].imshow(
            np.ma.masked_where(pr_slice == 0, pr_slice),
            cmap="Reds", alpha=0.3
        )

        axes[i].set_title(f"Slice {z}/{D-1}", fontsize=12)

    # Add overall title
    fig.suptitle("Validation Overlay (Green=GT, Red=Pred)", fontsize=14)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close()


def save_probability_panel(
    image: torch.Tensor,
    prob_map: torch.Tensor,
    out_path: Path,
    slices: Optional[List[int]] = None,
    class_name: str = "tumor",
) -> None:
    """
    Save probability heatmap panel.

    Args:
        image: (C, H, W, D) input image tensor
        prob_map: (H, W, D) probability tensor (0-1)
        out_path: Output file path
        slices: List of z indices to visualize
        class_name: Name of the class for the title
    """
    # Use first channel as background
    img = image[0].detach().cpu().float().numpy()
    probs = prob_map.detach().cpu().numpy()
    _, _, D = img.shape

    # Default to evenly spaced slices
    if slices is None:
        slices = [D // 4, D // 2, 3 * D // 4]

    # Ensure slices are valid
    slices = [max(0, min(s, D-1)) for s in slices]

    n_slices = len(slices)
    fig, axes = plt.subplots(1, n_slices, figsize=(6 * n_slices, 6))

    # Ensure axes is always a list
    if n_slices == 1:
        axes = [axes]

    for i, z in enumerate(slices):
        base = img[..., z]
        base = (base - base.min()) / (base.max() - base.min() + 1e-8)
        prob_slice = probs[..., z]

        axes[i].axis("off")
        axes[i].imshow(base, cmap="gray")

        # Overlay probability heatmap (mask low probabilities)
        axes[i].imshow(
            np.ma.masked_where(prob_slice < 0.1, prob_slice),
            cmap="hot", alpha=0.6, vmin=0, vmax=1
        )

        axes[i].set_title(f"Slice {z}/{D-1}", fontsize=12)

    # Add overall title
    fig.suptitle(f"{class_name.title()} Probability Map", fontsize=14)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close()


def save_val_overlays(
    batch_images: torch.Tensor,
    batch_predictions: torch.Tensor,
    batch_ground_truth: torch.Tensor,
    out_dir: Path,
    batch_idx: int,
    max_samples: int = 2,
    slices: Optional[List[int]] = None,
) -> int:
    """
    Save validation overlays for a batch.

    Args:
        batch_images: (B, C, H, W, D) batch of images
        batch_predictions: (B, C_out, H, W, D) batch of predictions
        batch_ground_truth: (B, C_out, H, W, D) batch of ground truth
        out_dir: Output directory
        batch_idx: Batch index for filename
        max_samples: Maximum number of samples to save from batch
        slices: List of z indices to visualize

    Returns:
        Number of overlays saved
    """
    saved = 0
    batch_size = min(batch_images.shape[0], max_samples)

    for i in range(batch_size):
        img = batch_images[i]  # (C, H, W, D)
        pred = batch_predictions[i]  # (C_out, H, W, D)
        gt = batch_ground_truth[i]  # (C_out, H, W, D)

        out_path = out_dir / f"val_overlay_b{batch_idx:03d}_s{i:02d}.png"
        save_overlay_panel(img, gt, pred, out_path, slices)
        saved += 1

    return saved


def save_training_summary_plot(
    train_losses: List[float],
    val_metrics: List[float],
    out_path: Path,
    metric_name: str = "Dice",
) -> None:
    """
    Save training summary plot.

    Args:
        train_losses: List of training losses per epoch
        val_metrics: List of validation metrics per epoch
        out_path: Output file path
        metric_name: Name of the validation metric
    """
    epochs = range(1, len(train_losses) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Training loss
    ax1.plot(epochs, train_losses, 'b-', linewidth=2)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Training Loss')
    ax1.set_title('Training Loss Over Time')
    ax1.grid(True, alpha=0.3)

    # Validation metric
    if val_metrics:
        val_epochs = range(1, len(val_metrics) + 1)
        ax2.plot(val_epochs, val_metrics, 'r-', linewidth=2, marker='o')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel(f'Validation {metric_name}')
        ax2.set_title(f'Validation {metric_name} Over Time')
        ax2.grid(True, alpha=0.3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
