#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONAI Label Application for Brain Tumor Segmentation.

This module exposes the tumor segmentation model as a MONAI Label server app,
making it directly usable inside 3D Slicer, OHIF Viewer, and MITK.

Clinical workflow:
  1. Start the MONAI Label server:
       monailabel start_server --app src/clinical/ --studies /data/brats/

  2. Open 3D Slicer → Extensions → MONAILabel → connect to http://localhost:8000

  3. Load any NIfTI / DICOM study and click "Run All" or use interactive prompts.

MONAI Label handles:
  - REST API (replaces FastAPI)
  - Active learning loop (requests most informative unlabelled cases)
  - DICOM / DICOMweb connectivity
  - 3D Slicer plugin updates automatically

Reference: https://github.com/Project-MONAI/MONAILabel
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from monailabel.interfaces.app import MONAILabelApp
    from monailabel.interfaces.config import TaskConfig
    from monailabel.interfaces.datastore import Datastore
    from monailabel.interfaces.tasks.infer_v2 import InferTask, InferType
    from monailabel.interfaces.tasks.train import TrainTask
    _MONAILABEL_AVAILABLE = True
except ImportError:
    _MONAILABEL_AVAILABLE = False

try:
    import torch
    from monai.networks.nets import UNETR
    from monai.inferers import SlidingWindowInferer
    from monai.transforms import (
        Compose, LoadImaged, EnsureChannelFirstd, Spacingd,
        NormalizeIntensityd, EnsureTyped, AsDiscreted,
    )
    _MONAI_AVAILABLE = True
except ImportError:
    _MONAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLASSES = {0: "background", 1: "necrotic_core", 2: "enhancing_tumor", 3: "edema"}
DEFAULT_SPATIAL_SIZE = (128, 128, 128)


# ---------------------------------------------------------------------------
# Inference task (works standalone without MONAI Label)
# ---------------------------------------------------------------------------

class TumorSegmentationInfer:
    """
    Standalone inference wrapper compatible with MONAI Label InferTask API.

    Can be called directly from Python or via the MONAI Label REST endpoint.
    """

    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str = "cpu",
        num_classes: int = 4,
        in_channels: int = 4,
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.device = device
        self.num_classes = num_classes
        self.in_channels = in_channels
        self._model = None

    def _load_model(self):
        if not _MONAI_AVAILABLE:
            raise ImportError("torch and monai are required for inference.")
        if self._model is not None:
            return self._model
        model = UNETR(
            in_channels=self.in_channels,
            out_channels=self.num_classes,
            img_size=DEFAULT_SPATIAL_SIZE,
            feature_size=16,
            hidden_size=768,
            mlp_dim=3072,
            num_heads=12,
            norm_name="instance",
            res_block=True,
        )
        if self.checkpoint_path.exists():
            state = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=True,
            )
            model.load_state_dict(state.get("model", state))
        model.to(self.device)
        model.eval()
        self._model = model
        return model

    def pre_transforms(self) -> Compose:
        """Standard BraTS preprocessing pipeline."""
        return Compose([
            LoadImaged(keys=["image"], image_only=True),
            EnsureChannelFirstd(keys=["image"]),
            Spacingd(keys=["image"], pixdim=(1.0, 1.0, 1.0), mode="bilinear"),
            NormalizeIntensityd(keys=["image"], nonzero=True, channel_wise=True),
            EnsureTyped(keys=["image"]),
        ])

    def post_transforms(self) -> Compose:
        return Compose([
            EnsureTyped(keys=["pred"]),
            AsDiscreted(keys=["pred"], argmax=True),
        ])

    def inferer(self) -> "SlidingWindowInferer":
        if not _MONAI_AVAILABLE:
            raise ImportError("monai required for sliding window inference.")
        return SlidingWindowInferer(
            roi_size=DEFAULT_SPATIAL_SIZE,
            sw_batch_size=1,
            overlap=0.5,
        )

    def __call__(self, image_path: str | Path) -> dict[str, Any]:
        """Run full inference on a NIfTI file. Returns mask and timing."""
        import time
        t0 = time.perf_counter()

        model = self._load_model()
        transforms = self.pre_transforms()
        data = transforms({"image": str(image_path)})
        image_tensor = data["image"].unsqueeze(0).to(self.device)

        with torch.no_grad():
            raw = self.inferer()(image_tensor, model)

        post = self.post_transforms()
        result = post({"pred": raw[0]})
        elapsed = time.perf_counter() - t0

        pred_np = result["pred"].cpu().numpy()
        class_volumes = {
            CLASSES[c]: float((pred_np == c).sum()) * 1.0  # voxel count
            for c in range(self.num_classes)
        }

        return {
            "segmentation": pred_np,
            "class_volumes_voxels": class_volumes,
            "segmentation_time_seconds": round(elapsed, 2),
            "device": self.device,
            "model": "UNETR",
        }


# ---------------------------------------------------------------------------
# MONAI Label App (only when monailabel is installed)
# ---------------------------------------------------------------------------

if _MONAILABEL_AVAILABLE and _MONAI_AVAILABLE:
    class TumorSegmentationApp(MONAILabelApp):
        """
        MONAI Label App for brain tumor segmentation with 3D Slicer / OHIF.

        Launch with:
            monailabel start_server --app src/clinical/ --studies /data/brats/
        """

        def init_infers(self) -> dict:
            return {
                "tumor_segmentation": TumorSegmentationInfer(
                    checkpoint_path="checkpoints/best_model.pth",
                ),
            }

        def init_trainers(self) -> dict:
            # Active learning trainer placeholder
            return {}
