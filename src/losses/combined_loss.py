#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Combined Loss Functions for Medical Image Segmentation

This module implements various strategies for combining multiple loss functions
to leverage the strengths of different loss types. Common combinations include
Dice + Cross-Entropy, Focal + Boundary, and custom weighted combinations.

References:
- Multi-loss strategies in medical image segmentation
- Adaptive weighting schemes for loss combination
"""

from typing import Dict, List, Optional

import torch
import torch.nn as nn
from monai.losses import DiceLoss

from .focal_loss import FocalLoss
from .tversky_loss import TverskyLoss


class CombinedLoss(nn.Module):
    """
    Combined Loss that combines multiple loss functions with configurable weights.

    Supports static and dynamic weighting strategies for optimal loss combination.
    """

    def __init__(
        self,
        losses: Dict[str, nn.Module],
        weights: Dict[str, float],
        reduction: str = "mean",
        adaptive_weighting: bool = False,
        adaptation_method: str = "uncertainty"
    ):
        """
        Initialize Combined Loss.

        Args:
            losses: Dictionary of loss functions {name: loss_function}
            weights: Dictionary of loss weights {name: weight}
            reduction: Reduction method for final loss
            adaptive_weighting: Enable adaptive weight adjustment
            adaptation_method: Method for adaptive weighting
                             ('uncertainty', 'gradnorm', 'performance')
        """
        super().__init__()
        self.losses = nn.ModuleDict(losses)
        self.static_weights = weights
        self.reduction = reduction
        self.adaptive_weighting = adaptive_weighting
        self.adaptation_method = adaptation_method

        # Initialize adaptive weights
        if adaptive_weighting:
            self.adaptive_weights = nn.ParameterDict({
                name: nn.Parameter(torch.tensor(weight, dtype=torch.float32))
                for name, weight in weights.items()
            })
        else:
            self.adaptive_weights = None

        # Track loss history for adaptation
        self.loss_history = {name: [] for name in losses.keys()}
        self.iteration = 0

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute combined loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Combined loss value
        """
        individual_losses = {}
        total_loss = 0.0

        # Compute each loss component
        for name, loss_fn in self.losses.items():
            try:
                loss_value = loss_fn(input_tensor, target)
                individual_losses[name] = loss_value

                # Get weight (adaptive or static)
                if self.adaptive_weighting and self.adaptive_weights is not None:
                    weight = torch.sigmoid(self.adaptive_weights[name])
                else:
                    weight = self.static_weights.get(name, 1.0)

                # Add weighted loss
                total_loss += weight * loss_value

                # Update loss history
                self.loss_history[name].append(loss_value.item())

            except Exception as e:
                print(f"Warning: Loss '{name}' failed with error: {e}")
                continue

        # Update adaptive weights if enabled
        if self.adaptive_weighting and self.iteration % 10 == 0:
            self._update_adaptive_weights(individual_losses)

        self.iteration += 1
        return total_loss

    def _update_adaptive_weights(self, individual_losses: Dict[str, torch.Tensor]) -> None:
        """Update adaptive weights based on loss performance."""
        if self.adaptation_method == "uncertainty":
            self._update_weights_uncertainty(individual_losses)
        elif self.adaptation_method == "gradnorm":
            self._update_weights_gradnorm(individual_losses)
        elif self.adaptation_method == "performance":
            self._update_weights_performance(individual_losses)

    def _update_weights_uncertainty(self, individual_losses: Dict[str, torch.Tensor]) -> None:
        """Update weights based on loss uncertainty (variance)."""
        for name in individual_losses.keys():
            if len(self.loss_history[name]) > 10:
                recent_losses = self.loss_history[name][-10:]
                variance = torch.var(torch.tensor(recent_losses))
                # Higher variance -> lower weight (more uncertain)
                uncertainty_factor = 1.0 / (1.0 + variance)
                self.adaptive_weights[name].data *= 0.9  # Decay
                self.adaptive_weights[name].data += 0.1 * uncertainty_factor  # Update

    def _update_weights_gradnorm(self, individual_losses: Dict[str, torch.Tensor]) -> None:
        """Update weights based on gradient norms (GradNorm algorithm)."""
        # Simplified GradNorm - compute relative gradient magnitudes
        grad_norms = {}

        for name, loss in individual_losses.items():
            if loss.requires_grad:
                # Compute gradient norm for this loss
                grads = torch.autograd.grad(
                    loss, self.parameters(), retain_graph=True, allow_unused=True
                )
                grad_norm = sum(g.norm() for g in grads if g is not None)
                grad_norms[name] = grad_norm

        # Normalize and update weights
        if grad_norms:
            total_grad_norm = sum(grad_norms.values())
            for name in grad_norms.keys():
                relative_grad = grad_norms[name] / (total_grad_norm + 1e-8)
                self.adaptive_weights[name].data *= (1.0 - 0.1 * relative_grad)

    def _update_weights_performance(self, individual_losses: Dict[str, torch.Tensor]) -> None:
        """Update weights based on relative loss performance."""
        if len(self.loss_history[list(self.losses.keys())[0]]) > 5:
            for name in self.losses.keys():
                recent_losses = self.loss_history[name][-5:]
                improvement = recent_losses[0] - recent_losses[-1]
                # Better improvement -> higher weight
                improvement_factor = torch.sigmoid(torch.tensor(improvement))
                self.adaptive_weights[name].data = (
                    0.9 * self.adaptive_weights[name].data +
                    0.1 * improvement_factor
                )

    def get_current_weights(self) -> Dict[str, float]:
        """Get current loss weights."""
        if self.adaptive_weighting and self.adaptive_weights is not None:
            return {
                name: torch.sigmoid(weight).item()
                for name, weight in self.adaptive_weights.items()
            }
        else:
            return self.static_weights.copy()

    def get_loss_history(self) -> Dict[str, List[float]]:
        """Get history of individual losses."""
        return {name: history.copy() for name, history in self.loss_history.items()}


