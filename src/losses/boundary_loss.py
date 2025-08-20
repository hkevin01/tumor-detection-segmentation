#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Boundary Loss Implementation for Medical Image Segmentation

Boundary losses focus on improving segmentation accuracy at object boundaries,
which is particularly important for medical imaging where precise delineation
of anatomical structures is critical.

References:
- Kervadec et al. "Boundary loss for highly unbalanced segmentation" (2019)
- Distance transform-based boundary penalties
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.ndimage import distance_transform_edt


class BoundaryLoss(nn.Module):
    """
    Boundary Loss for improving segmentation boundaries.

    Uses distance transforms to penalize predictions that are far from
    true boundaries, encouraging more precise boundary delineation.
    """

    def __init__(
        self,
        reduction: str = "mean",
        smooth: float = 1e-6,
        theta0: float = 3.0,
        theta: float = 5.0
    ):
        """
        Initialize Boundary Loss.

        Args:
            reduction: Reduction method ('mean', 'sum', 'none')
            smooth: Smoothing factor
            theta0: Initial boundary width parameter
            theta: Boundary width decay parameter
        """
        super().__init__()
        self.reduction = reduction
        self.smooth = smooth
        self.theta0 = theta0
        self.theta = theta

    def compute_distance_transform(self, mask: torch.Tensor) -> torch.Tensor:
        """
        Compute distance transform for boundary computation.

        Args:
            mask: Binary mask tensor (N, H, W) or (N, H, W, D)

        Returns:
            Distance transform tensor
        """
        batch_size = mask.shape[0]

        if mask.dim() == 3:  # 2D case
            height, width = mask.shape[1], mask.shape[2]
            dt_tensor = torch.zeros_like(mask, dtype=torch.float32)

            for b in range(batch_size):
                # Convert to numpy for scipy
                mask_np = mask[b].cpu().numpy().astype(np.uint8)

                # Compute distance transform
                dt_pos = distance_transform_edt(mask_np)
                dt_neg = distance_transform_edt(1 - mask_np)

                # Combine positive and negative distances
                dt = dt_pos - dt_neg
                dt_tensor[b] = torch.from_numpy(dt).to(mask.device)

        elif mask.dim() == 4:  # 3D case
            height, width, depth = mask.shape[1], mask.shape[2], mask.shape[3]
            dt_tensor = torch.zeros_like(mask, dtype=torch.float32)

            for b in range(batch_size):
                mask_np = mask[b].cpu().numpy().astype(np.uint8)

                dt_pos = distance_transform_edt(mask_np)
                dt_neg = distance_transform_edt(1 - mask_np)

                dt = dt_pos - dt_neg
                dt_tensor[b] = torch.from_numpy(dt).to(mask.device)
        else:
            raise ValueError(f"Unsupported mask dimension: {mask.dim()}")

        return dt_tensor

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Boundary Loss.

        Args:
            input_tensor: Predictions (N, C, H, W) or (N, C, H, W, D)
            target: Ground truth labels (N, H, W) or (N, H, W, D)

        Returns:
            Boundary loss value
        """
        # Apply softmax to get probabilities
        if input_tensor.dim() > target.dim():
            probs = F.softmax(input_tensor, dim=1)
        else:
            probs = input_tensor

        # Convert target to one-hot if needed
        if target.dim() == probs.dim() - 1:
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            if target.dim() == 2:  # 2D case
                target_one_hot = target_one_hot.permute(0, 3, 1, 2)
            else:  # 3D case
                target_one_hot = target_one_hot.permute(0, 4, 1, 2, 3)
        else:
            target_one_hot = target

        total_loss = 0.0
        num_classes = probs.size(1)

        for c in range(num_classes):
            # Get predictions and targets for this class
            pred_c = probs[:, c, ...]  # (N, H, W) or (N, H, W, D)
            target_c = target_one_hot[:, c, ...]  # (N, H, W) or (N, H, W, D)

            # Compute distance transform for ground truth
            dt_target = self.compute_distance_transform(target_c)

            # Compute boundary loss
            # Boundary loss = integral of prediction * distance_transform
            boundary_loss = (pred_c * dt_target).sum(dim=tuple(range(1, pred_c.dim())))

            # Normalize by image area/volume
            normalization = torch.prod(torch.tensor(pred_c.shape[1:])).float()
            boundary_loss = boundary_loss / (normalization + self.smooth)

            total_loss += boundary_loss.mean()

        # Average over classes
        total_loss = total_loss / num_classes

        return total_loss


class SurfaceLoss(nn.Module):
    """
    Surface Loss for boundary-aware segmentation.

    A more efficient implementation that approximates boundary loss
    using gradient-based surface computation.
    """

    def __init__(
        self,
        reduction: str = "mean",
        smooth: float = 1e-6,
        lambda_boundary: float = 1.0
    ):
        """
        Initialize Surface Loss.

        Args:
            reduction: Reduction method
            smooth: Smoothing factor
            lambda_boundary: Weight for boundary term
        """
        super().__init__()
        self.reduction = reduction
        self.smooth = smooth
        self.lambda_boundary = lambda_boundary

    def compute_surface_gradient(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Compute surface gradient using Sobel operator.

        Args:
            tensor: Input tensor (N, H, W) or (N, H, W, D)

        Returns:
            Surface gradient magnitude
        """
        if tensor.dim() == 3:  # 2D case
            # Sobel operators for 2D
            sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                                 dtype=tensor.dtype, device=tensor.device).view(1, 1, 3, 3)
            sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                                 dtype=tensor.dtype, device=tensor.device).view(1, 1, 3, 3)

            # Add channel dimension for conv2d
            tensor_expanded = tensor.unsqueeze(1)

            # Compute gradients
            grad_x = F.conv2d(tensor_expanded, sobel_x, padding=1)
            grad_y = F.conv2d(tensor_expanded, sobel_y, padding=1)

            # Gradient magnitude
            gradient_magnitude = torch.sqrt(grad_x**2 + grad_y**2 + self.smooth)

            return gradient_magnitude.squeeze(1)

        elif tensor.dim() == 4:  # 3D case
            # Simple 3D gradient approximation
            grad_x = torch.gradient(tensor, dim=1)[0]
            grad_y = torch.gradient(tensor, dim=2)[0]
            grad_z = torch.gradient(tensor, dim=3)[0]

            gradient_magnitude = torch.sqrt(grad_x**2 + grad_y**2 + grad_z**2 + self.smooth)

            return gradient_magnitude
        else:
            raise ValueError(f"Unsupported tensor dimension: {tensor.dim()}")

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Surface Loss.

        Args:
            input_tensor: Predictions
            target: Ground truth labels

        Returns:
            Surface loss value
        """
        # Apply softmax to get probabilities
        if input_tensor.dim() > target.dim():
            probs = F.softmax(input_tensor, dim=1)
        else:
            probs = input_tensor

        # Convert target to one-hot if needed
        if target.dim() == probs.dim() - 1:
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            if target.dim() == 2:  # 2D case
                target_one_hot = target_one_hot.permute(0, 3, 1, 2)
            else:  # 3D case
                target_one_hot = target_one_hot.permute(0, 4, 1, 2, 3)
        else:
            target_one_hot = target.float()

        total_loss = 0.0
        num_classes = probs.size(1)

        for c in range(num_classes):
            # Get predictions and targets for this class
            pred_c = probs[:, c, ...]
            target_c = target_one_hot[:, c, ...]

            # Compute surface gradients
            pred_surface = self.compute_surface_gradient(pred_c)
            target_surface = self.compute_surface_gradient(target_c)

            # Surface loss = L2 distance between surface gradients
            surface_diff = (pred_surface - target_surface) ** 2
            surface_loss = surface_diff.mean()

            total_loss += surface_loss

        # Average over classes
        total_loss = total_loss / num_classes

        return self.lambda_boundary * total_loss


class HausdorffLoss(nn.Module):
    """
    Hausdorff Distance-based Loss for boundary accuracy.

    Approximates Hausdorff distance using morphological operations
    for differentiable boundary optimization.
    """

    def __init__(
        self,
        reduction: str = "mean",
        alpha: float = 2.0,
        erosions: int = 10
    ):
        """
        Initialize Hausdorff Loss.

        Args:
            reduction: Reduction method
            alpha: Sharpness parameter for differentiable approximation
            erosions: Number of erosion operations for boundary computation
        """
        super().__init__()
        self.reduction = reduction
        self.alpha = alpha
        self.erosions = erosions

    def morphological_erosion(self, tensor: torch.Tensor, kernel_size: int = 3) -> torch.Tensor:
        """
        Perform morphological erosion using max pooling.

        Args:
            tensor: Input tensor
            kernel_size: Erosion kernel size

        Returns:
            Eroded tensor
        """
        if tensor.dim() == 3:  # 2D case
            # Add channel dimension
            tensor_expanded = tensor.unsqueeze(1)
            # Use negative max pooling for erosion
            eroded = -F.max_pool2d(-tensor_expanded, kernel_size, stride=1, padding=kernel_size//2)
            return eroded.squeeze(1)
        elif tensor.dim() == 4:  # 3D case
            tensor_expanded = tensor.unsqueeze(1)
            eroded = -F.max_pool3d(-tensor_expanded, kernel_size, stride=1, padding=kernel_size//2)
            return eroded.squeeze(1)
        else:
            raise ValueError(f"Unsupported tensor dimension: {tensor.dim()}")

    def compute_boundary(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Compute boundary using morphological operations.

        Args:
            tensor: Input binary tensor

        Returns:
            Boundary tensor
        """
        eroded = tensor
        for _ in range(self.erosions):
            eroded = self.morphological_erosion(eroded)

        boundary = tensor - eroded
        return boundary

    def forward(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Hausdorff Loss.

        Args:
            input_tensor: Predictions
            target: Ground truth labels

        Returns:
            Hausdorff loss value
        """
        # Apply softmax to get probabilities
        if input_tensor.dim() > target.dim():
            probs = F.softmax(input_tensor, dim=1)
        else:
            probs = input_tensor

        # Convert target to one-hot if needed
        if target.dim() == probs.dim() - 1:
            num_classes = probs.size(1)
            target_one_hot = F.one_hot(target, num_classes=num_classes)
            if target.dim() == 2:  # 2D case
                target_one_hot = target_one_hot.permute(0, 3, 1, 2)
            else:  # 3D case
                target_one_hot = target_one_hot.permute(0, 4, 1, 2, 3)
        else:
            target_one_hot = target.float()

        total_loss = 0.0
        num_classes = probs.size(1)

        for c in range(num_classes):
            # Get predictions and targets for this class
            pred_c = probs[:, c, ...]
            target_c = target_one_hot[:, c, ...]

            # Compute boundaries
            pred_boundary = self.compute_boundary(pred_c)
            target_boundary = self.compute_boundary(target_c)

            # Hausdorff distance approximation
            # Distance from pred boundary to target boundary
            pred_to_target = torch.min(
                torch.norm(pred_boundary.unsqueeze(-1) - target_boundary.unsqueeze(-2), dim=-1),
                dim=-1
            )[0]

            # Distance from target boundary to pred boundary
            target_to_pred = torch.min(
                torch.norm(target_boundary.unsqueeze(-1) - pred_boundary.unsqueeze(-2), dim=-1),
                dim=-1
            )[0]

            # Hausdorff distance = max of both directions
            hausdorff_dist = torch.max(
                torch.max(pred_to_target),
                torch.max(target_to_pred)
            )

            total_loss += hausdorff_dist

        # Average over classes
        total_loss = total_loss / num_classes

        return total_loss


def create_boundary_loss(
    loss_type: str = "boundary",
    **kwargs
) -> nn.Module:
    """
    Factory function to create boundary loss.

    Args:
        loss_type: Type of boundary loss ('boundary', 'surface', 'hausdorff')
        **kwargs: Additional arguments

    Returns:
        Configured boundary loss instance
    """
    if loss_type == "surface":
        return SurfaceLoss(**kwargs)
    elif loss_type == "hausdorff":
        return HausdorffLoss(**kwargs)
    else:
        return BoundaryLoss(**kwargs)


# Example usage and testing
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("Testing Boundary Loss Functions...")

    # Create sample data
    batch_size, num_classes, height, width = 2, 3, 64, 64
    predictions = torch.randn(batch_size, num_classes, height, width, device=device)
    targets = torch.randint(0, num_classes, (batch_size, height, width), device=device)

    # Test Surface Loss (more efficient)
    print("\nTesting Surface Loss...")
    surface_loss = SurfaceLoss(lambda_boundary=1.0)
    loss_value = surface_loss(predictions, targets)
    print(f"Surface loss: {loss_value.item():.4f}")

    # Test Hausdorff Loss
    print("\nTesting Hausdorff Loss...")
    hausdorff_loss = HausdorffLoss(alpha=2.0, erosions=5)
    loss_value = hausdorff_loss(predictions, targets)
    print(f"Hausdorff loss: {loss_value.item():.4f}")

    print("\nBoundary loss tests completed successfully!")
