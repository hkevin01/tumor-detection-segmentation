#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intensity Augmentation Transforms for Medical Images

This module provides intensity-based augmentation transforms specifically
designed for medical imaging modalities like CT, MRI, and PET. These
transforms address intensity variations common in medical imaging while
preserving diagnostic information.

Key Features:
- Gamma correction for contrast enhancement
- Bias field correction simulation
- Realistic intensity variations
- Modality-specific parameter ranges
"""

import warnings
from typing import Optional, Tuple, Union

import numpy as np
import torch

try:
    from monai.transforms import Transform
    HAS_MONAI = True
except ImportError:
    HAS_MONAI = False
    warnings.warn("MONAI not available. Using base transform class.")


class GammaCorrection(Transform if HAS_MONAI else object):
    """
    Gamma correction for medical image contrast enhancement.

    Applies gamma correction to simulate different imaging conditions
    and enhance contrast in specific intensity ranges.
    """

    def __init__(
        self,
        gamma_range: Tuple[float, float] = (0.7, 1.5),
        prob: float = 0.3,
        preserve_range: bool = True,
        invert_image: bool = False
    ):
        """
        Initialize gamma correction transform.

        Args:
            gamma_range: Range for gamma values (lower=darker, higher=brighter)
            prob: Probability of applying transform
            preserve_range: Whether to preserve original intensity range
            invert_image: Whether to randomly invert image before gamma
        """
        self.gamma_range = gamma_range
        self.prob = prob
        self.preserve_range = preserve_range
        self.invert_image = invert_image

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply gamma correction to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Gamma-corrected tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Sample gamma value
        gamma = self.rng.uniform(*self.gamma_range)

        # Store original range
        if self.preserve_range:
            original_min = data.min()
            original_max = data.max()

        # Normalize to [0, 1] for gamma correction
        data_normalized = (data - data.min()) / (data.max() - data.min() + 1e-8)

        # Optional inversion
        if self.invert_image and self.rng.random() < 0.5:
            data_normalized = 1.0 - data_normalized

        # Apply gamma correction
        gamma_corrected = torch.pow(data_normalized, gamma)

        # Restore original range if requested
        if self.preserve_range:
            gamma_corrected = gamma_corrected * (original_max - original_min) + original_min

        return gamma_corrected


class BiasFieldCorrection(Transform if HAS_MONAI else object):
    """
    Simulate bias field artifacts common in MRI imaging.

    Applies smooth spatial intensity variations to simulate
    bias field artifacts that occur due to magnetic field
    inhomogeneities in MRI scanners.
    """

    def __init__(
        self,
        coefficients_range: Tuple[float, float] = (0.0, 0.5),
        order: int = 3,
        prob: float = 0.2,
        preserve_mean: bool = True
    ):
        """
        Initialize bias field correction transform.

        Args:
            coefficients_range: Range for polynomial coefficients
            order: Order of polynomial bias field
            prob: Probability of applying transform
            preserve_mean: Whether to preserve original mean intensity
        """
        self.coefficients_range = coefficients_range
        self.order = order
        self.prob = prob
        self.preserve_mean = preserve_mean

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply bias field simulation to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Bias field corrected tensor
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

        # Generate bias field
        bias_field = self._generate_bias_field(spatial_shape)
        bias_field = torch.from_numpy(bias_field).to(data.device, data.dtype)

        # Store original mean
        if self.preserve_mean:
            original_mean = data.mean()

        # Apply bias field
        if has_channels:
            # Apply to all channels
            biased_data = data * bias_field.unsqueeze(0)
        else:
            biased_data = data * bias_field

        # Restore mean if requested
        if self.preserve_mean:
            current_mean = biased_data.mean()
            if current_mean > 1e-8:
                biased_data = biased_data * (original_mean / current_mean)

        return biased_data

    def _generate_bias_field(self, spatial_shape: Tuple[int, ...]) -> np.ndarray:
        """Generate smooth bias field using polynomial basis."""
        # Create coordinate grids
        coords = np.meshgrid(
            *[np.linspace(-1, 1, s) for s in spatial_shape],
            indexing='ij'
        )

        # Initialize bias field
        bias_field = np.ones(spatial_shape)

        # Generate polynomial terms
        for order in range(1, self.order + 1):
            for dim in range(len(spatial_shape)):
                # Sample coefficient
                coeff = self.rng.uniform(*self.coefficients_range)

                # Add polynomial term
                bias_field += coeff * (coords[dim] ** order)

        # Ensure positive values
        bias_field = np.exp(bias_field - bias_field.mean())

        return bias_field


class ContrastAdjustment(Transform if HAS_MONAI else object):
    """
    Contrast adjustment for medical images.

    Adjusts image contrast by modifying the intensity distribution
    while preserving important diagnostic features.
    """

    def __init__(
        self,
        contrast_range: Tuple[float, float] = (0.8, 1.2),
        brightness_range: Tuple[float, float] = (-0.1, 0.1),
        prob: float = 0.4,
        preserve_range: bool = True
    ):
        """
        Initialize contrast adjustment transform.

        Args:
            contrast_range: Range for contrast multiplier
            brightness_range: Range for brightness offset
            prob: Probability of applying transform
            preserve_range: Whether to preserve original intensity range
        """
        self.contrast_range = contrast_range
        self.brightness_range = brightness_range
        self.prob = prob
        self.preserve_range = preserve_range

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply contrast adjustment to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Contrast-adjusted tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Sample adjustment parameters
        contrast = self.rng.uniform(*self.contrast_range)
        brightness = self.rng.uniform(*self.brightness_range)

        # Store original range
        if self.preserve_range:
            original_min = data.min()
            original_max = data.max()

        # Calculate mean for contrast adjustment
        mean_intensity = data.mean()

        # Apply contrast and brightness adjustment
        adjusted = contrast * (data - mean_intensity) + mean_intensity + brightness

        # Restore original range if requested
        if self.preserve_range:
            adjusted = torch.clamp(adjusted, original_min, original_max)

        return adjusted


class IntensityShift(Transform if HAS_MONAI else object):
    """
    Random intensity shift for medical images.

    Applies random additive or multiplicative intensity shifts
    to simulate variations in imaging parameters.
    """

    def __init__(
        self,
        shift_range: Tuple[float, float] = (-0.1, 0.1),
        shift_type: str = "additive",  # "additive" or "multiplicative"
        prob: float = 0.3,
        per_channel: bool = False
    ):
        """
        Initialize intensity shift transform.

        Args:
            shift_range: Range for intensity shift values
            shift_type: Type of shift ("additive" or "multiplicative")
            prob: Probability of applying transform
            per_channel: Whether to apply different shifts per channel
        """
        self.shift_range = shift_range
        self.shift_type = shift_type
        self.prob = prob
        self.per_channel = per_channel

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply intensity shift to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Intensity-shifted tensor
        """
        if self.rng.random() > self.prob:
            return data

        if self.per_channel and data.dim() == 4:
            # Apply different shifts per channel
            shifted_data = torch.zeros_like(data)
            for c in range(data.shape[0]):
                shift_value = self.rng.uniform(*self.shift_range)
                shifted_data[c] = self._apply_shift(data[c], shift_value)
            return shifted_data
        else:
            # Apply same shift to all channels
            shift_value = self.rng.uniform(*self.shift_range)
            return self._apply_shift(data, shift_value)

    def _apply_shift(self, data: torch.Tensor, shift_value: float) -> torch.Tensor:
        """Apply intensity shift to data."""
        if self.shift_type == "additive":
            return data + shift_value
        elif self.shift_type == "multiplicative":
            return data * (1.0 + shift_value)
        else:
            raise ValueError(f"Unknown shift type: {self.shift_type}")