class AdaptiveCombinedLoss(nn.Module):
    """
    Adaptive Combined Loss with automatic loss selection and weighting.

    Automatically adjusts the combination of losses based on training progress
    and loss performance.
    """

    def __init__(
        self,
        loss_candidates: Dict[str, nn.Module],
        initial_weights: Optional[Dict[str, float]] = None,
        adaptation_frequency: int = 100,
        min_weight: float = 0.01,
        max_weight: float = 2.0
    ):
        """
        Initialize Adaptive Combined Loss.

        Args:
            loss_candidates: Available loss functions
            initial_weights: Starting weights (uniform if None)
            adaptation_frequency: How often to adapt weights
            min_weight: Minimum allowed weight
            max_weight: Maximum allowed weight
        """
        super().__init__()
        self.losses = nn.ModuleDict(loss_candidates)
        self.adaptation_frequency = adaptation_frequency
        self.min_weight = min_weight
        self.max_weight = max_weight

        # Initialize weights
        num_losses = len(loss_candidates)
        if initial_weights is None:
            initial_weights = {name: 1.0/num_losses for name in loss_candidates.keys()}

        self.weights = nn.ParameterDict({
            name: nn.Parameter(torch.tensor(weight, dtype=torch.float32))
            for name, weight in initial_weights.items()
        })

        # Performance tracking
        self.performance_tracker = {name: [] for name in loss_candidates.keys()}
        self.iteration = 0

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute adaptive combined loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Adaptive combined loss value
        """
        individual_losses = {}
        total_loss = 0.0

        # Compute individual losses
        for name, loss_fn in self.losses.items():
            try:
                loss_value = loss_fn(input_tensor, target)
                individual_losses[name] = loss_value

                # Apply normalized weight
                weight = self._get_normalized_weight(name)
                total_loss += weight * loss_value

                # Track performance
                self.performance_tracker[name].append(loss_value.item())

            except Exception as e:
                print(f"Warning: Loss '{name}' failed: {e}")
                continue

        # Adapt weights periodically
        if self.iteration % self.adaptation_frequency == 0 and self.iteration > 0:
            self._adapt_weights()

        self.iteration += 1
        return total_loss

    def _get_normalized_weight(self, name: str) -> torch.Tensor:
        """Get normalized weight for a loss."""
        # Apply constraints
        weight = torch.clamp(
            torch.sigmoid(self.weights[name]),
            self.min_weight,
            self.max_weight
        )

        # Normalize across all weights
        all_weights = torch.stack([
            torch.clamp(torch.sigmoid(w), self.min_weight, self.max_weight)
            for w in self.weights.values()
        ])
        weight_sum = all_weights.sum()

        return weight / weight_sum

    def _adapt_weights(self) -> None:
        """Adapt weights based on performance history."""
        if len(self.performance_tracker[list(self.losses.keys())[0]]) < 10:
            return

        # Compute performance metrics for each loss
        performance_scores = {}

        for name in self.losses.keys():
            recent_values = self.performance_tracker[name][-10:]

            # Compute improvement rate
            if len(recent_values) >= 2:
                improvement = (recent_values[0] - recent_values[-1]) / recent_values[0]
                stability = 1.0 / (1.0 + torch.var(torch.tensor(recent_values)))

                # Combined performance score
                performance_scores[name] = improvement + 0.1 * stability
            else:
                performance_scores[name] = 0.0

        # Update weights based on performance
        for name, score in performance_scores.items():
            # Encourage good performers, discourage poor performers
            adaptation_rate = 0.1
            self.weights[name].data += adaptation_rate * score


class DiceFocalLoss(nn.Module):
    """
    Combination of Dice Loss and Focal Loss.

    Popular combination for medical segmentation that addresses both
    overlap accuracy (Dice) and class imbalance (Focal).
    """

    def __init__(
        self,
        dice_weight: float = 0.5,
        focal_weight: float = 0.5,
        dice_smooth: float = 1e-6,
        focal_alpha: float = 0.25,
        focal_gamma: float = 2.0,
        reduction: str = "mean"
    ):
        """
        Initialize Dice-Focal Loss.

        Args:
            dice_weight: Weight for Dice loss component
            focal_weight: Weight for Focal loss component
            dice_smooth: Smoothing for Dice loss
            focal_alpha: Alpha parameter for Focal loss
            focal_gamma: Gamma parameter for Focal loss
            reduction: Reduction method
        """
        super().__init__()
        self.dice_weight = dice_weight
        self.focal_weight = focal_weight

        self.dice_loss = DiceLoss(
            smooth_nr=dice_smooth,
            smooth_dr=dice_smooth,
            reduction=reduction
        )
        self.focal_loss = FocalLoss(
            alpha=focal_alpha,
            gamma=focal_gamma,
            reduction=reduction
        )

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Dice-Focal Loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Combined Dice-Focal loss
        """
        dice_val = self.dice_loss(input_tensor, target)
        focal_val = self.focal_loss(input_tensor, target)

        return self.dice_weight * dice_val + self.focal_weight * focal_val


