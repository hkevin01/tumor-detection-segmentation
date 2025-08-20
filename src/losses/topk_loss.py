#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Top-K Loss and Hard Example Mining for Medical Image Segmentation

These loss functions focus training on the most difficult examples,
which is particularly useful for medical segmentation where challenging
cases at boundaries and rare structures need special attention.

References:
- Shrivastava et al. "Training Region-based Object Detectors with Online Hard Example Mining" (2016)
- Top-K loss for focusing on hardest examples
"""

from typing import Optional, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


class TopKLoss(nn.Module):
    """
    Top-K Loss that focuses on the K hardest examples.

    Instead of using all pixels/voxels, this loss only considers the K%
    hardest examples based on their loss values, forcing the model to
    focus on difficult regions.
    """

    def __init__(
        self,
        base_loss: nn.Module,
        k: Union[float, int] = 0.7,
        reduction: str = "mean",
        adaptive_k: bool = False,
        min_k: float = 0.1,
        max_k: float = 0.9
    ):
        """
        Initialize Top-K Loss.

        Args:
            base_loss: Base loss function to apply to top-k examples
            k: Fraction (0-1) or number of hardest examples to consider
            reduction: Reduction method for final loss
            adaptive_k: Whether to adaptively adjust k during training
            min_k: Minimum k value for adaptive adjustment
            max_k: Maximum k value for adaptive adjustment
        """
        super().__init__()
        self.base_loss = base_loss
        self.k = k
        self.reduction = reduction
        self.adaptive_k = adaptive_k
        self.min_k = min_k
        self.max_k = max_k

        # Track training progress for adaptive k
        self.iteration = 0
        self.loss_history = []

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Top-K Loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Top-K loss value
        """
        # Compute base loss with no reduction
        base_loss_func = nn.CrossEntropyLoss(reduction='none')
        if hasattr(self.base_loss, 'reduction'):
            original_reduction = self.base_loss.reduction
            self.base_loss.reduction = 'none'
            pixel_losses = self.base_loss(input_tensor, target)
            self.base_loss.reduction = original_reduction
        else:
            # Fallback to cross-entropy
            pixel_losses = base_loss_func(input_tensor, target)

        # Flatten pixel losses
        flat_losses = pixel_losses.view(-1)

        # Determine k value
        current_k = self._get_current_k()

        # Calculate number of top examples to keep
        if isinstance(current_k, float):
            num_topk = max(1, int(current_k * flat_losses.numel()))
        else:
            num_topk = min(current_k, flat_losses.numel())

        # Get top-k hardest examples
        topk_losses, _ = torch.topk(flat_losses, num_topk)

        # Apply reduction
        if self.reduction == "mean":
            final_loss = topk_losses.mean()
        elif self.reduction == "sum":
            final_loss = topk_losses.sum()
        else:
            final_loss = topk_losses

        # Update for adaptive k
        if self.adaptive_k:
            self.loss_history.append(final_loss.item())
            self._update_adaptive_k()

        self.iteration += 1
        return final_loss

    def _get_current_k(self) -> Union[float, int]:
        """Get current k value (adaptive or static)."""
        if self.adaptive_k:
            return self._compute_adaptive_k()
        else:
            return self.k

    def _compute_adaptive_k(self) -> float:
        """Compute adaptive k based on training progress."""
        if len(self.loss_history) < 10:
            return self.k

        # Start with high k (focus on more examples) and gradually reduce
        # to focus on harder examples as training progresses
        progress = min(1.0, self.iteration / 1000.0)  # Assume 1000 iterations for full adaptation

        # Exponential decay from max_k to min_k
        adaptive_k = self.max_k * (self.min_k / self.max_k) ** progress

        return max(self.min_k, min(self.max_k, adaptive_k))

    def _update_adaptive_k(self) -> None:
        """Update adaptive k based on loss trends."""
        if len(self.loss_history) >= 20:
            # Look at recent loss trend
            recent_losses = self.loss_history[-10:]
            older_losses = self.loss_history[-20:-10]

            recent_avg = sum(recent_losses) / len(recent_losses)
            older_avg = sum(older_losses) / len(older_losses)

            # If loss is not improving, focus on harder examples (reduce k)
            if recent_avg >= older_avg:
                self.k = max(self.min_k, self.k * 0.95)
            else:
                # If improving, can be slightly less aggressive
                self.k = min(self.max_k, self.k * 1.02)