class HistogramMatching(Transform if HAS_MONAI else object):
    """
    Histogram matching for intensity standardization.

    Matches the intensity histogram of input images to reference
    histograms to reduce intensity variations between scanners.
    """

    def __init__(
        self,
        reference_histogram: Optional[np.ndarray] = None,
        num_bins: int = 256,
        prob: float = 0.2,
        match_points: int = 100
    ):
        """
        Initialize histogram matching transform.

        Args:
            reference_histogram: Reference histogram for matching
            num_bins: Number of histogram bins
            prob: Probability of applying transform
            match_points: Number of points for histogram matching
        """
        self.reference_histogram = reference_histogram
        self.num_bins = num_bins
        self.prob = prob
        self.match_points = match_points

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply histogram matching to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Histogram-matched tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Convert to numpy for histogram operations
        device = data.device
        data_np = data.cpu().numpy()

        # Generate reference histogram if not provided
        if self.reference_histogram is None:
            ref_histogram = self._generate_reference_histogram(data_np)
        else:
            ref_histogram = self.reference_histogram

        # Apply histogram matching
        matched_data = self._match_histogram(data_np, ref_histogram)

        return torch.from_numpy(matched_data).to(device)

    def _generate_reference_histogram(self, data: np.ndarray) -> np.ndarray:
        """Generate a reference histogram from input data."""
        # Use a smoothed version of the input histogram as reference
        hist, bin_edges = np.histogram(data.flatten(), bins=self.num_bins)

        # Smooth histogram
        from scipy.ndimage import gaussian_filter1d
        smoothed_hist = gaussian_filter1d(hist.astype(float), sigma=1.0)

        return smoothed_hist / smoothed_hist.sum()

    def _match_histogram(self, data: np.ndarray, reference: np.ndarray) -> np.ndarray:
        """Match data histogram to reference histogram."""
        # Calculate data histogram
        data_hist, data_bins = np.histogram(data.flatten(), bins=self.num_bins)
        data_hist = data_hist.astype(float) / data_hist.sum()

        # Calculate cumulative distributions
        data_cdf = np.cumsum(data_hist)
        ref_cdf = np.cumsum(reference)

        # Create mapping between CDFs
        data_bin_centers = (data_bins[:-1] + data_bins[1:]) / 2
        ref_bin_centers = np.linspace(data.min(), data.max(), len(reference))

        # Interpolate mapping
        from scipy.interpolate import interp1d
        mapping = interp1d(
            data_cdf, data_bin_centers,
            bounds_error=False, fill_value='extrapolate'
        )

        # Apply mapping
        matched = mapping(np.interp(data.flatten(), data_bin_centers, data_cdf))

        return matched.reshape(data.shape)


