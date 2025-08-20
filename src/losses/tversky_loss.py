#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tversky Loss Implementation for Medical Image Segmentation

Tversky Loss is a generalization of Dice Loss that allows for better control
over the balance between precision and recall. Particularly useful in medical
imaging where false positives and false negatives have different costs.

References:
- Tversky, A. "Features of Similarity" (1977)
- Salehi et al. "Tversky Loss Function for Image Segmentation" (2017)
"""

from typing import List, Optional, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


class TverskyLoss(nn.Module):
    """
    Tversky Loss for medical image segmentation.

    Tversky Index = TP / (TP + alpha*FN + beta*FP)
    Tversky Loss = 1 - Tversky Index

    Where:
    - alpha controls the penalty for false negatives
    - beta controls the penalty for false positives
    - alpha = beta = 0.5 gives Dice Loss
    - alpha > beta emphasizes recall (reduces false negatives)
    - alpha < beta emphasizes precision (reduces false positives)
    """

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        smooth: float = 1e-6,
        reduction: str = "mean",
        ignore_index: int = -100
    ):
        """
        Initialize Tversky Loss.

        Args:
            alpha: Weight for false negatives (default: 0.5)
                  Higher alpha = more penalty for missing positive regions
            beta: Weight for false positives (default: 0.5)
                 Higher beta = more penalty for false positive regions
            smooth: Smoothing factor to avoid division by zero
            reduction: Reduction method ('mean', 'sum', 'none')
            ignore_index: Index to ignore in loss computation
        """
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.smooth = smooth
        self.reduction = reduction
        self.ignore_index = ignore_index

        # Validate parameters
        if alpha < 0 or beta < 0:
            raise ValueError("Alpha and beta must be non-negative")
        if alpha + beta <= 0:
            raise ValueError("Sum of alpha and beta must be positive")

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Tversky Loss.

        Args:
            input: Predictions (N, C, H, W, D) for 3D or (N, C, H, W) for 2D
            target: Ground truth labels (N, H, W, D) or (N, H, W)

        Returns:
            Tversky loss value
        """
        # Apply softmax to get probabilities
        if input.dim() > target.dim():
            probs = F.softmax(input, dim=1)
        else:
            probs = input

        # Convert target to one-hot if needed
        if target.dim() == probs.dim() - 1:
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            # Move class dimension to second position
            target_one_hot = target_one_hot.permute(0, -1, *range(1, target.dim()))
        else:
            target_one_hot = target

        # Flatten tensors for easier computation
        probs_flat = probs.view(probs.size(0), probs.size(1), -1)
        target_flat = target_one_hot.view(
            target_one_hot.size(0), target_one_hot.size(1), -1
        )

        # Compute Tversky loss for each class
        tversky_losses = []

        for c in range(probs.size(1)):
            if c == self.ignore_index:
                continue

            # Get predictions and targets for this class
            p_c = probs_flat[:, c, :]  # (N, H*W*D)
            t_c = target_flat[:, c, :]  # (N, H*W*D)

            # Compute Tversky components
            tp = (p_c * t_c).sum(dim=1)  # True positives
            fn = (t_c * (1 - p_c)).sum(dim=1)  # False negatives
            fp = (p_c * (1 - t_c)).sum(dim=1)  # False positives

            # Compute Tversky index
            tversky_index = (tp + self.smooth) / (
                tp + self.alpha * fn + self.beta * fp + self.smooth
            )

            # Tversky loss
            tversky_loss = 1.0 - tversky_index
            tversky_losses.append(tversky_loss)

        # Stack losses for all classes
        if tversky_losses:
            total_loss = torch.stack(tversky_losses, dim=1)  # (N, C)
        else:
            total_loss = torch.zeros(probs.size(0), device=probs.device)
            return total_loss.mean() if self.reduction == "mean" else total_loss.sum()

        # Apply reduction
        if self.reduction == "mean":
            return total_loss.mean()
        elif self.reduction == "sum":
            return total_loss.sum()
        else:
            return total_loss


