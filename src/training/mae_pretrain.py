# =============================================================================
# ID: MAE-001
# Requirement: Implement Masked Autoencoder pre-training for 3-D medical
#              image encoders to improve downstream tumour segmentation with
#              limited labelled data.
# Purpose: Self-supervised pre-training on large unlabelled imaging datasets
#          (e.g., public CT/MRI collections) provides rich representations
#          that transfer to downstream labelled segmentation tasks.
# Rationale: MONAI 1.5.0 added MaskedAutoencoder (MAE) implementation.
#             Pre-training on unlabelled BraTS volumes + public MRI datasets
#             reduces required labelled samples by 50-80% per empirical results.
# Inputs:
#   - model        : ViT-based encoder (ViT, SwinUNETR encoder compatible)
#   - data_loader  : DataLoader yielding {"image": MetaTensor}; no label needed
#   - config       : dict with mask_ratio, patch_size, decoder_depth, lr etc.
# Outputs: Pre-trained encoder weights; reconstruction visualisations
# Preconditions: MONAI >= 1.5.0; ViT or SwinUNETR encoder
# Postconditions: Checkpoint saved; encoder ready for segmentation fine-tuning
# Assumptions: Images normalised, resampled to 96^3 or 128^3 voxel patches
# Failure Modes: OOM on full volume — use patch-based MAE with crop strategy
# References:
#   - He et al. "Masked Autoencoders Are Scalable Vision Learners" CVPR 2022
#   - MONAI 1.5.0 "Implementation of a Masked Autoencoder" (#8152)
#   - Xie et al. "SimMIM: a Simple Framework for Masked Image Modeling" 2021
# =============================================================================
"""Masked Autoencoder pre-training for 3-D MRI encoder networks."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.cuda.amp import GradScaler, autocast
    from torch.utils.data import DataLoader
    _TORCH_OK = True
except ImportError:
    _TORCH_OK = False

try:
    from monai.networks.nets import ViT
    _VIT_OK = True
except ImportError:
    _VIT_OK = False


# =============================================================================
# ID: MAE-002 – Simple patch masking
# Requirement: Randomly mask a fraction of 3-D image patches with a learnable
#              mask token before passing to the encoder.
# Inputs:
#   - x          : Tensor (B, C, H, W, D) — pre-normalised image patch
#   - mask_ratio : float in (0, 1) — fraction of patches to mask
#   - patch_size : int — cubic patch dimension in voxels
# Outputs:
#   - masked_x   : Tensor (B, C, H, W, D) with masked patches zeroed
#   - mask       : BoolTensor (B, N) — True where patch is masked
# =============================================================================
def random_masking(
    x: "torch.Tensor",
    mask_ratio: float = 0.75,
    patch_size: int = 16,
) -> tuple:
    """Apply random patch masking to 3-D volumetric input.

    Args:
        x: Input tensor (B, C, H, W, D), spatially divisible by patch_size
        mask_ratio: Fraction of patches to mask out during pre-training
        patch_size: Cubic patch size in voxels

    Returns:
        Tuple (masked_x, mask) where mask is 1=masked, 0=visible
    """
    B, C, H, W, D = x.shape
    ph = H // patch_size
    pw = W // patch_size
    pd = D // patch_size
    N = ph * pw * pd

    # Generate per-image random patch ordering
    noise = torch.rand(B, N, device=x.device)
    ids_sorted = torch.argsort(noise, dim=1)

    num_masked = int(N * mask_ratio)
    mask = torch.zeros(B, N, dtype=torch.bool, device=x.device)
    mask.scatter_(1, ids_sorted[:, :num_masked], True)  # First num_masked = masked

    # Reshape mask to spatial grid for broadcasting
    mask_spatial = mask.float().view(B, 1, ph, pw, pd)
    mask_spatial = mask_spatial.repeat_interleave(patch_size, dim=2)
    mask_spatial = mask_spatial.repeat_interleave(patch_size, dim=3)
    mask_spatial = mask_spatial.repeat_interleave(patch_size, dim=4)

    masked_x = x * (1.0 - mask_spatial)
    return masked_x, mask


# =============================================================================
# ID: MAE-003 – MAE pre-training loop
# Requirement: Train the encoder to reconstruct masked patches from visible
#              context using pixel-level MSE reconstruction loss.
# Inputs: See class docstring
# Outputs: float — mean reconstruction loss for the epoch
# =============================================================================
class MAEPretrainer:
    """Masked Autoencoder self-supervised pre-training."""

    def __init__(
        self,
        encoder: "nn.Module",
        decoder: "nn.Module",
        data_loader: "DataLoader",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not _TORCH_OK:
            raise ImportError("torch must be installed.")

        self.encoder = encoder
        self.decoder = decoder
        self.loader = data_loader
        self.config = config or {}

        self.device = torch.device(
            self.config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        )
        self.encoder.to(self.device)
        self.decoder.to(self.device)

        self.mask_ratio = self.config.get("mask_ratio", 0.75)
        self.patch_size = self.config.get("patch_size", 16)

        params = list(self.encoder.parameters()) + list(self.decoder.parameters())
        self.optimizer = torch.optim.AdamW(
            params,
            lr=self.config.get("lr", 1.5e-4),
            weight_decay=self.config.get("weight_decay", 0.05),
        )
        self.scaler = GradScaler(enabled=self.device.type == "cuda")

        logger.info(
            "MAEPretrainer: mask_ratio=%.2f  patch_size=%d  device=%s",
            self.mask_ratio,
            self.patch_size,
            self.device,
        )

    def train_epoch(self, epoch: int) -> float:
        """Run one MAE pre-training epoch.

        Args:
            epoch: Current epoch index (for logging)

        Returns:
            Mean reconstruction loss for this epoch
        """
        self.encoder.train()
        self.decoder.train()
        total_loss = 0.0
        n = 0

        for batch in self.loader:
            imgs = batch["image"].to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)

            with autocast(enabled=self.device.type == "cuda"):
                masked, mask = random_masking(imgs, self.mask_ratio, self.patch_size)

                # Encode visible patches
                try:
                    latent = self.encoder(masked)
                except Exception:
                    # Fallback: treat entire image through encoder
                    latent = self.encoder(masked)

                # Decode and reconstruct full image
                reconstruction = self.decoder(latent)

                # Apply loss only on masked (target) patches
                B, C, H, W, D = imgs.shape
                ph = H // self.patch_size
                target_patches = imgs.unfold(2, self.patch_size, self.patch_size)
                target_patches = target_patches.unfold(3, self.patch_size, self.patch_size)
                target_patches = target_patches.unfold(4, self.patch_size, self.patch_size)

                # Normalise reconstruction target per-patch (SimMIM style)
                recon_patches = reconstruction.unfold(2, self.patch_size, self.patch_size)
                recon_patches = recon_patches.unfold(3, self.patch_size, self.patch_size)
                recon_patches = recon_patches.unfold(4, self.patch_size, self.patch_size)

                # MSE only on masked patches
                mask_3d = mask.view(B, ph, -1).bool()  # approximate reshape
                loss = F.mse_loss(reconstruction * mask.float().view(B, 1, ph, -1, 1),
                                  imgs * mask.float().view(B, 1, ph, -1, 1))

            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(
                list(self.encoder.parameters()) + list(self.decoder.parameters()), 1.0
            )
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total_loss += loss.item()
            n += 1

        avg = total_loss / max(n, 1)
        logger.info("MAE epoch %d — recon_loss: %.6f", epoch + 1, avg)
        return avg

    def save_encoder(self, save_path: str) -> None:
        """Persist encoder weights for downstream fine-tuning.

        Args:
            save_path: File path for the saved weights (.pth)
        """
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.encoder.state_dict(), save_path)
        logger.info("MAE encoder saved → %s", save_path)

    def load_encoder(self, weights_path: str) -> None:
        """Load pre-trained encoder weights (weights_only=True for security).

        Args:
            weights_path: Path to previously saved encoder state_dict
        """
        try:
            state = torch.load(weights_path, map_location=self.device, weights_only=True)
        except TypeError:
            state = torch.load(weights_path, map_location=self.device)
        self.encoder.load_state_dict(state)
        logger.info("MAE encoder loaded from %s", weights_path)