class OnlineHardExampleMining(nn.Module):
    """
    Online Hard Example Mining (OHEM) for medical segmentation.

    Dynamically selects hard examples during training based on their
    loss values, adapting to the current model's performance.
    """

    def __init__(
        self,
        base_loss: nn.Module,
        keep_ratio: float = 0.7,
        min_kept: int = 100,
        ignore_thresh: float = 0.7,
        reduction: str = "mean"
    ):
        """
        Initialize OHEM.

        Args:
            base_loss: Base loss function
            keep_ratio: Ratio of examples to keep
            min_kept: Minimum number of examples to keep
            ignore_thresh: Ignore examples with confidence > thresh
            reduction: Reduction method
        """
        super().__init__()
        self.base_loss = base_loss
        self.keep_ratio = keep_ratio
        self.min_kept = min_kept
        self.ignore_thresh = ignore_thresh
        self.reduction = reduction

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute OHEM Loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            OHEM loss value
        """
        # Get probabilities
        if input_tensor.dim() > target.dim():
            probs = F.softmax(input_tensor, dim=1)
        else:
            probs = input_tensor

        # Compute per-pixel losses
        base_loss_func = nn.CrossEntropyLoss(reduction='none')
        if hasattr(self.base_loss, 'reduction'):
            original_reduction = self.base_loss.reduction
            self.base_loss.reduction = 'none'
            pixel_losses = self.base_loss(input_tensor, target)
            self.base_loss.reduction = original_reduction
        else:
            pixel_losses = base_loss_func(input_tensor, target)

        # Compute confidence (max probability)
        max_probs, _ = torch.max(probs, dim=1)

        # Create mask for valid examples (low confidence)
        valid_mask = max_probs < self.ignore_thresh

        # Apply valid mask to losses
        masked_losses = pixel_losses * valid_mask.float()

        # Flatten for selection
        flat_losses = masked_losses.view(-1)
        flat_valid = valid_mask.view(-1)

        # Get valid losses only
        valid_losses = flat_losses[flat_valid]

        if valid_losses.numel() == 0:
            # No valid examples, return small loss
            return torch.tensor(0.0, device=input_tensor.device, requires_grad=True)

        # Determine number of examples to keep
        num_keep = max(
            self.min_kept,
            int(self.keep_ratio * valid_losses.numel())
        )
        num_keep = min(num_keep, valid_losses.numel())

        # Select hardest examples
        if num_keep < valid_losses.numel():
            hard_losses, _ = torch.topk(valid_losses, num_keep)
        else:
            hard_losses = valid_losses

        # Apply reduction
        if self.reduction == "mean":
            return hard_losses.mean()
        elif self.reduction == "sum":
            return hard_losses.sum()
        else:
            return hard_losses


class FocalTopKLoss(nn.Module):
    """
    Combination of Focal Loss and Top-K selection.

    Applies focal loss mechanism to emphasize hard examples,
    then selects top-K hardest for final loss computation.
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        k: float = 0.5,
        reduction: str = "mean",
        smooth: float = 1e-8
    ):
        """
        Initialize Focal Top-K Loss.

        Args:
            alpha: Focal loss alpha parameter
            gamma: Focal loss gamma parameter
            k: Top-k ratio
            reduction: Reduction method
            smooth: Smoothing factor
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.k = k
        self.reduction = reduction
        self.smooth = smooth

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Focal Top-K Loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Focal Top-K loss value
        """
        # Apply softmax to get probabilities
        if input_tensor.dim() > target.dim():
            probs = F.softmax(input_tensor, dim=1)
        else:
            probs = input_tensor

        # Get target probabilities
        if target.dim() == probs.dim() - 1:
            # Convert to one-hot
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            if target.dim() == 2:  # 2D case
                target_one_hot = target_one_hot.permute(0, 3, 1, 2)
            else:  # 3D case
                target_one_hot = target_one_hot.permute(0, 4, 1, 2, 3)
        else:
            target_one_hot = target

        # Compute focal weights
        p_t = (probs * target_one_hot).sum(dim=1)  # Probability of true class
        focal_weight = (1 - p_t + self.smooth) ** self.gamma

        # Compute cross-entropy loss
        ce_loss = -torch.log(p_t + self.smooth)

        # Apply alpha weighting
        alpha_t = self.alpha * target_one_hot + (1 - self.alpha) * (1 - target_one_hot)
        alpha_weight = (alpha_t).sum(dim=1)

        # Combine focal components
        focal_loss = alpha_weight * focal_weight * ce_loss

        # Flatten and select top-k
        flat_losses = focal_loss.view(-1)
        num_topk = max(1, int(self.k * flat_losses.numel()))

        topk_losses, _ = torch.topk(flat_losses, num_topk)

        # Apply reduction
        if self.reduction == "mean":
            return topk_losses.mean()
        elif self.reduction == "sum":
            return topk_losses.sum()
        else:
            return topk_losses