class GeneralizedTverskyLoss(nn.Module):
    """
    Generalized Tversky Loss with class-specific alpha and beta parameters.

    This allows different precision/recall trade-offs for different classes,
    which is useful when different anatomical structures have different
    clinical importance.
    """

    def __init__(
        self,
        alpha: Union[float, List[float]] = 0.5,
        beta: Union[float, List[float]] = 0.5,
        class_weights: Optional[List[float]] = None,
        smooth: float = 1e-6,
        reduction: str = "mean",
        ignore_index: int = -100
    ):
        """
        Initialize Generalized Tversky Loss.

        Args:
            alpha: Weight(s) for false negatives (per class or global)
            beta: Weight(s) for false positives (per class or global)
            class_weights: Relative importance of each class
            smooth: Smoothing factor
            reduction: Reduction method
            ignore_index: Index to ignore
        """
        super().__init__()
        self.alpha = alpha if isinstance(alpha, list) else [alpha]
        self.beta = beta if isinstance(beta, list) else [beta]
        self.class_weights = class_weights
        self.smooth = smooth
        self.reduction = reduction
        self.ignore_index = ignore_index

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Generalized Tversky Loss.

        Args:
            input: Predictions
            target: Ground truth labels

        Returns:
            Generalized Tversky loss value
        """
        # Apply softmax to get probabilities
        if input.dim() > target.dim():
            probs = F.softmax(input, dim=1)
        else:
            probs = input

        # Convert target to one-hot if needed
        if target.dim() == probs.dim() - 1:
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            target_one_hot = target_one_hot.permute(0, -1, *range(1, target.dim()))
        else:
            target_one_hot = target

        # Extend alpha and beta to match number of classes
        num_classes = probs.size(1)
        alpha_list = self.alpha * (num_classes // len(self.alpha) + 1)
        beta_list = self.beta * (num_classes // len(self.beta) + 1)
        alpha_list = alpha_list[:num_classes]
        beta_list = beta_list[:num_classes]

        # Default class weights
        if self.class_weights is None:
            class_weights = [1.0] * num_classes
        else:
            class_weights = self.class_weights

        # Flatten tensors
        probs_flat = probs.view(probs.size(0), probs.size(1), -1)
        target_flat = target_one_hot.view(
            target_one_hot.size(0), target_one_hot.size(1), -1
        )

        # Compute weighted Tversky loss for each class
        weighted_losses = []

        for c in range(num_classes):
            if c == self.ignore_index:
                continue

            # Get class-specific parameters
            alpha_c = alpha_list[c]
            beta_c = beta_list[c]
            weight_c = class_weights[c] if c < len(class_weights) else 1.0

            # Get predictions and targets for this class
            p_c = probs_flat[:, c, :]
            t_c = target_flat[:, c, :]

            # Compute Tversky components
            tp = (p_c * t_c).sum(dim=1)
            fn = (t_c * (1 - p_c)).sum(dim=1)
            fp = (p_c * (1 - t_c)).sum(dim=1)

            # Compute Tversky index
            tversky_index = (tp + self.smooth) / (
                tp + alpha_c * fn + beta_c * fp + self.smooth
            )

            # Weighted Tversky loss
            tversky_loss = weight_c * (1.0 - tversky_index)
            weighted_losses.append(tversky_loss)

        # Combine losses
        if weighted_losses:
            total_loss = torch.stack(weighted_losses, dim=1)
        else:
            total_loss = torch.zeros(probs.size(0), device=probs.device)
            return total_loss.mean() if self.reduction == "mean" else total_loss.sum()

        # Apply reduction
        if self.reduction == "mean":
            return total_loss.mean()
        elif self.reduction == "sum":
            return total_loss.sum()
        else:
            return total_loss


class FocalTverskyLoss(nn.Module):
    """
    Focal Tversky Loss combines Focal Loss and Tversky Loss.

    This addresses both class imbalance (via focal mechanism) and
    precision/recall trade-off (via Tversky mechanism).
    """

    def __init__(
        self,
        alpha: float = 0.7,
        beta: float = 0.3,
        gamma: float = 4.0/3.0,
        smooth: float = 1e-6,
        reduction: str = "mean",
        ignore_index: int = -100
    ):
        """
        Initialize Focal Tversky Loss.

        Args:
            alpha: Tversky alpha (false negative weight)
            beta: Tversky beta (false positive weight)
            gamma: Focal gamma (focusing parameter)
            smooth: Smoothing factor
            reduction: Reduction method
            ignore_index: Index to ignore
        """
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.smooth = smooth
        self.reduction = reduction
        self.ignore_index = ignore_index

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Focal Tversky Loss.

        Args:
            input: Predictions
            target: Ground truth labels

        Returns:
            Focal Tversky loss value
        """
        # First compute Tversky loss
        tversky_loss = TverskyLoss(
            alpha=self.alpha,
            beta=self.beta,
            smooth=self.smooth,
            reduction="none",
            ignore_index=self.ignore_index
        )

        tl = tversky_loss(input, target)

        # Apply focal mechanism
        focal_tversky = tl ** self.gamma

        # Apply reduction
        if self.reduction == "mean":
            return focal_tversky.mean()
        elif self.reduction == "sum":
            return focal_tversky.sum()
        else:
            return focal_tversky


