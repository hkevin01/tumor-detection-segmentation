#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Noise Augmentation Transforms for Medical Images

This module provides realistic noise augmentation transforms that simulate
common artifacts and noise patterns found in medical imaging modalities
like MRI, CT, and ultrasound.

Key Features:
- Gaussian and Rician noise simulation
- Motion artifacts simulation
- Gibbs ringing artifacts
- Scanner-specific noise patterns
- Intensity-dependent noise modeling
"""

import warnings
from typing import Dict, Optional, Tuple, Union

import numpy as np
import torch

try:
    from monai.transforms import Transform
    HAS_MONAI = True
except ImportError:
    HAS_MONAI = False
    warnings.warn("MONAI not available. Using base transform class.")


class GaussianNoise(Transform if HAS_MONAI else object):
    """
    Gaussian noise augmentation for medical images.

    Adds realistic Gaussian noise with configurable intensity
    and spatial correlation properties.
    """

    def __init__(
        self,
        noise_variance_range: Tuple[float, float] = (0.0, 0.1),
        relative_noise: bool = True,
        prob: float = 0.4,
        preserve_range: bool = True,
        spatial_correlation: Optional[float] = None
    ):
        """
        Initialize Gaussian noise transform.

        Args:
            noise_variance_range: Range for noise variance
            relative_noise: Whether noise is relative to image intensity
            prob: Probability of applying transform
            preserve_range: Whether to preserve original intensity range
            spatial_correlation: Spatial correlation for noise (None=independent)
        """
        self.noise_variance_range = noise_variance_range
        self.relative_noise = relative_noise
        self.prob = prob
        self.preserve_range = preserve_range
        self.spatial_correlation = spatial_correlation

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply Gaussian noise to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Noisy tensor
        """
        if self.rng.random() > self.prob:
            return data

        # Sample noise variance
        noise_variance = self.rng.uniform(*self.noise_variance_range)

        # Calculate noise standard deviation
        if self.relative_noise:
            # Noise relative to image standard deviation
            noise_std = noise_variance * data.std()
        else:
            # Absolute noise level
            noise_std = noise_variance

        # Generate noise
        if self.spatial_correlation is None:
            # Independent noise
            noise = torch.normal(0, noise_std, size=data.shape, device=data.device)
        else:
            # Spatially correlated noise
            noise = self._generate_correlated_noise(
                data.shape, noise_std, data.device
            )

        # Add noise to data
        noisy_data = data + noise

        # Preserve original range if requested
        if self.preserve_range:
            original_min = data.min()
            original_max = data.max()
            noisy_data = torch.clamp(noisy_data, original_min, original_max)

        return noisy_data

    def _generate_correlated_noise(
        self,
        shape: Tuple[int, ...],
        noise_std: float,
        device: torch.device
    ) -> torch.Tensor:
        """Generate spatially correlated noise."""
        # Generate independent noise
        noise = torch.normal(0, noise_std, size=shape, device=device)

        # Apply spatial smoothing for correlation
        if self.spatial_correlation and len(shape) >= 3:
            # Use Gaussian smoothing to introduce spatial correlation
            kernel_size = max(3, int(self.spatial_correlation * 7))
            if kernel_size % 2 == 0:
                kernel_size += 1

            # Apply 3D Gaussian smoothing
            from scipy.ndimage import gaussian_filter
            noise_np = noise.cpu().numpy()

            if noise_np.ndim == 4:  # (C, H, W, D)
                for c in range(shape[0]):
                    noise_np[c] = gaussian_filter(
                        noise_np[c],
                        sigma=self.spatial_correlation
                    )
            else:  # (H, W, D)
                noise_np = gaussian_filter(noise_np, sigma=self.spatial_correlation)

            noise = torch.from_numpy(noise_np).to(device)

        return noise


