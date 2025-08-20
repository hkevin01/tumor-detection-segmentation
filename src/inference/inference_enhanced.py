#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced inference script with overlay export capabilities.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Optional

import nibabel as nib
import numpy as np
import torch
from monai.data import DataLoader, Dataset
from monai.inferers import SlidingWindowInferer
from monai.networks.nets import UNETR, UNet
from monai.transforms import (AsDiscrete, Compose, EnsureChannelFirstd,
                              EnsureTyped, LoadImaged)
from monai.utils import set_determinism

from src.data.loaders_monai import load_monai_decathlon
from src.data.transforms_presets import (get_transforms_brats_like,
                                         get_transforms_ct_liver)
from src.training.callbacks.visualization import (save_overlay_panel,
                                                  save_prob_panel)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inference with overlay export")
    p.add_argument("--input", required=False, help="Input dir/file or Decathlon datalist JSON. If omitted, use --dataset-config.")
    p.add_argument("--dataset-config", help="Dataset config JSON (monai_decathlon) to build loaders for val split.")
    p.add_argument("--model", required=True, help="Path to model checkpoint (.pt)")
    p.add_argument("--config", required=True, help="Training config (JSON) used to build the model (reads model.img_size, out_channels, arch)")
    p.add_argument("--output-dir", default="reports/inference_exports", help="Directory to write outputs")
    p.add_argument("--device", default="auto", help="auto|cpu|cuda|cuda:0|mps")
    p.add_argument("--amp", action="store_true", help="Use mixed precision on CUDA")
    p.add_argument("--tta", action="store_true", help="Simple flip TTA (axes 2 and/or 3)")
    p.add_argument("--save-overlays", action="store_true", help="Save multi-slice overlay PNGs")
    p.add_argument("--save-prob-maps", action="store_true", help="Save probability heatmaps for --class-index")
    p.add_argument("--class-index", type=int, default=1, help="Class index for overlay/prob maps")
    p.add_argument("--slices", default="auto", help="Comma-separated z indices or 'auto'")
    p.add_argument("--sw-overlap", type=float, default=0.25, help="Sliding window overlap")
    p.add_argument("--batch-size", type=int, default=1, help="Batch size for Decathlon val loader")
    p.add_argument("--num-workers", type=int, default=0, help="Workers for Decathlon val loader")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def get_device(name: Optional[str]) -> torch.device:
    if name in (None, "auto"):
        if torch.cuda.is_available():
            return torch.device("cuda")
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(name)