def create_topk_loss(
    loss_type: str = "topk",
    base_loss: Optional[nn.Module] = None,
    **kwargs
) -> nn.Module:
    """
    Factory function to create top-k loss variant.

    Args:
        loss_type: Type of top-k loss ('topk', 'ohem', 'focal_topk')
        base_loss: Base loss function (for topk and ohem)
        **kwargs: Additional arguments

    Returns:
        Configured top-k loss instance
    """
    if loss_type == "ohem":
        if base_loss is None:
            base_loss = nn.CrossEntropyLoss()
        return OnlineHardExampleMining(base_loss, **kwargs)
    elif loss_type == "focal_topk":
        return FocalTopKLoss(**kwargs)
    else:  # topk
        if base_loss is None:
            base_loss = nn.CrossEntropyLoss()
        return TopKLoss(base_loss, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("Testing Top-K Loss Functions...")

    # Create sample data
    batch_size, num_classes, height, width = 2, 3, 64, 64
    predictions = torch.randn(batch_size, num_classes, height, width, device=device)
    targets = torch.randint(0, num_classes, (batch_size, height, width), device=device)

    # Test standard Top-K loss
    print("\nTesting Top-K Loss...")
    base_loss = nn.CrossEntropyLoss()
    topk_loss = TopKLoss(base_loss, k=0.7)
    loss_value = topk_loss(predictions, targets)
    print(f"Top-K loss: {loss_value.item():.4f}")

    # Test OHEM
    print("\nTesting Online Hard Example Mining...")
    ohem_loss = OnlineHardExampleMining(base_loss, keep_ratio=0.6)
    loss_value = ohem_loss(predictions, targets)
    print(f"OHEM loss: {loss_value.item():.4f}")

    # Test Focal Top-K
    print("\nTesting Focal Top-K Loss...")
    focal_topk = FocalTopKLoss(alpha=0.25, gamma=2.0, k=0.5)
    loss_value = focal_topk(predictions, targets)
    print(f"Focal Top-K loss: {loss_value.item():.4f}")

    # Test adaptive Top-K
    print("\nTesting Adaptive Top-K Loss...")
    adaptive_topk = TopKLoss(base_loss, k=0.8, adaptive_k=True)
    for i in range(5):
        loss_value = adaptive_topk(predictions, targets)
        current_k = adaptive_topk._get_current_k()
        print(f"Iteration {i+1}: loss={loss_value.item():.4f}, k={current_k:.3f}")

    print("\nAll Top-K loss tests completed successfully!")
    print("\nAll Top-K loss tests completed successfully!")