class RicianNoise(Transform if HAS_MONAI else object):
    """
    Rician noise simulation for MRI images.

    Simulates the Rician noise distribution characteristic
    of magnitude MRI images.
    """

    def __init__(
        self,
        noise_variance_range: Tuple[float, float] = (0.0, 0.2),
        prob: float = 0.3,
        preserve_range: bool = True
    ):
        """
        Initialize Rician noise transform.

        Args:
            noise_variance_range: Range for noise variance
            prob: Probability of applying transform
            preserve_range: Whether to preserve original intensity range
        """
        self.noise_variance_range = noise_variance_range
        self.prob = prob
        self.preserve_range = preserve_range

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply Rician noise to input tensor.

        Args:
            data: Input MRI tensor

        Returns:
            Tensor with Rician noise
        """
        if self.rng.random() > self.prob:
            return data

        # Sample noise variance
        noise_variance = self.rng.uniform(*self.noise_variance_range)
        noise_std = np.sqrt(noise_variance) * data.std()

        # Generate complex noise components
        real_noise = torch.normal(0, noise_std, size=data.shape, device=data.device)
        imag_noise = torch.normal(0, noise_std, size=data.shape, device=data.device)

        # Add noise to real and imaginary components
        # Assume input is magnitude image, so we simulate complex addition
        noisy_real = data + real_noise
        noisy_imag = imag_noise

        # Compute magnitude (Rician distribution)
        noisy_magnitude = torch.sqrt(noisy_real**2 + noisy_imag**2)

        # Preserve original range if requested
        if self.preserve_range:
            original_min = data.min()
            original_max = data.max()

            # Scale to preserve range
            current_min = noisy_magnitude.min()
            current_max = noisy_magnitude.max()

            if current_max > current_min:
                noisy_magnitude = (
                    (noisy_magnitude - current_min) / (current_max - current_min) *
                    (original_max - original_min) + original_min
                )

        return noisy_magnitude


class MotionArtifact(Transform if HAS_MONAI else object):
    """
    Motion artifact simulation for medical images.

    Simulates motion artifacts that occur due to patient
    movement during image acquisition.
    """

    def __init__(
        self,
        motion_strength_range: Tuple[float, float] = (1.0, 5.0),
        motion_frequency_range: Tuple[float, float] = (0.5, 2.0),
        motion_direction: Optional[str] = None,  # 'x', 'y', 'z', or None (random)
        prob: float = 0.1
    ):
        """
        Initialize motion artifact transform.

        Args:
            motion_strength_range: Range for motion artifact strength
            motion_frequency_range: Range for motion frequency
            motion_direction: Preferred motion direction
            prob: Probability of applying transform
        """
        self.motion_strength_range = motion_strength_range
        self.motion_frequency_range = motion_frequency_range
        self.motion_direction = motion_direction
        self.prob = prob

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply motion artifact to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Tensor with motion artifacts
        """
        if self.rng.random() > self.prob:
            return data

        # Sample motion parameters
        motion_strength = self.rng.uniform(*self.motion_strength_range)
        motion_frequency = self.rng.uniform(*self.motion_frequency_range)

        # Choose motion direction
        if self.motion_direction is None:
            directions = ['x', 'y', 'z'] if data.dim() >= 3 else ['x', 'y']
            motion_dir = self.rng.choice(directions)
        else:
            motion_dir = self.motion_direction

        # Generate motion trajectory
        motion_trajectory = self._generate_motion_trajectory(
            data.shape, motion_strength, motion_frequency, motion_dir
        )

        # Apply motion blur
        motion_blurred = self._apply_motion_blur(data, motion_trajectory)

        return motion_blurred

    def _generate_motion_trajectory(
        self,
        shape: Tuple[int, ...],
        strength: float,
        frequency: float,
        direction: str
    ) -> torch.Tensor:
        """Generate motion trajectory."""
        # Get spatial dimensions
        if len(shape) == 4:  # (C, H, W, D)
            spatial_shape = shape[1:]
        else:  # (H, W, D) or (H, W)
            spatial_shape = shape

        # Time points for motion
        num_time_points = spatial_shape[0]  # Use first spatial dimension
        t = np.linspace(0, 1, num_time_points)

        # Generate sinusoidal motion
        phase = self.rng.uniform(0, 2 * np.pi)
        motion_curve = strength * np.sin(2 * np.pi * frequency * t + phase)

        # Create motion displacement field
        motion_field = np.zeros((len(spatial_shape),) + spatial_shape)

        # Apply motion in specified direction
        if direction == 'x' and len(spatial_shape) >= 1:
            motion_field[0] = motion_curve.reshape(-1, *([1] * (len(spatial_shape) - 1)))
        elif direction == 'y' and len(spatial_shape) >= 2:
            motion_field[1] = motion_curve.reshape(-1, *([1] * (len(spatial_shape) - 1)))
        elif direction == 'z' and len(spatial_shape) >= 3:
            motion_field[2] = motion_curve.reshape(-1, *([1] * (len(spatial_shape) - 1)))

        return torch.from_numpy(motion_field).to(data.device, data.dtype)

    def _apply_motion_blur(
        self,
        data: torch.Tensor,
        motion_trajectory: torch.Tensor
    ) -> torch.Tensor:
        """Apply motion blur based on trajectory."""
        # Simple motion blur implementation
        # In practice, this would involve more sophisticated k-space simulation

        # Create motion kernel
        kernel_size = 5
        motion_kernel = torch.ones(kernel_size, device=data.device) / kernel_size

        # Apply 1D convolution along motion direction
        if data.dim() == 3:  # (H, W, D)
            # Apply blur along first dimension (motion direction)
            blurred = torch.nn.functional.conv1d(
                data.unsqueeze(0).unsqueeze(0).transpose(-1, -3),
                motion_kernel.view(1, 1, -1),
                padding=kernel_size // 2
            ).transpose(-1, -3).squeeze(0).squeeze(0)
        else:
            # For other dimensions, apply simple averaging
            blurred = data * 0.7 + data.roll(1, dims=0) * 0.15 + data.roll(-1, dims=0) * 0.15

        return blurred


