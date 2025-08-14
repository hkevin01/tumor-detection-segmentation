"""
Visualization utilities for tumor detection overlays.

Functions here help create labeled overlay images from an input medical
image and a predicted segmentation mask. Supports 2D and 3D volumes by
selecting a representative slice for visualization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm
    MPL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    MPL_AVAILABLE = False


def _to_numpy(img: np.ndarray) -> np.ndarray:
    """Ensure input is a numpy array of type float32."""
    if not isinstance(img, np.ndarray):
        raise TypeError("Expected numpy.ndarray inputs")
    arr = img.astype(np.float32, copy=False)
    return arr


def normalize_image(img: np.ndarray) -> np.ndarray:
    """Min-max normalize an image to [0, 1] range safely."""
    arr = _to_numpy(img)
    if arr.size == 0:
        return arr
    vmin = np.nanmin(arr)
    vmax = np.nanmax(arr)
    if vmax > vmin:
        arr = (arr - vmin) / (vmax - vmin)
    else:
        arr = np.zeros_like(arr, dtype=np.float32)
    return np.clip(arr, 0.0, 1.0)


def select_slice(
    image: np.ndarray,
    mask: np.ndarray,
    strategy: str = "largest",
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Select a representative 2D slice from a 3D volume for visualization.

    Args:
        image: 2D or 3D image array (H, W) or (D, H, W)
        mask: 2D or 3D mask array with same shape as image
        strategy: 'largest' (slice with max tumor area) or 'middle'

    Returns:
        (image_slice, mask_slice, slice_index)
    """
    img = _to_numpy(image)
    msk = _to_numpy(mask)

    if img.ndim == 2:
        return img, msk, 0

    if img.ndim != 3 or msk.ndim != 3:
        raise ValueError(
            "image and mask must be 2D or 3D with matching shapes"
        )

    if strategy == "middle":
        z = img.shape[0] // 2
    else:
        # largest area slice by counting nonzero mask pixels
        areas = (msk > 0).reshape(msk.shape[0], -1).sum(axis=1)
        if np.all(areas == 0):
            z = img.shape[0] // 2
        else:
            z = int(np.argmax(areas))

    return img[z], msk[z], z


def create_overlay(
    image_slice: np.ndarray,
    mask_slice: np.ndarray,
    alpha: float = 0.4,
    cmap: str = "jet",
) -> np.ndarray:
    """
    Create an RGB overlay of the mask on top of the grayscale image slice.

    Returns an array of shape (H, W, 3) in float32 [0,1].
    """
    if not MPL_AVAILABLE:  # pragma: no cover
        raise RuntimeError("matplotlib is required for overlay creation")

    base = normalize_image(image_slice)
    mask_bin = (mask_slice > 0).astype(np.float32)

    # Colorize mask
    colormap = cm.get_cmap(cmap)
    mask_rgb = colormap(mask_bin)[..., :3].astype(np.float32)

    # Stack grayscale to RGB
    base_rgb = np.stack([base, base, base], axis=-1)

    # Alpha blend
    overlay = (1 - alpha) * base_rgb + alpha * mask_rgb * (mask_bin[..., None])
    return np.clip(overlay, 0.0, 1.0).astype(np.float32)


def save_overlay(
    image: np.ndarray,
    mask: np.ndarray,
    out_path: str | Path,
    alpha: float = 0.4,
    cmap: str = "jet",
    title: Optional[str] = None,
    dpi: int = 150,
    strategy: str = "largest",
) -> Path:
    """Select a slice, create overlay, and save to disk as PNG."""
    if not MPL_AVAILABLE:  # pragma: no cover
        raise RuntimeError("matplotlib is required for saving overlay")

    img_s, msk_s, z = select_slice(image, mask, strategy=strategy)
    overlay = create_overlay(img_s, msk_s, alpha=alpha, cmap=cmap)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.imshow(overlay)
    plt.axis('off')
    if title:
        plt.title(f"{title} | slice {z}")
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()
    return out_path
