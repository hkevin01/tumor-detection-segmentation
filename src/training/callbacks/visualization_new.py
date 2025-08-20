#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import torch


def _normalize_img(img: np.ndarray) -> np.ndarray:
    img = img.astype(np.float32)
    mn, mx = float(img.min()), float(img.max())
    if mx <= mn + 1e-8:
        return np.zeros_like(img, dtype=np.float32)
    return (img - mn) / (mx - mn)


def _parse_slices(D: int, slices: Optional[Sequence[int] | str]) -> list[int]:
    if slices is None or (isinstance(slices, str) and slices.lower() == "auto"):
        return [max(0, D // 4), max(0, D // 2), max(0, (3 * D) // 4)]
    if isinstance(slices, str):
        # e.g., "30,50,70"
        try:
            return [int(s.strip()) for s in slices.split(",") if s.strip()]
        except Exception:
            return [max(0, D // 2)]
    # assume sequence of ints
    out = []
    for z in slices:
        try:
            out.append(int(z))
        except Exception:
            continue
    if not out:
        out = [max(0, D // 2)]
    return out


def save_overlay_panel(
    image_ch_first: torch.Tensor,
    label_onehot: Optional[torch.Tensor],
    pred_onehot: torch.Tensor,
    out_path: Path,
    slices: Optional[Sequence[int] | str] = "auto",
    base_modality: int = 0,
    cmap_gt: str = "Greens",
    cmap_pred: str = "Reds",
    alpha_gt: float = 0.30,
    alpha_pred: float = 0.30,
    class_index: Optional[int] = None,
) -> None:
    """
    Save a 1xK panel of axial overlays:
      - Background: grayscale base modality
      - Overlays: GT (green), prediction (red)

    image_ch_first: (C, H, W, D)
    label_onehot:   (C_out, H, W, D) or None (if you only have predictions)
    pred_onehot:    (C_out, H, W, D)
    out_path:       output PNG path
    slices:         "auto" (25/50/75%) or list of z indices
    class_index:    which class channel to visualize; if None, use class 1 if exists else max over classes
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = image_ch_first[base_modality].detach().cpu().float().numpy()
    H, W, D = img.shape
    z_list = _parse_slices(D, slices)

    # choose class
    def pick_channel(t: torch.Tensor) -> np.ndarray:
        # t: (C_out, H, W, D)
        if class_index is not None and class_index < t.shape[0]:
            return t[class_index].detach().cpu().float().numpy()
        if t.shape[0] > 1:
            return t[1].detach().cpu().float().numpy()
        # if single channel, return it
        return t[0].detach().cpu().float().numpy()

    pr_mask_3d = pick_channel(pred_onehot)
    gt_mask_3d = pick_channel(label_onehot) if label_onehot is not None else None

    fig, axes = plt.subplots(1, len(z_list), figsize=(5 * len(z_list), 5))
    if len(z_list) == 1:
        axes = [axes]

    for ax, z in zip(axes, z_list):
        z = int(np.clip(z, 0, D - 1))
        base = _normalize_img(img[..., z])
        ax.imshow(base, cmap="gray")
        if gt_mask_3d is not None:
            ax.imshow(np.ma.masked_where(gt_mask_3d[..., z] == 0, gt_mask_3d[..., z]), cmap=cmap_gt, alpha=alpha_gt)
        ax.imshow(np.ma.masked_where(pr_mask_3d[..., z] == 0, pr_mask_3d[..., z]), cmap=cmap_pred, alpha=alpha_pred)
        ax.set_title(f"z={z}")
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def save_prob_panel(
    image_ch_first: torch.Tensor,
    prob_logits_or_probs: torch.Tensor,
    out_path: Path,
    slices: Optional[Sequence[int] | str] = "auto",
    base_modality: int = 0,
    class_index: int = 1,
    apply_softmax: bool = True,
    cmap_prob: str = "magma",
    alpha_prob: float = 0.50,
) -> None:
    """
    Save probability heatmaps for a single class as overlays on the base image.
    prob_logits_or_probs: (C_out, H, W, D) logits or probabilities
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = image_ch_first[base_modality].detach().cpu().float().numpy()
    H, W, D = img.shape
    z_list = _parse_slices(D, slices)

    t = prob_logits_or_probs.detach().cpu().float()
    if apply_softmax:
        t = torch.softmax(t, dim=0)
    class_index = int(np.clip(class_index, 0, t.shape[0] - 1))
    prob3d = t[class_index].numpy()

    fig, axes = plt.subplots(1, len(z_list), figsize=(5 * len(z_list), 5))
    if len(z_list) == 1:
        axes = [axes]

    for ax, z in zip(axes, z_list):
        z = int(np.clip(z, 0, D - 1))
        base = _normalize_img(img[..., z])
        ax.imshow(base, cmap="gray")
        ax.imshow(prob3d[..., z], cmap=cmap_prob, alpha=alpha_prob, vmin=0.0, vmax=1.0)
        ax.set_title(f"Prob class={class_index}, z={z}")
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


# Backward compatibility aliases
save_probability_panel = save_prob_panel
