#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Focal Loss Implementation for Medical Image Segmentation

Focal Loss addresses class imbalance by down-weighting easy examples and
focusing learning on hard examples. Particularly effective for medical
segmentation where background dominates.

References:
- Lin et al. "Focal Loss for Dense Object Detection" (2017)
- Adaptations for medical image segmentation
"""

from typing import List, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance in segmentation.

    Focal Loss = -alpha * (1 - p_t)^gamma * log(p_t)

    Where:
    - p_t is the model's estimated probability for each class
    - alpha controls the relative importance of rare classes
    - gamma controls how much to down-weight easy examples
    """

    def __init__(
        self,
        alpha: Union[float, List[float]] = 1.0,
        gamma: float = 2.0,
        reduction: str = "mean",
        ignore_index: int = -100,
        smooth: float = 1e-8
    ):
        """
        Initialize Focal Loss.

        Args:
            alpha: Weighting factor for rare class (default: 1.0)
                  Can be scalar or list of weights for each class
            gamma: Focusing parameter (default: 2.0)
                  Higher gamma = more focus on hard examples
            reduction: Specifies reduction to apply to output ('mean', 'sum', 'none')
            ignore_index: Index to ignore in loss computation
            smooth: Smoothing factor to avoid numerical instability
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        self.ignore_index = ignore_index
        self.smooth = smooth

        if isinstance(alpha, list):
            self.alpha = torch.tensor(alpha, dtype=torch.float32)

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Focal Loss.

        Args:
            input: Predictions (N, C, H, W, D) for 3D or (N, C, H, W) for 2D
            target: Ground truth labels (N, H, W, D) or (N, H, W)

        Returns:
            Focal loss value
        """
        # Apply softmax to get probabilities
        if input.dim() > target.dim():
            # Input has channel dimension, apply softmax
            p = F.softmax(input, dim=1)
        else:
            # Input is already probabilities
            p = input

        # Create one-hot encoding of target
        if target.dim() == p.dim() - 1:
            # Target needs one-hot encoding
            num_classes = p.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            # Move class dimension to second position
            target_one_hot = target_one_hot.permute(0, -1, *range(1, target.dim()))
        else:
            target_one_hot = target

        # Flatten for easier computation
        p_flat = p.view(p.size(0), p.size(1), -1)  # (N, C, H*W*D)
        target_flat = target_one_hot.view(target_one_hot.size(0), target_one_hot.size(1), -1)

        # Compute focal loss for each class
        focal_loss = 0.0

        for c in range(p.size(1)):
            # Get probabilities and targets for this class
            p_c = p_flat[:, c, :]  # (N, H*W*D)
            t_c = target_flat[:, c, :]  # (N, H*W*D)

            # Skip if ignore_index
            if c == self.ignore_index:
                continue

            # Compute focal weight: (1 - p_t)^gamma
            p_t = torch.where(t_c == 1, p_c, 1 - p_c)
            focal_weight = (1 - p_t + self.smooth) ** self.gamma

            # Compute cross entropy: -log(p_t)
            ce_loss = -torch.log(p_t + self.smooth)

            # Apply alpha weighting
            if isinstance(self.alpha, torch.Tensor):
                alpha_weight = self.alpha[c]
            else:
                alpha_weight = self.alpha

            # Combine focal weight, alpha weight, and cross entropy
            focal_c = alpha_weight * focal_weight * ce_loss

            # Only consider positive examples for this class
            focal_c = focal_c * t_c

            focal_loss += focal_c.sum()

        # Apply reduction
        num_positives = target_one_hot.sum()
        if self.reduction == "mean":
            focal_loss = focal_loss / (num_positives + self.smooth)
        elif self.reduction == "sum":
            pass  # Keep as sum

        return focal_loss


