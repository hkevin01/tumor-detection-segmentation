#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, cast

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from monai.data import decollate_batch
from monai.inferers import SlidingWindowInferer
from monai.losses import DiceCELoss
from monai.metrics import DiceMetric
from monai.networks.nets import UNETR, UNet
from monai.transforms import AsDiscrete
from torch.utils.data import DataLoader

# Project loaders and transforms
from src.data.loaders_monai import load_monai_decathlon
from src.data.transforms_presets import (get_transforms_brats_like,
                                         get_transforms_ct_liver)
from src.training.callbacks.visualization import save_overlay_panel

# Optional dependency: MLflow
MLFLOW_AVAILABLE = importlib.util.find_spec("mlflow") is not None


def _mlflow():
    """Return mlflow module if installed, else None."""
    if not MLFLOW_AVAILABLE:
        return None
    return importlib.import_module("mlflow")


def set_determinism(seed: int = 42, enforce: bool = True) -> None:
    import random
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)
    if enforce:
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Enhanced training with MONAI datasets"
    )
    p.add_argument(
        "--config",
        required=True,
        help="Path to base training config (JSON)",
    )
    p.add_argument(
        "--dataset-config",
        help=(
            "Path to dataset config (JSON). If monai_decathlon, will "
            "auto-download"
        ),
    )
    p.add_argument(
        "--output-dir",
        default="models/unetr",
        help="Directory to write checkpoints and logs",
    )
    p.add_argument("--epochs", type=int, default=None, help="Override epochs")
    p.add_argument(
        "--amp", action="store_true", help="Enable mixed precision (AMP)"
    )
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument(
        "--no-deterministic",
        action="store_true",
        help="Allow non-deterministic ops",
    )
    p.add_argument(
        "--device", default=None, help="cpu | cuda | cuda:0 | mps | auto"
    )
    p.add_argument(
        "--resume", default=None, help="Path to checkpoint to resume from"
    )
    p.add_argument(
        "--val-interval", type=int, default=1, help="Validate every N epochs"
    )
    # A) Sliding-window overlap CLI
    p.add_argument(
        "--sw-overlap",
        type=float,
        default=0.25,
        help="Sliding window overlap for validation/inference",
    )
    # C) Overlays
    p.add_argument(
        "--save-overlays",
        action="store_true",
        help="Save simple validation overlays each eval",
    )
    p.add_argument(
        "--overlays-max",
        type=int,
        default=2,
        help="Max number of validation overlays to save per eval",
    )
    # D) Validation control
    p.add_argument(
        "--val-max-batches",
        type=int,
        default=0,
        help="Max validation batches per eval (0=all)",
    )
    # E) Probability maps
    p.add_argument(
        "--save-prob-maps",
        action="store_true",
        help="Save probability heatmaps for tumor class",
    )
    return p.parse_args()


def build_transforms_from_dataset_cfg(ds_cfg: Dict):
    spacing = tuple(ds_cfg.get("spacing", (1.0, 1.0, 1.0)))
    name = ds_cfg.get("transforms", "brats_like")
    if name == "brats_like":
        return get_transforms_brats_like(spacing=spacing)
    if name == "ct_liver":
        return get_transforms_ct_liver(spacing=spacing)
    return get_transforms_brats_like(spacing=spacing)


def build_model_from_cfg(
    cfg: Dict, in_channels: int = 4, out_channels: int = 2
) -> nn.Module:
    arch = cfg.get("model", {}).get("arch", "unetr").lower()
    if arch == "unetr":
        return UNETR(
            in_channels=in_channels,
            out_channels=out_channels,
            img_size=tuple(
                cfg.get("model", {}).get("img_size", [128, 128, 128])
            ),
            feature_size=cfg.get("model", {}).get("feature_size", 16),
            hidden_size=cfg.get("model", {}).get("hidden_size", 768),
            mlp_dim=cfg.get("model", {}).get("mlp_dim", 3072),
            num_heads=cfg.get("model", {}).get("num_heads", 12),
            pos_embed="perceptron",
            norm_name="instance",
            res_block=True,
            dropout_rate=cfg.get("model", {}).get("dropout", 0.0),
        )
    return UNet(
        spatial_dims=3,
        in_channels=in_channels,
        out_channels=out_channels,
        channels=cfg.get("model", {}).get("channels", [16, 32, 64, 128, 256]),
        strides=cfg.get("model", {}).get("strides", [2, 2, 2, 2]),
        num_res_units=cfg.get("model", {}).get("num_res_units", 2),
        norm=cfg.get("model", {}).get("norm", "INSTANCE"),
        dropout=cfg.get("model", {}).get("dropout", 0.0),
    )