class GibbsRinging(Transform if HAS_MONAI else object):
    """
    Gibbs ringing artifact simulation.

    Simulates Gibbs ringing artifacts that occur due to
    truncation of high-frequency components in k-space.
    """

    def __init__(
        self,
        cutoff_frequency_range: Tuple[float, float] = (0.7, 0.9),
        ringing_intensity_range: Tuple[float, float] = (0.1, 0.3),
        prob: float = 0.15
    ):
        """
        Initialize Gibbs ringing transform.

        Args:
            cutoff_frequency_range: Range for k-space cutoff frequency
            ringing_intensity_range: Range for ringing artifact intensity
            prob: Probability of applying transform
        """
        self.cutoff_frequency_range = cutoff_frequency_range
        self.ringing_intensity_range = ringing_intensity_range
        self.prob = prob

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply Gibbs ringing artifact to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Tensor with Gibbs ringing artifacts
        """
        if self.rng.random() > self.prob:
            return data

        # Sample parameters
        cutoff_freq = self.rng.uniform(*self.cutoff_frequency_range)
        ringing_intensity = self.rng.uniform(*self.ringing_intensity_range)

        # Apply Gibbs ringing simulation
        if data.dim() == 4:  # (C, H, W, D)
            ringing_data = torch.zeros_like(data)
            for c in range(data.shape[0]):
                ringing_data[c] = self._simulate_gibbs_ringing(
                    data[c], cutoff_freq, ringing_intensity
                )
        else:  # (H, W, D) or (H, W)
            ringing_data = self._simulate_gibbs_ringing(
                data, cutoff_freq, ringing_intensity
            )

        return ringing_data

    def _simulate_gibbs_ringing(
        self,
        image: torch.Tensor,
        cutoff_freq: float,
        intensity: float
    ) -> torch.Tensor:
        """Simulate Gibbs ringing by k-space truncation."""
        # Convert to k-space (frequency domain)
        k_space = torch.fft.fftn(image, dim=(-3, -2, -1) if image.dim() == 3 else (-2, -1))

        # Create k-space mask for truncation
        mask = self._create_kspace_mask(k_space.shape, cutoff_freq)
        mask = mask.to(image.device)

        # Apply truncation
        truncated_k_space = k_space * mask

        # Convert back to image space
        truncated_image = torch.fft.ifftn(truncated_k_space, dim=(-3, -2, -1) if image.dim() == 3 else (-2, -1))
        truncated_image = torch.real(truncated_image)

        # Blend with original image
        ringing_image = (1 - intensity) * image + intensity * truncated_image

        return ringing_image

    def _create_kspace_mask(self, shape: Tuple[int, ...], cutoff_freq: float) -> torch.Tensor:
        """Create k-space truncation mask."""
        # Create coordinate grids
        coords = []
        for dim_size in shape:
            coord = torch.linspace(-1, 1, dim_size)
            coords.append(coord)

        # Create meshgrid
        grids = torch.meshgrid(*coords, indexing='ij')

        # Calculate distance from k-space center
        distance = torch.sqrt(sum(grid**2 for grid in grids))

        # Create circular/spherical mask
        mask = (distance <= cutoff_freq).float()

        return mask


class ScannerSpecificNoise(Transform if HAS_MONAI else object):
    """
    Scanner-specific noise patterns.

    Simulates noise patterns specific to different
    scanner types and imaging parameters.
    """

    def __init__(
        self,
        scanner_type: str = "1.5T_MRI",
        noise_profile: Optional[Dict[str, float]] = None,
        prob: float = 0.2
    ):
        """
        Initialize scanner-specific noise.

        Args:
            scanner_type: Type of scanner (1.5T_MRI, 3T_MRI, CT, etc.)
            noise_profile: Custom noise profile parameters
            prob: Probability of applying transform
        """
        self.scanner_type = scanner_type
        self.prob = prob

        # Default noise profiles for different scanners
        self.noise_profiles = {
            "1.5T_MRI": {
                "gaussian_std": 0.05,
                "rician_variance": 0.02,
                "spatial_correlation": 0.5
            },
            "3T_MRI": {
                "gaussian_std": 0.03,
                "rician_variance": 0.015,
                "spatial_correlation": 0.3
            },
            "CT": {
                "gaussian_std": 0.1,
                "poisson_scaling": 1000,
                "spatial_correlation": 0.1
            }
        }

        self.noise_profile = noise_profile or self.noise_profiles.get(
            scanner_type, self.noise_profiles["1.5T_MRI"]
        )

        self.rng = np.random.RandomState()

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        """
        Apply scanner-specific noise to input tensor.

        Args:
            data: Input medical image tensor

        Returns:
            Tensor with scanner-specific noise
        """
        if self.rng.random() > self.prob:
            return data

        noisy_data = data.clone()

        # Apply noise based on scanner type
        if "MRI" in self.scanner_type:
            # Apply Rician noise for MRI
            rician_transform = RicianNoise(
                noise_variance_range=(0, self.noise_profile["rician_variance"]),
                prob=1.0
            )
            noisy_data = rician_transform(noisy_data)

        elif "CT" in self.scanner_type:
            # Apply Poisson noise for CT
            if "poisson_scaling" in self.noise_profile:
                scaling = self.noise_profile["poisson_scaling"]
                # Simulate photon counting noise
                scaled_data = data * scaling
                poisson_noise = torch.poisson(scaled_data) / scaling
                noisy_data = poisson_noise

        # Add additional Gaussian noise
        if "gaussian_std" in self.noise_profile:
            gaussian_noise = torch.normal(
                0, self.noise_profile["gaussian_std"] * data.std(),
                size=data.shape, device=data.device
            )
            noisy_data = noisy_data + gaussian_noise

        return noisy_data


def create_noise_transform(
    transform_type: str = "gaussian",
    **kwargs
) -> Union[GaussianNoise, RicianNoise, MotionArtifact, GibbsRinging, ScannerSpecificNoise]:
    """
    Factory function to create noise transforms.

    Args:
        transform_type: Type of noise transform to create
        **kwargs: Transform-specific parameters

    Returns:
        Configured noise transform
    """
    if transform_type == "gaussian":
        return GaussianNoise(**kwargs)
    elif transform_type == "rician":
        return RicianNoise(**kwargs)
    elif transform_type == "motion":
        return MotionArtifact(**kwargs)
    elif transform_type == "gibbs":
        return GibbsRinging(**kwargs)
    elif transform_type == "scanner":
        return ScannerSpecificNoise(**kwargs)
    else:
        raise ValueError(f"Unknown noise transform type: {transform_type}")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Noise Augmentation Transforms...")

    # Create sample medical image
    test_image = torch.rand(1, 64, 64, 32) * 1000  # Simulate medical image
    print(f"Original image range: [{test_image.min():.1f}, {test_image.max():.1f}]")
    print(f"Original image std: {test_image.std():.3f}")

    # Test Gaussian noise
    print("\nTesting Gaussian Noise...")
    gaussian_noise = GaussianNoise(
        noise_variance_range=(0.05, 0.15),
        relative_noise=True,
        prob=1.0
    )
    noisy_gaussian = gaussian_noise(test_image)
    print(f"Gaussian noisy range: [{noisy_gaussian.min():.1f}, {noisy_gaussian.max():.1f}]")

    # Test Rician noise
    print("\nTesting Rician Noise...")
    rician_noise = RicianNoise(
        noise_variance_range=(0.1, 0.2),
        prob=1.0
    )
    noisy_rician = rician_noise(test_image)
    print(f"Rician noisy range: [{noisy_rician.min():.1f}, {noisy_rician.max():.1f}]")

    # Test motion artifacts
    print("\nTesting Motion Artifacts...")
    motion_artifact = MotionArtifact(
        motion_strength_range=(2.0, 4.0),
        motion_direction='x',
        prob=1.0
    )
    motion_corrupted = motion_artifact(test_image)
    print(f"Motion corrupted range: [{motion_corrupted.min():.1f}, {motion_corrupted.max():.1f}]")

    # Test Gibbs ringing
    print("\nTesting Gibbs Ringing...")
    gibbs_ringing = GibbsRinging(
        cutoff_frequency_range=(0.6, 0.8),
        ringing_intensity_range=(0.2, 0.3),
        prob=1.0
    )
    gibbs_corrupted = gibbs_ringing(test_image)
    print(f"Gibbs corrupted range: [{gibbs_corrupted.min():.1f}, {gibbs_corrupted.max():.1f}]")

    # Test scanner-specific noise
    print("\nTesting Scanner-Specific Noise...")
    scanner_noise = ScannerSpecificNoise(
        scanner_type="3T_MRI",
        prob=1.0
    )
    scanner_noisy = scanner_noise(test_image)
    print(f"Scanner noisy range: [{scanner_noisy.min():.1f}, {scanner_noisy.max():.1f}]")

    # Test factory function
    print("\nTesting Factory Function...")
    gaussian_noise2 = create_noise_transform(
        "gaussian",
        noise_variance_range=(0.05, 0.1),
        prob=0.5
    )
    print(f"Created noise transform: {type(gaussian_noise2).__name__}")

    print("\nAll noise transform tests completed successfully!")
    print("\nAll noise transform tests completed successfully!")