class AdaptiveFocalLoss(nn.Module):
    """
    Adaptive Focal Loss that automatically adjusts alpha based on class frequencies.

    This version dynamically computes alpha weights based on the inverse
    frequency of classes in the current batch, making it more robust to
    varying class distributions.
    """

    def __init__(
        self,
        gamma: float = 2.0,
        reduction: str = "mean",
        ignore_index: int = -100,
        smooth: float = 1e-8,
        alpha_smooth: float = 0.1
    ):
        """
        Initialize Adaptive Focal Loss.

        Args:
            gamma: Focusing parameter
            reduction: Reduction method
            ignore_index: Index to ignore
            smooth: Smoothing factor
            alpha_smooth: Smoothing for alpha computation
        """
        super().__init__()
        self.gamma = gamma
        self.reduction = reduction
        self.ignore_index = ignore_index
        self.smooth = smooth
        self.alpha_smooth = alpha_smooth

    def compute_adaptive_alpha(self, target: torch.Tensor) -> torch.Tensor:
        """
        Compute adaptive alpha weights based on class frequencies.

        Args:
            target: Ground truth labels

        Returns:
            Alpha weights for each class
        """
        # Get unique classes and their counts
        unique_classes, counts = torch.unique(target, return_counts=True)

        # Compute frequencies
        total_pixels = target.numel()
        frequencies = counts.float() / total_pixels

        # Compute inverse frequency weights (with smoothing)
        alpha_weights = 1.0 / (frequencies + self.alpha_smooth)

        # Normalize weights
        alpha_weights = alpha_weights / alpha_weights.sum()

        # Create full alpha tensor
        num_classes = unique_classes.max().item() + 1
        alpha = torch.ones(num_classes, device=target.device)
        alpha[unique_classes] = alpha_weights

        return alpha

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Adaptive Focal Loss.

        Args:
            input: Predictions
            target: Ground truth labels

        Returns:
            Adaptive focal loss value
        """
        # Compute adaptive alpha
        alpha = self.compute_adaptive_alpha(target)

        # Create standard focal loss with computed alpha
        focal_loss = FocalLoss(
            alpha=alpha.tolist(),
            gamma=self.gamma,
            reduction=self.reduction,
            ignore_index=self.ignore_index,
            smooth=self.smooth
        )

        return focal_loss(input, target)


class BinaryFocalLoss(nn.Module):
    """
    Binary Focal Loss for binary segmentation tasks.

    Simplified version for binary classification with optimized computation.
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean",
        smooth: float = 1e-8
    ):
        """
        Initialize Binary Focal Loss.

        Args:
            alpha: Weight for positive class (0.25 works well for most cases)
            gamma: Focusing parameter
            reduction: Reduction method
            smooth: Smoothing factor
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        self.smooth = smooth

    def forward(
        self,
        input: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Binary Focal Loss.

        Args:
            input: Predictions (logits or probabilities)
            target: Binary ground truth (0 or 1)

        Returns:
            Binary focal loss value
        """
        # Apply sigmoid if input appears to be logits
        if input.min() < 0 or input.max() > 1:
            p = torch.sigmoid(input)
        else:
            p = input

        # Compute focal components
        p_t = torch.where(target == 1, p, 1 - p)
        alpha_t = torch.where(target == 1, self.alpha, 1 - self.alpha)

        # Focal weight
        focal_weight = (1 - p_t + self.smooth) ** self.gamma

        # Binary cross entropy
        bce_loss = -torch.log(p_t + self.smooth)

        # Combine components
        focal_loss = alpha_t * focal_weight * bce_loss

        # Apply reduction
        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        else:
            return focal_loss


def create_focal_loss(
    task_type: str = "multiclass",
    num_classes: int = 2,
    alpha: Union[float, List[float]] = None,
    gamma: float = 2.0,
    adaptive: bool = False,
    **kwargs
) -> nn.Module:
    """
    Factory function to create appropriate focal loss for the task.

    Args:
        task_type: Type of segmentation task ('binary' or 'multiclass')
        num_classes: Number of classes (ignored for binary)
        alpha: Alpha parameter (auto-computed for adaptive)
        gamma: Gamma parameter
        adaptive: Whether to use adaptive alpha
        **kwargs: Additional arguments

    Returns:
        Configured focal loss instance
    """
    if task_type == "binary":
        return BinaryFocalLoss(
            alpha=alpha if alpha is not None else 0.25,
            gamma=gamma,
            **kwargs
        )
    elif adaptive:
        return AdaptiveFocalLoss(
            gamma=gamma,
            **kwargs
        )
    else:
        # Default alpha for multiclass
        if alpha is None:
            alpha = 1.0

        return FocalLoss(
            alpha=alpha,
            gamma=gamma,
            **kwargs
        )


# Example usage and testing
if __name__ == "__main__":
    # Test focal loss implementations
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Binary segmentation example
    print("Testing Binary Focal Loss...")
    binary_loss = BinaryFocalLoss(alpha=0.25, gamma=2.0)

    # Create sample data
    batch_size, height, width = 2, 64, 64
    binary_pred = torch.randn(batch_size, height, width, device=device)
    binary_target = torch.randint(0, 2, (batch_size, height, width), device=device).float()

    loss_value = binary_loss(binary_pred, binary_target)
    print(f"Binary focal loss: {loss_value.item():.4f}")

    # Multiclass segmentation example
    print("\nTesting Multiclass Focal Loss...")
    num_classes = 4
    multiclass_loss = FocalLoss(alpha=1.0, gamma=2.0)

    multiclass_pred = torch.randn(batch_size, num_classes, height, width, device=device)
    multiclass_target = torch.randint(0, num_classes, (batch_size, height, width), device=device)

    loss_value = multiclass_loss(multiclass_pred, multiclass_target)
    print(f"Multiclass focal loss: {loss_value.item():.4f}")

    # Adaptive focal loss example
    print("\nTesting Adaptive Focal Loss...")
    adaptive_loss = AdaptiveFocalLoss(gamma=2.0)

    loss_value = adaptive_loss(multiclass_pred, multiclass_target)
    print(f"Adaptive focal loss: {loss_value.item():.4f}")

    print("\nAll focal loss tests completed successfully!")
    print("\nAll focal loss tests completed successfully!")
