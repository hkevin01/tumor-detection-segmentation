# =============================================================================
# ID: SEMI-SUP-001
# Requirement: Implement pseudo-label semi-supervised training loop that
#              leverages a teacher model to generate labels for unlabelled data.
# Purpose: Maximise model generalisation when only a fraction of training
#          volumes carry expert annotations (typical in clinical settings).
# Rationale: Mean-teacher consistency training (Tarvainen & Valpola 2017)
#            provides stable pseudo-labels via exponential moving average of
#            student weights without requiring separate annotation cycles.
# Inputs:
#   - teacher_model : EMA of student; updated via update_ema_variables()
#   - student_model : Trained by supervised + consistency losses
#   - labelled_loader   : DataLoader with image+label pairs
#   - unlabelled_loader : DataLoader with image only (no label required)
#   - config : dict with ema_decay, consistency_weight, rampup_epochs
# Outputs: float — composite semi-supervised loss for one epoch
# Preconditions: MONAI 1.3+ installed; teacher initialised from student
# Postconditions: Student updated; teacher EMA updated post-batch
# Assumptions: Unlabelled data has same spatial resolution as labelled data
# Side Effects: Modifies teacher_model parameters in-place (no grad)
# Failure Modes: EMA divergence if ema_decay is too low (<0.99)
# Verification: tests/test_semi_supervised.py
# References:
#   - Tarvainen & Valpola "Mean teachers are better role models" (NeurIPS 2017)
#   - MONAI 1.5 PythonicWorkflow + IterableDataset support
#   - MICCAI 2025 "Semi-Supervised Multi-Modal Medical Image Segmentation"
# =============================================================================
"""
Semi-supervised training with Mean Teacher consistency regularisation.

Combines supervised DiceCELoss on labelled data with unsupervised
consistency loss between student and teacher predictions on unlabelled data.
Suitable for scenarios where fewer than 20 % of volumes have expert labels.
"""

import logging
from typing import Any, Dict, Iterator, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from torch.cuda.amp import GradScaler, autocast
    from torch.utils.data import DataLoader

    from monai.data import decollate_batch
    from monai.losses import DiceCELoss
    from monai.metrics import DiceMetric
    from monai.transforms import AsDiscrete, Compose, EnsureType

    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False


# =============================================================================
# ID: SEMI-SUP-002 – EMA weight update
# Requirement: Update teacher network as exponential moving average of student.
# Purpose: EMA smoothing provides a more stable pseudo-label generator than
#          the noisily-updated student, reducing confirmation bias.
# Inputs:
#   - student_model : current student nn.Module
#   - teacher_model : EMA teacher nn.Module (no_grad)
#   - ema_decay     : float in [0.99, 0.9999]; higher = slower teacher update
# Side Effects: Modifies teacher_model.parameters() in-place
# =============================================================================
def update_ema_variables(
    student_model: "nn.Module",
    teacher_model: "nn.Module",
    ema_decay: float,
) -> None:
    """Update teacher model weights as EMA of student model weights."""
    with torch.no_grad():
        for s_param, t_param in zip(
            student_model.parameters(), teacher_model.parameters()
        ):
            t_param.data.mul_(ema_decay).add_(s_param.data, alpha=1.0 - ema_decay)


# =============================================================================
# ID: SEMI-SUP-003 – Sigmoid ramp-up schedule
# Requirement: Ramp consistency weight from 0 to max over rampup_epochs to
#              prevent premature pseudo-label collapse in early training.
# References: Laine & Aila "Temporal Ensembling" (ICLR 2017)
# =============================================================================
def sigmoid_rampup(current_epoch: int, rampup_epochs: int) -> float:
    """Return sigmoid-shaped ramp weight in [0, 1]."""
    if rampup_epochs == 0:
        return 1.0
    import math
    t = max(0.0, min(1.0, current_epoch / rampup_epochs))
    return float(math.exp(-5.0 * (1.0 - t) ** 2))


