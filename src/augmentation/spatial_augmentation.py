#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spatial Augmentation Transforms for Medical Images

This module provides spatial augmentation transforms for 3D medical images
including elastic deformations, affine transformations, and non-linear
deformations while preserving anatomical constraints.

Key Features:
- 3D elastic transformations
- Affine transformations (rotation, scaling, translation)
- Non-linear deformations with anatomical constraints
- Anisotropic scaling for different medical orientations
"""

import warnings
from typing import Dict, Tuple, Union

import numpy as np
import torch

try:
    from monai.transforms import Transform
    HAS_MONAI = True
except ImportError:
    HAS_MONAI = False
    warnings.warn("MONAI not available. Using base transform class.")


class ElasticTransform(Transform if HAS_MONAI else object):
    """
    3D Elastic transformation for medical images.

    Applies realistic elastic deformations that preserve anatomical
    structure while providing effective data augmentation.
    """

    def __init__(
        self,
        alpha_range: Tuple[float, float] = (0.0, 30.0),
        sigma_range: Tuple[float, float] = (5.0, 15.0),
        prob: float = 0.2,
        mode: str = "bilinear",
        padding_mode: str = "border",
        anatomical_preservation: float = 0.8
    ):
        """
        Initialize elastic transform.

        Args:
            alpha_range: Range for deformation strength
            sigma_range: Range for smoothing kernel sigma
            prob: Probability of applying transform
            mode: Interpolation mode
            padding_mode: Padding mode for out-of-bounds values
            anatomical_preservation: Factor to preserve anatomy (0=none, 1=strict)
        """
        self.alpha_range = alpha_range
        self.sigma_range = sigma_range
        self.prob = prob
        self.mode = mode
        self.padding_mode = padding_mode
        self.anatomical_preservation = anatomical_preservation

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply elastic transformation to input tensor.

        Args:
            data: Input tensor (C, H, W, D) or (H, W, D)

        Returns:
            Elastically transformed tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Get spatial dimensions
        if data.dim() == 4:  # (C, H, W, D)
            spatial_shape = data.shape[1:]
            has_channels = True
        else:  # (H, W, D)
            spatial_shape = data.shape
            has_channels = False

        # Generate displacement field
        displacement_field = self._generate_displacement_field(spatial_shape)

        # Apply anatomical preservation constraints
        if self.anatomical_preservation > 0:
            displacement_field = self._apply_anatomical_constraints(
                displacement_field, spatial_shape
            )

        # Convert to tensor
        displacement_field = torch.from_numpy(displacement_field).to(
            data.device, data.dtype
        )

        # Apply deformation
        if has_channels:
            transformed_data = torch.zeros_like(data)
            for c in range(data.shape[0]):
                transformed_data[c] = self._warp_tensor(
                    data[c], displacement_field
                )
        else:
            transformed_data = self._warp_tensor(data, displacement_field)

        return transformed_data

    def _generate_displacement_field(self, spatial_shape: Tuple[int, ...]) -> np.ndarray:
        """Generate smooth displacement field."""
        # Sample parameters
        alpha = self.rng.uniform(*self.alpha_range)
        sigma = self.rng.uniform(*self.sigma_range)

        # Generate random displacement for each dimension
        displacement_field = np.zeros((len(spatial_shape),) + spatial_shape)

        for dim in range(len(spatial_shape)):
            # Generate random field
            random_field = self.rng.normal(0, 1, spatial_shape)

            # Smooth with Gaussian kernel
            from scipy.ndimage import gaussian_filter
            smooth_field = gaussian_filter(random_field, sigma)

            # Scale by alpha
            displacement_field[dim] = smooth_field * alpha

        return displacement_field

    def _apply_anatomical_constraints(
        self,
        displacement_field: np.ndarray,
        spatial_shape: Tuple[int, ...]
    ) -> np.ndarray:
        """Apply constraints to preserve anatomical structure."""
        # Create boundary weight mask
        boundary_weights = np.ones(spatial_shape)

        # Reduce deformation near boundaries
        boundary_depth = max(1, min(spatial_shape) // 20)

        for dim in range(len(spatial_shape)):
            # Distance from each boundary
            coords = np.arange(spatial_shape[dim])
            dist_start = coords
            dist_end = spatial_shape[dim] - 1 - coords

            # Minimum distance to boundary
            dist_to_boundary = np.minimum(dist_start, dist_end)

            # Weight based on distance
            weights = np.minimum(dist_to_boundary, boundary_depth) / boundary_depth

            # Reshape for broadcasting
            shape = [1] * len(spatial_shape)
            shape[dim] = spatial_shape[dim]
            weights = weights.reshape(shape)

            # Apply to boundary weights
            boundary_weights *= weights

        # Apply anatomical preservation
        preservation_factor = (
            self.anatomical_preservation +
            (1 - self.anatomical_preservation) * boundary_weights
        )

        # Scale displacement field
        for dim in range(len(spatial_shape)):
            displacement_field[dim] *= preservation_factor

        return displacement_field

    def _warp_tensor(
        self,
        tensor: torch.Tensor,
        displacement_field: torch.Tensor
    ) -> torch.Tensor:
        """Warp tensor using displacement field."""
        spatial_shape = tensor.shape

        # Create coordinate grids
        coords = torch.meshgrid(
            *[torch.arange(s, device=tensor.device, dtype=tensor.dtype)
              for s in spatial_shape],
            indexing='ij'
        )
        coords = torch.stack(coords, dim=0)

        # Add displacement
        warped_coords = coords + displacement_field

        # Normalize coordinates to [-1, 1] for grid_sample
        for dim in range(len(spatial_shape)):
            warped_coords[dim] = 2.0 * warped_coords[dim] / (spatial_shape[dim] - 1) - 1.0

        # Rearrange for grid_sample (expects [..., D, H, W, 3])
        if len(spatial_shape) == 3:  # 3D case
            grid = warped_coords.permute(1, 2, 3, 0).unsqueeze(0)
            # Reverse order for grid_sample convention
            grid = grid[..., [2, 1, 0]]
        else:
            raise NotImplementedError("Only 3D transforms supported currently")

        # Apply warping
        tensor_batch = tensor.unsqueeze(0).unsqueeze(0)
        warped = torch.nn.functional.grid_sample(
            tensor_batch,
            grid,
            mode=self.mode,
            padding_mode=self.padding_mode,
            align_corners=True
        )

        return warped.squeeze(0).squeeze(0)


class AffineTransform(Transform if HAS_MONAI else object):
    """
    3D Affine transformation for medical images.

    Applies rotation, scaling, and translation transformations
    with medical imaging constraints.
    """

    def __init__(
        self,
        rotation_range: Tuple[float, float] = (-15.0, 15.0),
        scaling_range: Tuple[float, float] = (0.9, 1.1),
        translation_range: Tuple[float, float] = (-10.0, 10.0),
        prob: float = 0.3,
        mode: str = "bilinear",
        padding_mode: str = "border"
    ):
        """
        Initialize affine transform.

        Args:
            rotation_range: Range for rotation angles in degrees
            scaling_range: Range for scaling factors
            translation_range: Range for translation in pixels
            prob: Probability of applying transform
            mode: Interpolation mode
            padding_mode: Padding mode
        """
        self.rotation_range = rotation_range
        self.scaling_range = scaling_range
        self.translation_range = translation_range
        self.prob = prob
        self.mode = mode
        self.padding_mode = padding_mode

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply affine transformation to input tensor.

        Args:
            data: Input tensor (C, H, W, D) or (H, W, D)

        Returns:
            Affine transformed tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Generate affine matrix
        affine_matrix = self._generate_affine_matrix(data.shape)
        affine_matrix = torch.from_numpy(affine_matrix).to(
            data.device, data.dtype
        )

        # Apply transformation
        if data.dim() == 4:  # (C, H, W, D)
            transformed_data = torch.zeros_like(data)
            for c in range(data.shape[0]):
                transformed_data[c] = self._apply_affine(data[c], affine_matrix)
        else:  # (H, W, D)
            transformed_data = self._apply_affine(data, affine_matrix)

        return transformed_data

    def _generate_affine_matrix(self, data_shape: Tuple[int, ...]) -> np.ndarray:
        """Generate random affine transformation matrix."""
        # Get spatial shape
        if len(data_shape) == 4:  # (C, H, W, D)
            spatial_shape = data_shape[1:]
        else:  # (H, W, D)
            spatial_shape = data_shape

        # Sample transformation parameters
        rotation_angles = [
            self.rng.uniform(*self.rotation_range) * np.pi / 180.0
            for _ in range(3)
        ]
        scaling_factors = [
            self.rng.uniform(*self.scaling_range)
            for _ in range(3)
        ]
        translation = [
            self.rng.uniform(*self.translation_range)
            for _ in range(3)
        ]

        # Create rotation matrices
        rx, ry, rz = rotation_angles

        # Rotation around x-axis
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx), np.cos(rx)]
        ])

        # Rotation around y-axis
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])

        # Rotation around z-axis
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz), np.cos(rz), 0],
            [0, 0, 1]
        ])

        # Combined rotation
        R = Rz @ Ry @ Rx

        # Scaling matrix
        S = np.diag(scaling_factors)

        # Combined transformation matrix
        transform_matrix = R @ S

        # Add translation
        affine_matrix = np.eye(4)
        affine_matrix[:3, :3] = transform_matrix
        affine_matrix[:3, 3] = translation

        return affine_matrix

    def _apply_affine(
        self,
        tensor: torch.Tensor,
        affine_matrix: torch.Tensor
    ) -> torch.Tensor:
        """Apply affine transformation to tensor."""
        spatial_shape = tensor.shape

        # Create coordinate grid
        coords = torch.meshgrid(
            *[torch.arange(s, device=tensor.device, dtype=tensor.dtype)
              for s in spatial_shape],
            indexing='ij'
        )
        coords = torch.stack(coords, dim=-1)  # (..., 3)

        # Add homogeneous coordinate
        ones = torch.ones(coords.shape[:-1] + (1,), device=tensor.device, dtype=tensor.dtype)
        coords_homog = torch.cat([coords, ones], dim=-1)  # (..., 4)

        # Apply affine transformation
        coords_transformed = coords_homog @ affine_matrix.t()
        coords_transformed = coords_transformed[..., :3]  # Remove homogeneous coordinate

        # Normalize to [-1, 1] for grid_sample
        for dim in range(3):
            coords_transformed[..., dim] = (
                2.0 * coords_transformed[..., dim] / (spatial_shape[dim] - 1) - 1.0
            )

        # Rearrange for grid_sample
        grid = coords_transformed.unsqueeze(0)
        # Reverse order for grid_sample convention (D, H, W -> W, H, D)
        grid = grid[..., [2, 1, 0]]

        # Apply transformation
        tensor_batch = tensor.unsqueeze(0).unsqueeze(0)
        transformed = torch.nn.functional.grid_sample(
            tensor_batch,
            grid,
            mode=self.mode,
            padding_mode=self.padding_mode,
            align_corners=True
        )

        return transformed.squeeze(0).squeeze(0)


class NonLinearDeformation(Transform if HAS_MONAI else object):
    """
    Non-linear deformation using B-spline basis functions.

    Provides smooth, realistic deformations using B-spline
    control points for medical image augmentation.
    """

    def __init__(
        self,
        control_point_spacing: Union[int, Tuple[int, ...]] = 32,
        deformation_strength: float = 5.0,
        prob: float = 0.15,
        mode: str = "bilinear"
    ):
        """
        Initialize non-linear deformation.

        Args:
            control_point_spacing: Spacing between B-spline control points
            deformation_strength: Maximum deformation strength
            prob: Probability of applying transform
            mode: Interpolation mode
        """
        if isinstance(control_point_spacing, int):
            self.control_point_spacing = (control_point_spacing,) * 3
        else:
            self.control_point_spacing = control_point_spacing

        self.deformation_strength = deformation_strength
        self.prob = prob
        self.mode = mode

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply non-linear deformation to input tensor.

        Args:
            data: Input tensor

        Returns:
            Non-linearly deformed tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Get spatial dimensions
        if data.dim() == 4:  # (C, H, W, D)
            spatial_shape = data.shape[1:]
            has_channels = True
        else:  # (H, W, D)
            spatial_shape = data.shape
            has_channels = False

        # Generate B-spline deformation field
        deformation_field = self._generate_bspline_field(spatial_shape)
        deformation_field = torch.from_numpy(deformation_field).to(
            data.device, data.dtype
        )

        # Apply deformation
        if has_channels:
            deformed_data = torch.zeros_like(data)
            for c in range(data.shape[0]):
                deformed_data[c] = self._apply_deformation(
                    data[c], deformation_field
                )
        else:
            deformed_data = self._apply_deformation(data, deformation_field)

        return deformed_data

    def _generate_bspline_field(self, spatial_shape: Tuple[int, ...]) -> np.ndarray:
        """Generate deformation field using B-spline basis."""
        # Calculate control point grid size
        control_grid_size = tuple(
            (s // cp_spacing) + 1
            for s, cp_spacing in zip(spatial_shape, self.control_point_spacing)
        )

        # Generate random control point displacements
        control_points = self.rng.normal(
            0, self.deformation_strength,
            (3,) + control_grid_size
        )

        # Interpolate to full resolution using B-spline interpolation
        deformation_field = np.zeros((3,) + spatial_shape)

        for dim in range(3):
            # Use scipy for B-spline interpolation
            from scipy.ndimage import zoom
            scale_factors = tuple(
                s / cgs for s, cgs in zip(spatial_shape, control_grid_size)
            )
            deformation_field[dim] = zoom(control_points[dim], scale_factors, order=3)

        return deformation_field

    def _apply_deformation(
        self,
        tensor: torch.Tensor,
        deformation_field: torch.Tensor
    ) -> torch.Tensor:
        """Apply B-spline deformation to tensor."""
        spatial_shape = tensor.shape

        # Create coordinate grids
        coords = torch.meshgrid(
            *[torch.arange(s, device=tensor.device, dtype=tensor.dtype)
              for s in spatial_shape],
            indexing='ij'
        )
        coords = torch.stack(coords, dim=0)

        # Add deformation
        deformed_coords = coords + deformation_field

        # Normalize for grid_sample
        for dim in range(len(spatial_shape)):
            deformed_coords[dim] = (
                2.0 * deformed_coords[dim] / (spatial_shape[dim] - 1) - 1.0
            )

        # Prepare grid for grid_sample
        grid = deformed_coords.permute(1, 2, 3, 0).unsqueeze(0)
        grid = grid[..., [2, 1, 0]]  # Reverse for grid_sample convention

        # Apply deformation
        tensor_batch = tensor.unsqueeze(0).unsqueeze(0)
        deformed = torch.nn.functional.grid_sample(
            tensor_batch,
            grid,
            mode=self.mode,
            padding_mode='border',
            align_corners=True
        )

        return deformed.squeeze(0).squeeze(0)


class AnisotropicScaling(Transform if HAS_MONAI else object):
    """
    Anisotropic scaling for medical images.

    Applies different scaling factors along different axes
    to simulate anisotropic voxel spacing common in medical imaging.
    """

    def __init__(
        self,
        scaling_range: Dict[str, Tuple[float, float]] = None,
        prob: float = 0.2,
        mode: str = "trilinear"
    ):
        """
        Initialize anisotropic scaling.

        Args:
            scaling_range: Scaling ranges for each axis
            prob: Probability of applying transform
            mode: Interpolation mode
        """
        if scaling_range is None:
            scaling_range = {
                'x': (0.8, 1.2),
                'y': (0.8, 1.2),
                'z': (0.5, 2.0)  # More variation in z-direction
            }

        self.scaling_range = scaling_range
        self.prob = prob
        self.mode = mode

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply anisotropic scaling to input tensor.

        Args:
            data: Input tensor

        Returns:
            Anisotropically scaled tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Sample scaling factors
        scale_x = self.rng.uniform(*self.scaling_range['x'])
        scale_y = self.rng.uniform(*self.scaling_range['y'])
        scale_z = self.rng.uniform(*self.scaling_range['z'])

        scaling_factors = [scale_x, scale_y, scale_z]

        # Apply scaling using interpolation
        if data.dim() == 4:  # (C, H, W, D)
            scaled_data = torch.nn.functional.interpolate(
                data.unsqueeze(0),
                scale_factor=scaling_factors,
                mode=self.mode,
                align_corners=True
            ).squeeze(0)
        else:  # (H, W, D)
            scaled_data = torch.nn.functional.interpolate(
                data.unsqueeze(0).unsqueeze(0),
                scale_factor=scaling_factors,
                mode=self.mode,
                align_corners=True
            ).squeeze(0).squeeze(0)

        return scaled_data


def create_spatial_transform(
    transform_type: str = "elastic",
    **kwargs
) -> Union[ElasticTransform, AffineTransform, NonLinearDeformation, AnisotropicScaling]:
    """
    Factory function to create spatial transforms.

    Args:
        transform_type: Type of transform to create
        **kwargs: Transform-specific parameters

    Returns:
        Configured spatial transform
    """
    if transform_type == "elastic":
        return ElasticTransform(**kwargs)
    elif transform_type == "affine":
        return AffineTransform(**kwargs)
    elif transform_type == "nonlinear":
        return NonLinearDeformation(**kwargs)
    elif transform_type == "anisotropic":
        return AnisotropicScaling(**kwargs)
    else:
        raise ValueError(f"Unknown transform type: {transform_type}")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Spatial Augmentation Transforms...")

    # Create sample 3D medical image
    test_image = torch.randn(1, 64, 64, 32)  # Small size for testing
    print(f"Original image shape: {test_image.shape}")

    # Test elastic transform
    print("\nTesting Elastic Transform...")
    elastic_transform = ElasticTransform(
        alpha_range=(10.0, 20.0),
        sigma_range=(3.0, 7.0),
        prob=1.0  # Always apply for testing
    )
    elastic_transformed = elastic_transform(test_image)
    print(f"Elastic transformed shape: {elastic_transformed.shape}")

    # Test affine transform
    print("\nTesting Affine Transform...")
    affine_transform = AffineTransform(
        rotation_range=(-10.0, 10.0),
        scaling_range=(0.9, 1.1),
        prob=1.0
    )
    affine_transformed = affine_transform(test_image)
    print(f"Affine transformed shape: {affine_transformed.shape}")

    # Test non-linear deformation
    print("\nTesting Non-Linear Deformation...")
    nonlinear_transform = NonLinearDeformation(
        control_point_spacing=16,
        deformation_strength=3.0,
        prob=1.0
    )
    nonlinear_transformed = nonlinear_transform(test_image)
    print(f"Non-linear transformed shape: {nonlinear_transformed.shape}")

    # Test anisotropic scaling
    print("\nTesting Anisotropic Scaling...")
    anisotropic_transform = AnisotropicScaling(
        scaling_range={
            'x': (0.9, 1.1),
            'y': (0.9, 1.1),
            'z': (0.7, 1.3)
        },
        prob=1.0
    )
    anisotropic_transformed = anisotropic_transform(test_image)
    print(f"Anisotropic transformed shape: {anisotropic_transformed.shape}")

    # Test factory function
    print("\nTesting Factory Function...")
    elastic_transform2 = create_spatial_transform(
        "elastic",
        alpha_range=(5.0, 15.0),
        prob=0.3
    )
    print(f"Created transform: {type(elastic_transform2).__name__}")

    print("\nAll spatial transform tests completed successfully!")
    print("\nAll spatial transform tests completed successfully!")