def create_intensity_transform(
    transform_type: str = "gamma",
    **kwargs
) -> Union[GammaCorrection, BiasFieldCorrection, ContrastAdjustment, IntensityShift, HistogramMatching]:
    """
    Factory function to create intensity transforms.

    Args:
        transform_type: Type of transform to create
        **kwargs: Transform-specific parameters

    Returns:
        Configured intensity transform
    """
    if transform_type == "gamma":
        return GammaCorrection(**kwargs)
    elif transform_type == "bias_field":
        return BiasFieldCorrection(**kwargs)
    elif transform_type == "contrast":
        return ContrastAdjustment(**kwargs)
    elif transform_type == "intensity_shift":
        return IntensityShift(**kwargs)
    elif transform_type == "histogram":
        return HistogramMatching(**kwargs)
    else:
        raise ValueError(f"Unknown transform type: {transform_type}")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Intensity Augmentation Transforms...")

    # Create sample medical image data
    test_image = torch.rand(1, 128, 128, 64) * 1000  # Simulate CT data
    print(f"Original image range: [{test_image.min():.1f}, {test_image.max():.1f}]")

    # Test gamma correction
    print("\nTesting Gamma Correction...")
    gamma_transform = GammaCorrection(
        gamma_range=(0.5, 2.0),
        prob=1.0  # Always apply for testing
    )
    gamma_corrected = gamma_transform(test_image)
    print(f"Gamma corrected range: [{gamma_corrected.min():.1f}, {gamma_corrected.max():.1f}]")

    # Test bias field correction
    print("\nTesting Bias Field Simulation...")
    bias_transform = BiasFieldCorrection(
        coefficients_range=(0.0, 0.3),
        order=2,
        prob=1.0
    )
    bias_corrected = bias_transform(test_image)
    print(f"Bias field applied range: [{bias_corrected.min():.1f}, {bias_corrected.max():.1f}]")

    # Test contrast adjustment
    print("\nTesting Contrast Adjustment...")
    contrast_transform = ContrastAdjustment(
        contrast_range=(0.7, 1.3),
        brightness_range=(-0.2, 0.2),
        prob=1.0
    )
    contrast_adjusted = contrast_transform(test_image)
    print(f"Contrast adjusted range: [{contrast_adjusted.min():.1f}, {contrast_adjusted.max():.1f}]")

    # Test intensity shift
    print("\nTesting Intensity Shift...")
    shift_transform = IntensityShift(
        shift_range=(-0.2, 0.2),
        shift_type="multiplicative",
        prob=1.0
    )
    intensity_shifted = shift_transform(test_image)
    print(f"Intensity shifted range: [{intensity_shifted.min():.1f}, {intensity_shifted.max():.1f}]")

    # Test histogram matching
    print("\nTesting Histogram Matching...")
    histogram_transform = HistogramMatching(
        num_bins=128,
        prob=1.0
    )
    histogram_matched = histogram_transform(test_image)
    print(f"Histogram matched range: [{histogram_matched.min():.1f}, {histogram_matched.max():.1f}]")

    # Test factory function
    print("\nTesting Factory Function...")
    gamma_transform2 = create_intensity_transform(
        "gamma",
        gamma_range=(0.8, 1.2),
        prob=0.5
    )
    print(f"Created transform: {type(gamma_transform2).__name__}")

    print("\nAll intensity transform tests completed successfully!")
    print("\nAll intensity transform tests completed successfully!")