def create_tversky_loss(
    loss_type: str = "standard",
    alpha: Union[float, List[float]] = 0.5,
    beta: Union[float, List[float]] = 0.5,
    **kwargs
) -> nn.Module:
    """
    Factory function to create appropriate Tversky loss variant.

    Args:
        loss_type: Type of Tversky loss ('standard', 'generalized', 'focal')
        alpha: Alpha parameter(s)
        beta: Beta parameter(s)
        **kwargs: Additional arguments

    Returns:
        Configured Tversky loss instance
    """
    if loss_type == "generalized":
        return GeneralizedTverskyLoss(alpha=alpha, beta=beta, **kwargs)
    elif loss_type == "focal":
        return FocalTverskyLoss(alpha=alpha, beta=beta, **kwargs)
    else:
        return TverskyLoss(alpha=alpha, beta=beta, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Test standard Tversky loss
    print("Testing Standard Tversky Loss...")

    # Create sample data
    batch_size, num_classes, height, width = 2, 3, 64, 64
    predictions = torch.randn(batch_size, num_classes, height, width, device=device)
    targets = torch.randint(0, num_classes, (batch_size, height, width), device=device)

    # Test different alpha/beta combinations
    configs = [
        (0.5, 0.5, "Balanced (Dice-like)"),
        (0.7, 0.3, "Recall-focused"),
        (0.3, 0.7, "Precision-focused"),
    ]

    for alpha, beta, description in configs:
        tversky_loss = TverskyLoss(alpha=alpha, beta=beta)
        loss_value = tversky_loss(predictions, targets)
        print(f"{description}: {loss_value.item():.4f}")

    # Test generalized Tversky loss
    print("\nTesting Generalized Tversky Loss...")
    gen_tversky = GeneralizedTverskyLoss(
        alpha=[0.7, 0.5, 0.3],  # Different alpha for each class
        beta=[0.3, 0.5, 0.7],   # Different beta for each class
        class_weights=[1.0, 2.0, 1.5]  # Different importance
    )

    loss_value = gen_tversky(predictions, targets)
    print(f"Generalized Tversky loss: {loss_value.item():.4f}")

    # Test focal Tversky loss
    print("\nTesting Focal Tversky Loss...")
    focal_tversky = FocalTverskyLoss(alpha=0.7, beta=0.3, gamma=4.0/3.0)

    loss_value = focal_tversky(predictions, targets)
    print(f"Focal Tversky loss: {loss_value.item():.4f}")

    print("\nAll Tversky loss tests completed successfully!")
    print("\nAll Tversky loss tests completed successfully!")