class MeanTeacherTrainer:
    # =========================================================================
    # ID: SEMI-SUP-004
    # Requirement: Orchestrate one semi-supervised training epoch combining
    #              supervised and consistency objectives.
    # =========================================================================

    def __init__(
        self,
        student_model: "nn.Module",
        teacher_model: "nn.Module",
        labelled_loader: "DataLoader",
        unlabelled_loader: "DataLoader",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not _DEPS_OK:
            raise ImportError("torch and monai must be installed.")

        self.student = student_model
        self.teacher = teacher_model
        self.l_loader = labelled_loader
        self.u_loader = unlabelled_loader
        self.config = config or {}

        device_str = self.config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.device = torch.device(device_str)
        self.student.to(self.device)
        self.teacher.to(self.device)

        # Teacher weights are not updated by gradient
        for p in self.teacher.parameters():
            p.requires_grad_(False)

        n_classes = self.config.get("num_classes", 3)
        self.sup_loss = DiceCELoss(
            to_onehot_y=True,
            softmax=True,
            lambda_dice=self.config.get("dice_weight", 0.5),
            lambda_ce=self.config.get("ce_weight", 0.5),
            label_smoothing=self.config.get("label_smoothing", 0.05),
        )
        self.consistency_criterion = nn.MSELoss()

        self.optimizer = torch.optim.AdamW(
            self.student.parameters(),
            lr=self.config.get("lr", 1e-4),
            weight_decay=self.config.get("weight_decay", 1e-5),
        )
        self.scaler = GradScaler(enabled=self.device.type == "cuda")
        self.ema_decay = self.config.get("ema_decay", 0.999)
        self.max_consistency_weight = self.config.get("consistency_weight", 0.1)
        self.rampup_epochs = self.config.get("rampup_epochs", 40)

        self.dice_metric = DiceMetric(include_background=False, reduction="mean")
        self.post_pred = Compose([EnsureType(), AsDiscrete(argmax=True, to_onehot=n_classes)])
        self.post_label = Compose([EnsureType(), AsDiscrete(to_onehot=n_classes)])

        logger.info(
            "MeanTeacherTrainer: ema_decay=%.4f  max_consistency_weight=%.3f  "
            "rampup=%d epochs",
            self.ema_decay,
            self.max_consistency_weight,
            self.rampup_epochs,
        )

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Run one semi-supervised training epoch.

        Args:
            epoch: Current epoch index (0-based) used for ramp-up weighting

        Returns:
            dict with supervised_loss, consistency_loss, total_loss
        """
        self.student.train()
        self.teacher.eval()

        consistency_weight = self.max_consistency_weight * sigmoid_rampup(
            epoch, self.rampup_epochs
        )

        sup_loss_sum = 0.0
        cons_loss_sum = 0.0
        n_batches = 0

        # Infinite iterator over unlabelled loader — cycle if shorter
        u_iter: Iterator = iter(self.u_loader)

        for batch in self.l_loader:
            # --- Labelled supervised branch -----------------------------------
            imgs = batch["image"].to(self.device, non_blocking=True)
            lbls = batch["label"].to(self.device, non_blocking=True)

            # --- Unlabelled consistency branch --------------------------------
            try:
                u_batch = next(u_iter)
            except StopIteration:
                u_iter = iter(self.u_loader)
                u_batch = next(u_iter)
            u_imgs = u_batch["image"].to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)

            with autocast(enabled=self.device.type == "cuda"):
                # Student predictions on labelled data
                student_sup = self.student(imgs)
                s_loss = self.sup_loss(student_sup, lbls)

                # Consistency on unlabelled data
                student_u = self.student(u_imgs)
                with torch.no_grad():
                    teacher_u = self.teacher(u_imgs)

                # Soft-label MSE consistency in probability space
                student_prob = torch.softmax(student_u, dim=1)
                teacher_prob = torch.softmax(teacher_u, dim=1)
                c_loss = self.consistency_criterion(student_prob, teacher_prob.detach())

                total = s_loss + consistency_weight * c_loss

            self.scaler.scale(total).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(self.student.parameters(), 1.0)
            self.scaler.step(self.optimizer)
            self.scaler.update()

            update_ema_variables(self.student, self.teacher, self.ema_decay)

            sup_loss_sum += s_loss.item()
            cons_loss_sum += c_loss.item()
            n_batches += 1

        result = {
            "supervised_loss": sup_loss_sum / max(n_batches, 1),
            "consistency_loss": cons_loss_sum / max(n_batches, 1),
            "consistency_weight": consistency_weight,
            "total_loss": (sup_loss_sum + consistency_weight * cons_loss_sum) / max(n_batches, 1),
        }
        logger.info(
            "Epoch %d semi-sup — sup_loss: %.4f  cons_loss: %.4f  weight: %.4f",
            epoch + 1,
            result["supervised_loss"],
            result["consistency_loss"],
            consistency_weight,
        )
        return result
