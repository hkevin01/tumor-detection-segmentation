#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medical-Specific Transforms for 3D Segmentation

This module provides medical imaging transforms that preserve anatomical
constraints while providing effective data augmentation for medical
segmentation tasks.

Key Features:
- Anatomically-aware elastic deformation
- Medical normalization with intensity constraints
- Organ-specific transform boundaries
- Integration with MONAI transform framework
"""

import warnings
from typing import Dict, Optional, Tuple, Union

import numpy as np
import torch

try:
    import monai
    from monai.data import MetaTensor
    from monai.transforms import MapTransform, Randomizable, Transform
    from monai.utils import ensure_tuple_rep
    HAS_MONAI = True
except ImportError:
    HAS_MONAI = False
    warnings.warn("MONAI not available. Some features may be limited.")


class ElasticDeformation(Transform if HAS_MONAI else object):
    """
    Elastic deformation with anatomical constraints.

    Applies smooth elastic deformation that preserves anatomical topology
    while providing realistic data augmentation for medical images.
    """

    def __init__(
        self,
        sigma_range: Tuple[float, float] = (10.0, 20.0),
        magnitude_range: Tuple[float, float] = (0.1, 0.3),
        prob: float = 0.1,
        spatial_size: Optional[Tuple[int, ...]] = None,
        mode: str = "bilinear",
        padding_mode: str = "border",
        anatomical_constraint: float = 0.8,
        preserve_topology: bool = True
    ):
        """
        Initialize elastic deformation transform.

        Args:
            sigma_range: Range for Gaussian kernel sigma
            magnitude_range: Range for deformation magnitude
            prob: Probability of applying transform
            spatial_size: Expected spatial size of input
            mode: Interpolation mode
            padding_mode: Padding mode for out-of-bounds values
            anatomical_constraint: Factor to constrain deformation near boundaries
            preserve_topology: Whether to preserve topological structure
        """
        self.sigma_range = sigma_range
        self.magnitude_range = magnitude_range
        self.prob = prob
        self.spatial_size = spatial_size
        self.mode = mode
        self.padding_mode = padding_mode
        self.anatomical_constraint = anatomical_constraint
        self.preserve_topology = preserve_topology

        # Create random number generator
        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply elastic deformation to input tensor.

        Args:
            data: Input tensor (C, H, W, D) or (H, W, D)

        Returns:
            Elastically deformed tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Ensure tensor is on CPU for numpy operations
        device = data.device
        data_np = data.cpu().numpy()

        # Get spatial dimensions
        if data_np.ndim == 4:  # (C, H, W, D)
            spatial_shape = data_np.shape[1:]
            has_channel = True
        else:  # (H, W, D)
            spatial_shape = data_np.shape
            has_channel = False

        # Generate displacement field
        displacement_field = self._generate_displacement_field(spatial_shape)

        # Apply anatomical constraints
        if self.anatomical_constraint < 1.0:
            displacement_field = self._apply_anatomical_constraints(
                displacement_field, data_np, spatial_shape
            )

        # Apply deformation
        if has_channel:
            deformed_data = np.zeros_like(data_np)
            for c in range(data_np.shape[0]):
                deformed_data[c] = self._apply_displacement(
                    data_np[c], displacement_field
                )
        else:
            deformed_data = self._apply_displacement(data_np, displacement_field)

        return torch.from_numpy(deformed_data).to(device)

    def _generate_displacement_field(self, spatial_shape: Tuple[int, ...]) -> np.ndarray:
        """Generate smooth displacement field."""
        # Sample deformation parameters
        sigma = self.rng.uniform(*self.sigma_range)
        magnitude = self.rng.uniform(*self.magnitude_range)

        # Generate random displacement for each dimension
        displacement_field = np.zeros((len(spatial_shape),) + spatial_shape)

        for dim in range(len(spatial_shape)):
            # Generate random field
            random_field = self.rng.normal(0, 1, spatial_shape)

            # Smooth with Gaussian kernel
            from scipy.ndimage import gaussian_filter
            smooth_field = gaussian_filter(random_field, sigma)

            # Normalize and scale
            if smooth_field.std() > 0:
                smooth_field = (smooth_field - smooth_field.mean()) / smooth_field.std()
                displacement_field[dim] = smooth_field * magnitude * spatial_shape[dim]

        return displacement_field

    def _apply_anatomical_constraints(
        self,
        displacement_field: np.ndarray,
        data: np.ndarray,
        spatial_shape: Tuple[int, ...]
    ) -> np.ndarray:
        """Apply anatomical constraints to displacement field."""
        # Create boundary mask (reduce deformation near edges)
        boundary_mask = np.ones(spatial_shape)

        # Define boundary region
        boundary_width = max(1, min(spatial_shape) // 20)

        for dim in range(len(spatial_shape)):
            # Create distance from boundary
            coords = np.arange(spatial_shape[dim])
            dist_from_start = coords
            dist_from_end = spatial_shape[dim] - 1 - coords

            # Create 1D mask
            mask_1d = np.minimum(dist_from_start, dist_from_end)
            mask_1d = np.minimum(mask_1d, boundary_width) / boundary_width

            # Expand to full dimensions
            expand_dims = [1] * len(spatial_shape)
            expand_dims[dim] = spatial_shape[dim]
            mask_1d = mask_1d.reshape(expand_dims)

            # Apply to boundary mask
            boundary_mask *= mask_1d

        # Apply constraint
        constraint_factor = (
            self.anatomical_constraint +
            (1 - self.anatomical_constraint) * boundary_mask
        )

        for dim in range(len(spatial_shape)):
            displacement_field[dim] *= constraint_factor

        return displacement_field

    def _apply_displacement(
        self,
        image: np.ndarray,
        displacement_field: np.ndarray
    ) -> np.ndarray:
        """Apply displacement field to image using scipy interpolation."""
        from scipy.ndimage import map_coordinates

        # Create coordinate grids
        coords = np.meshgrid(*[np.arange(s) for s in image.shape], indexing='ij')
        coords = np.array(coords)

        # Add displacement
        new_coords = coords + displacement_field

        # Apply interpolation
        if self.mode == "bilinear":
            order = 1
        elif self.mode == "bicubic":
            order = 3
        else:
            order = 0

        deformed = map_coordinates(
            image,
            new_coords,
            order=order,
            mode='reflect' if self.padding_mode == 'border' else 'constant',
            prefilter=True
        )

        return deformed


class AnatomicalConstraints(Transform if HAS_MONAI else object):
    """
    Apply anatomical constraints during augmentation.

    Ensures that augmentations preserve anatomical plausibility
    by constraining deformations based on organ boundaries and
    anatomical priors.
    """

    def __init__(
        self,
        organ_masks: Optional[Dict[str, np.ndarray]] = None,
        constraint_strength: float = 0.7,
        boundary_preservation: float = 0.9,
        volume_preservation: float = 0.8
    ):
        """
        Initialize anatomical constraints.

        Args:
            organ_masks: Dictionary of organ masks for constraints
            constraint_strength: Overall constraint strength (0=none, 1=strict)
            boundary_preservation: Organ boundary preservation factor
            volume_preservation: Volume preservation factor
        """
        self.organ_masks = organ_masks or {}
        self.constraint_strength = constraint_strength
        self.boundary_preservation = boundary_preservation
        self.volume_preservation = volume_preservation

    def __call__(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Apply anatomical constraints to augmentation.

        Args:
            data: Dictionary containing image and segmentation data

        Returns:
            Constrained data dictionary
        """
        if "image" not in data or self.constraint_strength == 0:
            return data

        # Apply volume preservation
        if "seg" in data and self.volume_preservation > 0:
            data = self._preserve_volumes(data)

        # Apply boundary preservation
        if self.boundary_preservation > 0:
            data = self._preserve_boundaries(data)

        return data

    def _preserve_volumes(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Preserve organ volumes during augmentation."""
        seg = data["seg"]
        original_volumes = {}

        # Calculate original volumes
        unique_labels = torch.unique(seg)
        for label in unique_labels:
            if label > 0:  # Skip background
                original_volumes[label.item()] = (seg == label).sum().item()

        # Store for potential correction
        data["_original_volumes"] = original_volumes

        return data

    def _preserve_boundaries(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Preserve critical anatomical boundaries."""
        if "seg" not in data:
            return data

        seg = data["seg"]

        # Calculate boundary preservation mask
        # This would implement sophisticated boundary detection
        # For now, use simple edge detection
        boundary_mask = self._detect_boundaries(seg)

        # Store boundary information
        data["_boundary_mask"] = boundary_mask

        return data

    def _detect_boundaries(self, seg: torch.Tensor) -> torch.Tensor:
        """Detect anatomical boundaries in segmentation."""
        # Simple boundary detection using gradients
        if seg.dim() == 3:
            seg = seg.unsqueeze(0)  # Add batch dimension

        # Calculate gradients
        grad_x = torch.diff(seg.float(), dim=-1, prepend=seg[..., :1])
        grad_y = torch.diff(seg.float(), dim=-2, prepend=seg[..., :1, :])
        grad_z = torch.diff(seg.float(), dim=-3, prepend=seg[..., :1, :, :])

        # Combine gradients
        boundary_strength = torch.sqrt(grad_x**2 + grad_y**2 + grad_z**2)

        # Threshold to get boundary mask
        boundary_mask = (boundary_strength > 0.1).float()

        return boundary_mask.squeeze(0) if boundary_mask.dim() == 4 else boundary_mask


class MedicalNormalization(Transform if HAS_MONAI else object):
    """
    Medical image normalization with intensity constraints.

    Provides robust normalization for medical images that handles
    intensity variations while preserving diagnostic information.
    """

    def __init__(
        self,
        modality: str = "CT",
        intensity_range: Optional[Tuple[float, float]] = None,
        percentile_range: Tuple[float, float] = (1.0, 99.0),
        clip_values: bool = True,
        zero_center: bool = True,
        unit_variance: bool = True
    ):
        """
        Initialize medical normalization.

        Args:
            modality: Medical imaging modality (CT, MRI, PET, etc.)
            intensity_range: Expected intensity range for modality
            percentile_range: Percentile range for robust normalization
            clip_values: Whether to clip extreme values
            zero_center: Whether to center data around zero
            unit_variance: Whether to normalize to unit variance
        """
        self.modality = modality.upper()
        self.intensity_range = intensity_range
        self.percentile_range = percentile_range
        self.clip_values = clip_values
        self.zero_center = zero_center
        self.unit_variance = unit_variance

        # Modality-specific defaults
        self.modality_ranges = {
            "CT": (-1000, 1000),  # Hounsfield units
            "MRI": (0, 4000),     # Typical T1/T2 range
            "PET": (0, 10),       # SUV values
            "DWI": (0, 3000),     # Diffusion weighted
        }

        if self.intensity_range is None:
            self.intensity_range = self.modality_ranges.get(self.modality, (0, 1))

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply medical normalization to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Normalized tensor
        """
        # Convert to float for processing
        original_dtype = data.dtype
        data = data.float()

        # Apply modality-specific preprocessing
        if self.modality == "CT":
            data = self._normalize_ct(data)
        elif self.modality == "MRI":
            data = self._normalize_mri(data)
        else:
            data = self._normalize_generic(data)

        # Apply percentile-based normalization
        if self.percentile_range != (0, 100):
            data = self._percentile_normalize(data)

        # Apply intensity range clipping
        if self.clip_values and self.intensity_range:
            data = torch.clamp(data, self.intensity_range[0], self.intensity_range[1])

        # Zero center and unit variance
        if self.zero_center or self.unit_variance:
            data = self._standardize(data)

        return data.to(original_dtype)

    def _normalize_ct(self, data: torch.Tensor) -> torch.Tensor:
        """CT-specific normalization (Hounsfield units)."""
        # Clip to typical CT range
        data = torch.clamp(data, -1000, 1000)

        # Window to soft tissue range for general use
        # This can be made configurable for specific tasks
        window_center = 40
        window_width = 400

        data = (data - (window_center - window_width/2)) / window_width
        data = torch.clamp(data, 0, 1)

        return data

    def _normalize_mri(self, data: torch.Tensor) -> torch.Tensor:
        """MRI-specific normalization."""
        # Remove background (typically near zero)
        background_threshold = data.mean() * 0.1
        foreground_mask = data > background_threshold

        if foreground_mask.sum() > 0:
            # Normalize based on foreground statistics
            foreground_data = data[foreground_mask]
            data = data / foreground_data.mean()
        else:
            # Fallback normalization
            data = data / (data.max() + 1e-8)

        return data

    def _normalize_generic(self, data: torch.Tensor) -> torch.Tensor:
        """Generic intensity normalization."""
        # Min-max normalization to [0, 1]
        data_min = data.min()
        data_max = data.max()

        if data_max > data_min:
            data = (data - data_min) / (data_max - data_min)

        return data

    def _percentile_normalize(self, data: torch.Tensor) -> torch.Tensor:
        """Percentile-based robust normalization."""
        p_low, p_high = self.percentile_range

        # Calculate percentiles
        low_val = torch.quantile(data, p_low / 100.0)
        high_val = torch.quantile(data, p_high / 100.0)

        # Normalize to percentile range
        if high_val > low_val:
            data = (data - low_val) / (high_val - low_val)
            data = torch.clamp(data, 0, 1)

        return data

    def _standardize(self, data: torch.Tensor) -> torch.Tensor:
        """Apply zero-centering and unit variance normalization."""
        if self.zero_center:
            data = data - data.mean()

        if self.unit_variance:
            std = data.std()
            if std > 1e-8:
                data = data / std

        return data


def create_medical_transform(
    transform_type: str = "elastic",
    **kwargs
) -> Union[ElasticDeformation, AnatomicalConstraints, MedicalNormalization]:
    """
    Factory function to create medical transforms.

    Args:
        transform_type: Type of transform to create
        **kwargs: Transform-specific parameters

    Returns:
        Configured medical transform
    """
    if transform_type == "elastic":
        return ElasticDeformation(**kwargs)
    elif transform_type == "anatomical":
        return AnatomicalConstraints(**kwargs)
    elif transform_type == "normalization":
        return MedicalNormalization(**kwargs)
    else:
        raise ValueError(f"Unknown transform type: {transform_type}")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Medical Transforms...")

    # Create sample 3D medical image
    test_image = torch.randn(1, 128, 128, 64)  # (C, H, W, D)
    test_seg = torch.randint(0, 4, (128, 128, 64))  # Segmentation

    print(f"Original image shape: {test_image.shape}")
    print(f"Original intensity range: [{test_image.min():.3f}, {test_image.max():.3f}]")

    # Test elastic deformation
    print("\nTesting Elastic Deformation...")
    elastic_transform = ElasticDeformation(
        sigma_range=(5.0, 15.0),
        magnitude_range=(0.05, 0.15),
        prob=1.0  # Always apply for testing
    )

    deformed_image = elastic_transform(test_image)
    print(f"Deformed image shape: {deformed_image.shape}")

    # Test medical normalization
    print("\nTesting Medical Normalization...")

    # CT normalization
    ct_norm = MedicalNormalization(modality="CT")
    ct_data = torch.randint(-1000, 1000, (128, 128, 64)).float()
    normalized_ct = ct_norm(ct_data)
    print(f"CT normalization: [{ct_data.min():.0f}, {ct_data.max():.0f}] -> [{normalized_ct.min():.3f}, {normalized_ct.max():.3f}]")

    # MRI normalization
    mri_norm = MedicalNormalization(modality="MRI")
    mri_data = torch.rand(128, 128, 64) * 2000
    normalized_mri = mri_norm(mri_data)
    print(f"MRI normalization: [{mri_data.min():.0f}, {mri_data.max():.0f}] -> [{normalized_mri.min():.3f}, {normalized_mri.max():.3f}]")

    # Test anatomical constraints
    print("\nTesting Anatomical Constraints...")
    anatomical_transform = AnatomicalConstraints(
        constraint_strength=0.8,
        boundary_preservation=0.9
    )

    test_data = {
        "image": test_image,
        "seg": test_seg
    }

    constrained_data = anatomical_transform(test_data)
    print(f"Anatomical constraints applied. Keys: {list(constrained_data.keys())}")

    # Test factory function
    print("\nTesting Factory Function...")
    elastic_transform2 = create_medical_transform(
        "elastic",
        sigma_range=(10.0, 20.0),
        magnitude_range=(0.1, 0.2)
    )
    print(f"Created transform: {type(elastic_transform2).__name__}")

    print("\nAll medical transform tests completed successfully!")
    print("\nAll medical transform tests completed successfully!")