def build_model(cfg: Dict, in_channels: int, out_channels: int):
    arch = cfg.get("model", {}).get("arch", "unetr").lower()
    if arch == "unetr":
        return UNETR(
            in_channels=in_channels,
            out_channels=out_channels,
            img_size=tuple(cfg.get("model", {}).get("img_size", [128, 128, 128])),
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


def _infer_in_channels_from_case(sample: Dict) -> int:
    """
    Estimate input channels based on 'image' field:
      - list of modality paths -> channels=len(list)
      - single path -> channels=1
      - tensor -> use shape[0] after EnsureChannelFirstd
    """
    img = sample.get("image")
    if isinstance(img, (list, tuple)):
        return len(img)
    if isinstance(img, str):
        return 1
    # tensor path (already loaded)
    if torch.is_tensor(img):
        return int(img.shape[0]) if img.ndim >= 4 else 1
    return 4


def _simple_tta_logits(model, images: torch.Tensor) -> torch.Tensor:
    """
    Symmetric flip TTA over W and H axes. Average logits.
    images: (N,C,H,W,D)
    """
    preds = []
    logits = model(images)
    preds.append(logits)
    # flip W
    preds.append(model(torch.flip(images, dims=[3])).flip(dims=[3]))
    # flip H
    preds.append(model(torch.flip(images, dims=[2])).flip(dims=[2]))
    # flip H and W
    preds.append(model(torch.flip(images, dims=[2, 3])).flip(dims=[2, 3]))
    return torch.stack(preds, dim=0).mean(dim=0)


def _save_nifti(arr: np.ndarray, affine: np.ndarray, path: Path) -> None:
    nib.Nifti1Image(arr, affine).to_filename(str(path))


def run_with_decathlon_loader(
    args: argparse.Namespace, cfg: Dict, device: torch.device, out_dir: Path
) -> None:
    # Load dataset config and transforms, build val loader via our decathlon loader
    with open(args.dataset_config, "r") as f:
        ds_cfg = json.load(f)

    # Use the dataset's transforms for consistency
    spacing = tuple(ds_cfg.get("spacing", (1.0, 1.0, 1.0)))
    tf_name = ds_cfg.get("transforms", "brats_like")
    if tf_name == "ct_liver":
        t_train, t_val = get_transforms_ct_liver(spacing=spacing)
    else:
        t_train, t_val = get_transforms_brats_like(spacing=spacing)

    # Build decathlon loaders (train unused here)
    _, val_loader, meta = load_monai_decathlon(
        cfg=ds_cfg,
        transforms_train=t_train,
        transforms_val=t_val,
        download=False,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=False,
    )

    # Infer channels from first batch
    first = next(iter(val_loader))
    in_channels = int(first["image"].shape[1])
    out_channels = cfg.get("model", {}).get("out_channels", 2)
    model = build_model(cfg, in_channels=in_channels, out_channels=out_channels).to(device)

    # Load checkpoint
    state = torch.load(args.model, map_location="cpu")
    model.load_state_dict(state.get("model", state))
    model.eval()

    # Sliding-window config
    roi_size = tuple(cfg.get("model", {}).get("img_size", [128, 128, 128]))
    inferer = SlidingWindowInferer(roi_size=roi_size, sw_batch_size=1, overlap=args.sw_overlap)

    post_pred = AsDiscrete(argmax=True, to_onehot=out_channels)
    post_label = AsDiscrete(to_onehot=out_channels)

    # Dice if labels exist
    try:
        from monai.metrics import DiceMetric
        dice_metric = DiceMetric(include_background=False, reduction="mean")
        compute_dice = True
    except Exception:
        compute_dice = False

    overlays_dir = out_dir / "overlays"
    prob_dir = out_dir / "prob_maps"

    with torch.no_grad():
        for idx, batch in enumerate(val_loader):
            images = batch["image"].to(device)
            labels = batch.get("label")
            if labels is not None:
                labels = labels.to(device)

            if args.amp and device.type == "cuda":
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    logits = _simple_tta_logits(model, images) if args.tta else inferer(images, model)
            else:
                logits = _simple_tta_logits(model, images) if args.tta else inferer(images, model)

            # Save mask NIfTI (argmax)
            probs = torch.softmax(logits, dim=1)
            mask = torch.argmax(probs, dim=1).detach().cpu().numpy().astype(np.uint8)  # (N,H,W,D)
            # Attempt to carry affine from meta if provided by loader
            affine = np.eye(4, dtype=np.float32)
            for n in range(mask.shape[0]):
                case_id = f"case_{idx:04d}_{n}"
                _save_nifti(mask[n], affine, out_dir / f"{case_id}_mask.nii.gz")

            # Visual overlays
            if args.save_overlays or args.save_prob_maps or compute_dice:
                preds_list = [post_pred(i) for i in torch.unbind(logits, dim=0)]
                labels_list = [post_label(i) for i in torch.unbind(labels, dim=0)] if labels is not None else [None] * len(preds_list)

                for n, (pred_oh, gt_oh) in enumerate(zip(preds_list, labels_list)):
                    case_id = f"case_{idx:04d}_{n}"
                    img_cf = images[n].detach().cpu()  # (C,H,W,D)

                    if args.save_overlays:
                        save_overlay_panel(
                            image_ch_first=img_cf,
                            label_onehot=gt_oh,
                            pred_onehot=pred_oh,
                            out_path=overlays_dir / f"{case_id}_overlay.png",
                            slices=args.slices,
                            class_index=args.class_index,
                        )

                    if args.save_prob_maps:
                        # probs[n]: (C_out,H,W,D)
                        save_prob_panel(
                            image_ch_first=img_cf,
                            prob_logits_or_probs=probs[n].detach().cpu(),
                            out_path=prob_dir / f"{case_id}_prob.png",
                            slices=args.slices,
                            class_index=args.class_index,
                            apply_softmax=False,  # already softmaxed
                        )

                if compute_dice and labels is not None:
                    # accumulate and print per-batch dice
                    preds_for_dice = [post_pred(i) for i in torch.unbind(logits, dim=0)]
                    gts_for_dice = [post_label(i) for i in torch.unbind(labels, dim=0)]
                    dice_metric(y_pred=preds_for_dice, y=gts_for_dice)

    if 'dice_metric' in locals():
        mean_dice = float(dice_metric.aggregate().item())
        dice_metric.reset()
        print(f"[SUMMARY] Mean Dice over validation set: {mean_dice:.4f}")


def run_with_simple_input(
    args: argparse.Namespace, cfg: Dict, device: torch.device, out_dir: Path
) -> None:
    """
    Basic path-only inference: expects a single 3D volume (NIfTI) or a directory of volumes.
    This path is less feature-complete than the Decathlon route but works for quick demos.
    """
    # Build a simple transform: load, ensure channel first, optional spacing, scale intensity
    tf = Compose(
        [
            LoadImaged(keys=["image"]),
            EnsureChannelFirstd(keys=["image"]),
            EnsureTyped(keys=["image"], device=device, track_meta=False),
            # If CT-like values, you could add ScaleIntensityRanged here
        ]
    )

    # Gather files
    in_path = Path(args.input)
    files = []
    if in_path.is_dir():
        for p in sorted(in_path.glob("*.nii*")):
            files.append({"image": str(p)})
    else:
        files.append({"image": str(in_path)})

    ds = Dataset(data=files, transform=tf)
    loader = DataLoader(ds, batch_size=1, shuffle=False, num_workers=0)

    # Infer channels from first case (post EnsureChannelFirst)
    first = next(iter(loader))
    in_channels = int(first["image"].shape[1])
    out_channels = cfg.get("model", {}).get("out_channels", 2)
    model = build_model(cfg, in_channels=in_channels, out_channels=out_channels).to(device)

    state = torch.load(args.model, map_location="cpu")
    model.load_state_dict(state.get("model", state))
    model.eval()

    roi_size = tuple(cfg.get("model", {}).get("img_size", [128, 128, 128]))
    inferer = SlidingWindowInferer(roi_size=roi_size, sw_batch_size=1, overlap=args.sw_overlap)

    overlays_dir = out_dir / "overlays"
    prob_dir = out_dir / "prob_maps"

    with torch.no_grad():
        for idx, batch in enumerate(loader):
            images = batch["image"].to(device)
            logits = inferer(images, model)
            probs = torch.softmax(logits, dim=1)
            mask = torch.argmax(probs, dim=1).detach().cpu().numpy().astype(np.uint8)  # (N,H,W,D)

            affine = np.eye(4, dtype=np.float32)
            for n in range(mask.shape[0]):
                case_id = f"case_{idx:04d}_{n}"
                _save_nifti(mask[n], affine, out_dir / f"{case_id}_mask.nii.gz")

                if args.save_overlays:
                    pred_oh = AsDiscrete(argmax=True, to_onehot=out_channels)(logits[n].detach().cpu())
                    save_overlay_panel(
                        image_ch_first=images[n].detach().cpu(),
                        label_onehot=None,
                        pred_onehot=pred_oh,
                        out_path=overlays_dir / f"{case_id}_overlay.png",
                        slices=args.slices,
                        class_index=args.class_index,
                    )

                if args.save_prob_maps:
                    save_prob_panel(
                        image_ch_first=images[n].detach().cpu(),
                        prob_logits_or_probs=probs[n].detach().cpu(),
                        out_path=prob_dir / f"{case_id}_prob.png",
                        slices=args.slices,
                        class_index=args.class_index,
                        apply_softmax=False,
                    )


def main() -> int:
    args = parse_args()
    set_determinism(args.seed)
    device = get_device(args.device)
    # Fix the attribute name parsing
    output_dir = getattr(args, 'output_dir', args.__dict__.get('output-dir', 'reports/inference_exports'))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load training config
    with open(args.config, "r") as f:
        cfg = json.load(f)

    if args.dataset_config:
        run_with_decathlon_loader(args, cfg, device, out_dir)
    elif args.input:
        run_with_simple_input(args, cfg, device, out_dir)
    else:
        raise SystemExit("Provide either --dataset-config (Decathlon val) or --input (file/dir).")

    print(f"[DONE] Outputs written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
