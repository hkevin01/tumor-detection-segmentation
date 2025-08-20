"""
Advanced Loss Functions for Medical Image Segmentation

This module provides a comprehensive collection of loss functions specifically
designed for medical image segmentation tasks, addressing common challenges
like class imbalance, boundary sensitivity, and multi-class segmentation.

Components:
- FocalLoss: Address class imbalance
- TverskyLoss: Balance precision/recall
- CombinedLoss: Multi-loss strategies
- BoundaryLoss: Boundary-aware segmentation
- TopKLoss: Focus on hardest examples
- LossScheduler: Dynamic loss weighting
"""

__version__ = "1.0.0"
__author__ = "Medical AI Team"

from .boundary_loss import (BoundaryLoss, HausdorffLoss, SurfaceLoss,
                            create_boundary_loss)
from .combined_loss import (AdaptiveCombinedLoss, CombinedLoss, DiceFocalLoss,
                            TverskyFocalLoss, create_combined_loss)
from .focal_loss import (AdaptiveFocalLoss, BinaryFocalLoss, FocalLoss,
                         create_focal_loss)
from .loss_config import (LossConfig, create_loss_from_config,
                          get_recommended_config)
from .loss_scheduler import (AdaptiveLossWeighting, CurriculumLossScheduler,
                             LossScheduler, MultiTaskLossBalancer,
                             create_loss_scheduler)
from .topk_loss import (FocalTopKLoss, OnlineHardExampleMining, TopKLoss,
                        create_topk_loss)
from .tversky_loss import (FocalTverskyLoss, GeneralizedTverskyLoss,
                           TverskyLoss, create_tversky_loss)

__all__ = [
    # Focal Loss variants
    "FocalLoss",
    "AdaptiveFocalLoss",
    "BinaryFocalLoss",
    "create_focal_loss",

    # Tversky Loss variants
    "TverskyLoss",
    "GeneralizedTverskyLoss",
    "FocalTverskyLoss",
    "create_tversky_loss",

    # Combined Loss variants
    "CombinedLoss",
    "AdaptiveCombinedLoss",
    "DiceFocalLoss",
    "TverskyFocalLoss",
    "create_combined_loss",

    # Boundary Loss variants
    "BoundaryLoss",
    "SurfaceLoss",
    "HausdorffLoss",
    "create_boundary_loss",

    # Top-K Loss variants
    "TopKLoss",
    "OnlineHardExampleMining",
    "FocalTopKLoss",
    "create_topk_loss",

    # Loss Schedulers
    "LossScheduler",
    "AdaptiveLossWeighting",
    "CurriculumLossScheduler",
    "MultiTaskLossBalancer",
    "create_loss_scheduler",

    # Configuration
    "LossConfig",
    "create_loss_from_config",
    "get_recommended_config",
]