class TverskyFocalLoss(nn.Module):
    """
    Combination of Tversky Loss and Focal Loss.

    Combines precision/recall control (Tversky) with class imbalance
    handling (Focal) for robust medical segmentation.
    """

    def __init__(
        self,
        tversky_weight: float = 0.6,
        focal_weight: float = 0.4,
        tversky_alpha: float = 0.7,
        tversky_beta: float = 0.3,
        focal_alpha: float = 0.25,
        focal_gamma: float = 2.0,
        reduction: str = "mean"
    ):
        """
        Initialize Tversky-Focal Loss.

        Args:
            tversky_weight: Weight for Tversky loss
            focal_weight: Weight for Focal loss
            tversky_alpha: Alpha for Tversky loss
            tversky_beta: Beta for Tversky loss
            focal_alpha: Alpha for Focal loss
            focal_gamma: Gamma for Focal loss
            reduction: Reduction method
        """
        super().__init__()
        self.tversky_weight = tversky_weight
        self.focal_weight = focal_weight

        self.tversky_loss = TverskyLoss(
            alpha=tversky_alpha,
            beta=tversky_beta,
            reduction=reduction
        )
        self.focal_loss = FocalLoss(
            alpha=focal_alpha,
            gamma=focal_gamma,
            reduction=reduction
        )

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Tversky-Focal Loss.

        Args:
            input_tensor: Model predictions
            target: Ground truth labels

        Returns:
            Combined Tversky-Focal loss
        """
        tversky_val = self.tversky_loss(input_tensor, target)
        focal_val = self.focal_loss(input_tensor, target)

        return self.tversky_weight * tversky_val + self.focal_weight * focal_val


def create_combined_loss(
    loss_config: Dict[str, Dict],
    adaptive: bool = False
) -> nn.Module:
    """
    Factory function to create combined loss from configuration.

    Args:
        loss_config: Configuration dictionary with loss specifications
        adaptive: Whether to use adaptive weighting

    Returns:
        Configured combined loss instance

    Example:
        loss_config = {
            "dice": {"type": "dice", "weight": 0.5, "smooth": 1e-6},
            "focal": {"type": "focal", "weight": 0.3, "gamma": 2.0},
            "tversky": {"type": "tversky", "weight": 0.2, "alpha": 0.7}
        }
    """
    losses = {}
    weights = {}

    for name, config in loss_config.items():
        loss_type = config["type"]
        weight = config.get("weight", 1.0)
        weights[name] = weight

        # Create loss function based on type
        if loss_type == "dice":
            losses[name] = DiceLoss(**{k: v for k, v in config.items() if k not in ["type", "weight"]})
        elif loss_type == "focal":
            losses[name] = FocalLoss(**{k: v for k, v in config.items() if k not in ["type", "weight"]})
        elif loss_type == "tversky":
            losses[name] = TverskyLoss(**{k: v for k, v in config.items() if k not in ["type", "weight"]})
        elif loss_type == "cross_entropy":
            losses[name] = nn.CrossEntropyLoss(**{k: v for k, v in config.items() if k not in ["type", "weight"]})
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

    if adaptive:
        return AdaptiveCombinedLoss(losses, weights)
    else:
        return CombinedLoss(losses, weights)


# Example usage and testing
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("Testing Combined Loss Functions...")

    # Create sample data
    batch_size, num_classes, height, width = 2, 3, 64, 64
    predictions = torch.randn(batch_size, num_classes, height, width, device=device)
    targets = torch.randint(0, num_classes, (batch_size, height, width), device=device)

    # Test Dice-Focal combination
    print("\nTesting Dice-Focal Loss...")
    dice_focal = DiceFocalLoss(dice_weight=0.6, focal_weight=0.4)
    loss_value = dice_focal(predictions, targets)
    print(f"Dice-Focal loss: {loss_value.item():.4f}")

    # Test Tversky-Focal combination
    print("\nTesting Tversky-Focal Loss...")
    tversky_focal = TverskyFocalLoss(tversky_weight=0.7, focal_weight=0.3)
    loss_value = tversky_focal(predictions, targets)
    print(f"Tversky-Focal loss: {loss_value.item():.4f}")

    # Test general combined loss
    print("\nTesting General Combined Loss...")
    loss_config = {
        "dice": {"type": "dice", "weight": 0.4, "smooth_nr": 1e-6},
        "focal": {"type": "focal", "weight": 0.4, "gamma": 2.0},
        "tversky": {"type": "tversky", "weight": 0.2, "alpha": 0.7}
    }

    combined_loss = create_combined_loss(loss_config, adaptive=False)
    loss_value = combined_loss(predictions, targets)
    print(f"General combined loss: {loss_value.item():.4f}")

    print("\nAll combined loss tests completed successfully!")
    print("\nAll combined loss tests completed successfully!")