def get_device(arg_device: Optional[str]) -> torch.device:
    if arg_device in (None, "auto"):
        if torch.cuda.is_available():
            return torch.device("cuda")
        if getattr(torch.backends, "mps", None) and \
                torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(arg_device)


def infer_in_channels_from_loader(loader: DataLoader, default: int = 4) -> int:
    """
    B) Inspect a single batch to determine input channels robustly.
    Does not permanently consume the iterator for training.
    """
    it = iter(loader)
    try:
        sample = next(it)
    except StopIteration:
        return default
    img = sample["image"]
    if img.ndim >= 5:
        return int(img.shape[1])
    return default


def save_prob_map_png(
    image_chn_first: torch.Tensor,
    prob_tumor: torch.Tensor,
    out_path: Path,
    slices: Optional[list] = None,
) -> None:
    """
    Save probability heatmap for tumor class.
    image_chn_first: (C, H, W, D) tensor (float)
    prob_tumor: (H, W, D) tensor (0-1 probabilities)
    slices: Optional list of z indices. If None, uses middle slice.
    """
    # use first modality as background image
    img = image_chn_first[0].detach().cpu().float().numpy()
    probs = prob_tumor.detach().cpu().numpy()
    _, _, D = img.shape

    # Default to middle slice if no slices specified
    if slices is None:
        slices = [D // 2]

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
        prob_slice = probs[..., z]

        axes[i].axis("off")
        axes[i].imshow(base, cmap="gray")
        # Overlay probability heatmap
        axes[i].imshow(
            np.ma.masked_where(prob_slice < 0.1, prob_slice),
            cmap="hot", alpha=0.6, vmin=0, vmax=1
        )
        axes[i].set_title(f"Prob Map Slice {z}/{D-1}", fontsize=10)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close()


def train_one_epoch(
    model,
    loader: DataLoader,
    optimizer,
    loss_fn,
    device,
    scaler: Optional[torch.cuda.amp.GradScaler] = None,
):
    model.train()
    epoch_loss = 0.0
    count = 0
    for batch in loader:
        images = batch["image"].to(device)
        labels = batch["label"].to(device)
        optimizer.zero_grad(set_to_none=True)
        if scaler is not None and device.type == "cuda":
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                logits = model(images)
                loss = loss_fn(logits, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(images)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()
        epoch_loss += float(loss.item())
        count += 1
    return epoch_loss / max(1, count)


@torch.no_grad()
def validate(
    model,
    loader: DataLoader,
    device,
    post_pred,
    post_label,
    roi_size: Optional[Tuple[int, int, int]] = None,
    sw_overlap: float = 0.25,
    save_overlays: bool = False,
    overlay_dir: Optional[Path] = None,
    overlays_max: int = 2,
    val_max_batches: int = 0,
    save_prob_maps: bool = False,
):
    model.eval()
    dice_metric = DiceMetric(include_background=False, reduction="mean")
    saved = 0
    prob_maps_saved = 0

    # A) Use config-provided roi_size if available,
    #    else fall back to full image shape
    inferers = {}  # cache per image shape if not using fixed roi_size

    for batch_idx, batch in enumerate(loader):
        # D) Validation batch limit
        if val_max_batches > 0 and batch_idx >= val_max_batches:
            break

        images = batch["image"].to(device)
        labels = batch["label"].to(device)

        if roi_size is not None:
            inferer = SlidingWindowInferer(
                roi_size=tuple(roi_size),
                sw_batch_size=1,
                overlap=sw_overlap,
            )
        else:
            # cache inferer per final spatial dims to avoid re-alloc
            key = tuple(images.shape[-3:])
            if key not in inferers:
                inferers[key] = SlidingWindowInferer(
                    roi_size=key, sw_batch_size=1, overlap=sw_overlap
                )
            inferer = inferers[key]

        logits = inferer(images, model)

        # E) Save probability maps before converting to discrete predictions
        if (save_prob_maps and overlay_dir is not None
                and prob_maps_saved < overlays_max):
            probs = torch.softmax(logits, dim=1)
            if probs.shape[1] > 1:  # Multi-class
                prob_tumor = probs[0, 1]  # Class 1 probabilities
            else:
                prob_tumor = probs[0, 0]  # Single class

            img_chn_first = images[0]  # (C,H,W,D)
            D = img_chn_first.shape[-1]
            slice_indices = [D // 4, D // 2, 3 * D // 4]

            prob_path = overlay_dir / f"val_probmap_{batch_idx:03d}.png"
            save_prob_map_png(
                img_chn_first, prob_tumor, prob_path, slice_indices
            )
            prob_maps_saved += 1

        preds_list = [post_pred(i) for i in decollate_batch(logits)]
        gts_list = [post_label(i) for i in decollate_batch(labels)]
        dice_metric(y_pred=preds_list, y=gts_list)

        # C) Optional overlays
        if save_overlays and overlay_dir is not None and saved < overlays_max:
            # Use first item in batch
            img_chn_first = images[0]  # (C,H,W,D)
            gt_onehot = gts_list[0]    # (C_out,H,W,D)
            pr_onehot = preds_list[0]  # (C_out,H,W,D)

            # Create multi-slice overlays (25%, 50%, 75% depth)
            D = img_chn_first.shape[-1]
            slice_indices = [D // 4, D // 2, 3 * D // 4]

            out_path = overlay_dir / f"val_overlay_{batch_idx:03d}.png"
            save_overlay_panel(
                image_ch_first=img_chn_first,
                label_onehot=gt_onehot,
                pred_onehot=pr_onehot,
                out_path=out_path,
                slices=slice_indices
            )
            saved += 1

    mean_dice = float(dice_metric.aggregate().item())
    dice_metric.reset()
    return {"dice": mean_dice, "n": len(loader)}


def main() -> int:
    args = parse_args()
    set_determinism(args.seed, enforce=not args.no_deterministic)

    # Device
    device = get_device(args.device)

    # Output dir
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir = out_dir / "overlays"

    # Load base config
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Dataset setup
    ds_cfg = None
    if args.dataset_config:
        with open(args.dataset_config, "r", encoding="utf-8") as f:
            ds_cfg = json.load(f)

    # Build transforms
    if ds_cfg:
        t_train, t_val = build_transforms_from_dataset_cfg(ds_cfg)
    else:
        t_train, t_val = get_transforms_brats_like()

    # Build DataLoaders using existing loader API
    if not (ds_cfg and ds_cfg.get("source") == "monai_decathlon"):
        raise RuntimeError("Requires --dataset-config (monai_decathlon).")

    train_key = ds_cfg.get("splits", {}).get("train_key", "training")
    val_key = ds_cfg.get("splits", {}).get("val_key", "validation")
    data_root = ds_cfg.get("data_root", "data/msd")
    dataset_id = ds_cfg.get("dataset_id", "Task01_BrainTumour")
    loader_cfg = ds_cfg.get("loader", {})

    train_res = load_monai_decathlon(
        root_dir=data_root,
        task=dataset_id,
        section=train_key,
        download=True,
        cache_rate=0.0,
        num_workers=int(loader_cfg.get("num_workers", 4)),
        transform=t_train,
        batch_size=int(loader_cfg.get("batch_size", 1)),
        pin_memory=bool(loader_cfg.get("pin_memory", False)),
    )
    val_res = load_monai_decathlon(
        root_dir=data_root,
        task=dataset_id,
        section=val_key,
        download=True,
        cache_rate=0.0,
        num_workers=int(loader_cfg.get("num_workers", 4)),
        transform=t_val,
        batch_size=int(loader_cfg.get("batch_size", 1)),
        pin_memory=bool(loader_cfg.get("pin_memory", False)),
    )

    train_loader = train_res["dataloader"]
    val_loader = val_res["dataloader"]
    # dataset meta (kept minimal to avoid unused warnings)

    # B) Infer in_channels from a real batch before building the model
    inferred_in_channels = infer_in_channels_from_loader(
        train_loader, default=4
    )
    out_channels = cfg.get("model", {}).get("out_channels", 2)
    model = build_model_from_cfg(
        cfg,
        in_channels=inferred_in_channels,
        out_channels=out_channels,
    ).to(device)

    # Loss, optimizer, scheduler
    loss_fn = DiceCELoss(
        to_onehot_y=True,
        softmax=True,
        include_background=False,
    )
    lr = cfg.get("optim", {}).get("lr", 1e-4)
    weight_decay = cfg.get("optim", {}).get("weight_decay", 0.0)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=weight_decay
    )
    epochs = args.epochs or cfg.get("trainer", {}).get("epochs", 50)
    val_interval = args.val_interval

    # AMP scaler
    scaler = (
        torch.cuda.amp.GradScaler()
        if (args.amp and device.type == "cuda")
        else None
    )

    # Resume if provided
    start_epoch = 0
    if args.resume is not None and os.path.isfile(args.resume):
        state = torch.load(args.resume, map_location="cpu")
        model.load_state_dict(state.get("model", state))
        if "optimizer" in state:
            optimizer.load_state_dict(state["optimizer"])
        start_epoch = state.get("epoch", 0)
        print(f"[INFO] Resumed from {args.resume} at epoch {start_epoch}")

    # Post transforms for validation metrics
    post_pred = AsDiscrete(argmax=True, to_onehot=out_channels)
    post_label = AsDiscrete(to_onehot=out_channels)

    # A) Determine roi_size for validation inferer from config if available
    roi_size_typed: Optional[Tuple[int, int, int]] = None
    model_img_size = cfg.get("model", {}).get("img_size", None)
    if isinstance(model_img_size, (list, tuple)) and len(model_img_size) == 3:
        roi_size_typed = cast(
            Tuple[int, int, int], tuple(int(x) for x in model_img_size)
        )

    # MLflow logging
    mlflow = _mlflow()
    if mlflow:
        mlflow.set_experiment(
            cfg.get("mlflow", {}).get("experiment", "medical-imaging")
        )
        run_name = cfg.get("mlflow", {}).get(
            "run_name", f"run-{int(time.time())}"
        )
        mlflow.start_run(run_name=run_name)
        mlflow.log_params({
            "arch": cfg.get("model", {}).get("arch", "unetr"),
            "in_channels": inferred_in_channels,
            "out_channels": out_channels,
            "lr": lr,
            "epochs": epochs,
            "amp": bool(scaler is not None),
            "dataset_task": ds_cfg.get("dataset_id") if ds_cfg else None,
            "seed": args.seed,
            "roi_size": (
                roi_size_typed if roi_size_typed is not None else "full"
            ),
            "sw_overlap": args.sw_overlap,
        })

    best_dice = -1.0
    best_ckpt = out_dir / "best.pt"

    for epoch in range(start_epoch, epochs):
        t0 = time.time()
        train_loss = train_one_epoch(
            model, train_loader, optimizer, loss_fn, device, scaler
        )
        dt = time.time() - t0

        print(
            f"[Ep {epoch+1}/{epochs}] loss={train_loss:.4f} "
            f"t={dt:.1f}s"
        )
        if mlflow:
            mlflow.log_metrics(
                {"train/loss": train_loss, "time/epoch_s": dt}, step=epoch
            )

        if (epoch + 1) % val_interval == 0:
            metrics = validate(
                model,
                val_loader,
                device,
                post_pred,
                post_label,
                roi_size=roi_size_typed,
                sw_overlap=args.sw_overlap,
                save_overlays=args.save_overlays,
                overlay_dir=overlays_dir,
                overlays_max=args.overlays_max,
                val_max_batches=args.val_max_batches,
                save_prob_maps=args.save_prob_maps,
            )
            dice = metrics["dice"]
            print(f"  [Val] mean_dice={dice:.4f}")
            if mlflow:
                mlflow.log_metric("val/dice", dice, step=epoch)
            if dice > best_dice:
                best_dice = dice
                state = {
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "epoch": epoch,
                }
                torch.save(state, best_ckpt)
                print(
                    f"  [CKPT] Saved best to {best_ckpt} "
                    f"(dice={best_dice:.4f})"
                )

    final_ckpt = out_dir / "last.pt"
    final_state = {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "epoch": epochs - 1,
    }
    torch.save(final_state, final_ckpt)
    print(
        f"[DONE] Saved final checkpoint to {final_ckpt}. "
        f"Best dice={best_dice:.4f}"
    )

    if mlflow:
        mlflow.log_artifact(str(best_ckpt))
        mlflow.log_artifact(str(final_ckpt))
        if args.save_overlays and overlays_dir.exists():
            # log a couple of overlay images
            for p in sorted(overlays_dir.glob("*.png"))[:3]:
                mlflow.log_artifact(str(p))
        mlflow.end_run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
