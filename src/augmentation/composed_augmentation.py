#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Composed Augmentation Pipelines for Medical Images

This module provides comprehensive augmentation pipelines that combine
multiple transform types in intelligent ways. It includes adaptive
scheduling, curriculum learning, and optimization-ready configurations.

Key Features:
- Medical-specific augmentation pipelines
- Adaptive transform selection and parameters
- Curriculum learning with progressive difficulty
- Integration with hyperparameter optimization
- Domain-specific pipeline configurations
"""

import warnings
from typing import Any, Callable, Dict, List, Union

import numpy as np
import torch

try:
    from monai.transforms import Compose, Transform
    HAS_MONAI = True
except ImportError:
    HAS_MONAI = False
    warnings.warn("MONAI not available. Using custom composition.")

from .intensity_augmentation import create_intensity_transform
# Import our augmentation modules
from .medical_transforms import create_medical_transform
from .noise_augmentation import create_noise_transform
from .spatial_augmentation import create_spatial_transform


class MedicalAugmentationPipeline:
    """
    Comprehensive medical image augmentation pipeline.

    Combines multiple augmentation types in a configurable pipeline
    optimized for medical image segmentation tasks.
    """

    def __init__(
        self,
        pipeline_config: Dict[str, Any],
        domain: str = "general",
        training_phase: str = "training",  # "training", "validation", "test"
        adaptive_scheduling: bool = True
    ):
        """
        Initialize medical augmentation pipeline.

        Args:
            pipeline_config: Configuration for augmentation pipeline
            domain: Medical domain (brain, cardiac, liver, etc.)
            training_phase: Current training phase
            adaptive_scheduling: Enable adaptive parameter scheduling
        """
        self.pipeline_config = pipeline_config
        self.domain = domain
        self.training_phase = training_phase
        self.adaptive_scheduling = adaptive_scheduling

        # Initialize transform components
        self.transform_components = self._create_transform_components()

        # Adaptive scheduling state
        self.iteration_count = 0
        self.performance_history = []

        # Random state
        self.rng = np.random.RandomState()

    def __call__(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Apply augmentation pipeline to data.

        Args:
            data: Dictionary containing image and segmentation data

        Returns:
            Augmented data dictionary
        """
        if self.training_phase != "training":
            # Only apply augmentation during training
            return data

        # Update adaptive parameters if enabled
        if self.adaptive_scheduling:
            self._update_adaptive_parameters()

        # Apply transforms in order
        augmented_data = data.copy()

        # 1. Medical-specific preprocessing
        if "medical" in self.transform_components:
            augmented_data = self._apply_medical_transforms(augmented_data)

        # 2. Spatial transforms
        if "spatial" in self.transform_components:
            augmented_data = self._apply_spatial_transforms(augmented_data)

        # 3. Intensity transforms
        if "intensity" in self.transform_components:
            augmented_data = self._apply_intensity_transforms(augmented_data)

        # 4. Noise and artifacts
        if "noise" in self.transform_components:
            augmented_data = self._apply_noise_transforms(augmented_data)

        # 5. Post-processing and validation
        augmented_data = self._validate_augmented_data(augmented_data, data)

        self.iteration_count += 1
        return augmented_data

    def _create_transform_components(self) -> Dict[str, List[Callable]]:
        """Create transform components from configuration."""
        components = {}

        # Medical transforms
        if "medical" in self.pipeline_config:
            medical_transforms = []
            for transform_config in self.pipeline_config["medical"]:
                transform = create_medical_transform(**transform_config)
                medical_transforms.append(transform)
            components["medical"] = medical_transforms

        # Spatial transforms
        if "spatial" in self.pipeline_config:
            spatial_transforms = []
            for transform_config in self.pipeline_config["spatial"]:
                transform = create_spatial_transform(**transform_config)
                spatial_transforms.append(transform)
            components["spatial"] = spatial_transforms

        # Intensity transforms
        if "intensity" in self.pipeline_config:
            intensity_transforms = []
            for transform_config in self.pipeline_config["intensity"]:
                transform = create_intensity_transform(**transform_config)
                intensity_transforms.append(transform)
            components["intensity"] = intensity_transforms

        # Noise transforms
        if "noise" in self.pipeline_config:
            noise_transforms = []
            for transform_config in self.pipeline_config["noise"]:
                transform = create_noise_transform(**transform_config)
                noise_transforms.append(transform)
            components["noise"] = noise_transforms

        return components

    def _apply_medical_transforms(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply medical-specific transforms."""
        for transform in self.transform_components["medical"]:
            if hasattr(transform, '__call__'):
                if "image" in data:
                    data["image"] = transform(data["image"])
        return data

    def _apply_spatial_transforms(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply spatial transforms to both image and segmentation."""
        for transform in self.transform_components["spatial"]:
            if hasattr(transform, '__call__'):
                # Apply same spatial transform to image and segmentation
                if "image" in data:
                    # Store random state to ensure same transform for image and seg
                    if hasattr(transform, 'rng'):
                        current_state = transform.rng.get_state()

                    data["image"] = transform(data["image"])

                    if "seg" in data and hasattr(transform, 'rng'):
                        # Restore state and apply same transform to segmentation
                        transform.rng.set_state(current_state)
                        data["seg"] = transform(data["seg"])

        return data

    def _apply_intensity_transforms(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply intensity transforms (only to image, not segmentation)."""
        for transform in self.transform_components["intensity"]:
            if hasattr(transform, '__call__') and "image" in data:
                data["image"] = transform(data["image"])
        return data

    def _apply_noise_transforms(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply noise and artifact transforms."""
        for transform in self.transform_components["noise"]:
            if hasattr(transform, '__call__') and "image" in data:
                data["image"] = transform(data["image"])
        return data

    def _validate_augmented_data(
        self,
        augmented_data: Dict[str, torch.Tensor],
        original_data: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """Validate and fix augmented data."""
        # Check for NaN or infinite values
        for key, tensor in augmented_data.items():
            if torch.isnan(tensor).any() or torch.isinf(tensor).any():
                print(f"Warning: NaN/Inf detected in {key}, reverting to original")
                augmented_data[key] = original_data[key]

        # Ensure segmentation values are still integers
        if "seg" in augmented_data:
            seg = augmented_data["seg"]
            if seg.dtype.is_floating_point:
                # Round to nearest integer for segmentation
                augmented_data["seg"] = torch.round(seg).to(torch.long)

        return augmented_data

    def _update_adaptive_parameters(self):
        """Update transform parameters based on training progress."""
        # This would integrate with training metrics to adaptively adjust parameters
        # For now, implement simple iteration-based scheduling

        progress = min(1.0, self.iteration_count / 1000.0)  # Assume 1000 iterations

        # Reduce augmentation intensity as training progresses
        for category, transforms in self.transform_components.items():
            for transform in transforms:
                if hasattr(transform, 'prob'):
                    # Gradually reduce probability
                    initial_prob = getattr(transform, '_initial_prob', transform.prob)
                    if not hasattr(transform, '_initial_prob'):
                        transform._initial_prob = transform.prob

                    transform.prob = initial_prob * (1.0 - 0.3 * progress)


class AdaptiveAugmentation:
    """
    Adaptive augmentation that adjusts parameters based on model performance.

    Monitors training metrics and adaptively modifies augmentation
    parameters to improve model generalization.
    """

    def __init__(
        self,
        base_pipeline: MedicalAugmentationPipeline,
        adaptation_rate: float = 0.1,
        performance_window: int = 100,
        adaptation_targets: List[str] = None
    ):
        """
        Initialize adaptive augmentation.

        Args:
            base_pipeline: Base augmentation pipeline
            adaptation_rate: Rate of parameter adaptation
            performance_window: Window size for performance averaging
            adaptation_targets: List of metrics to optimize for
        """
        self.base_pipeline = base_pipeline
        self.adaptation_rate = adaptation_rate
        self.performance_window = performance_window
        self.adaptation_targets = adaptation_targets or ["dice_score", "loss"]

        # Performance tracking
        self.performance_history = {target: [] for target in self.adaptation_targets}
        self.parameter_history = []

    def __call__(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply adaptive augmentation."""
        return self.base_pipeline(data)

    def update_performance(self, metrics: Dict[str, float]):
        """
        Update performance metrics for adaptation.

        Args:
            metrics: Current performance metrics
        """
        for target in self.adaptation_targets:
            if target in metrics:
                self.performance_history[target].append(metrics[target])

                # Keep only recent history
                if len(self.performance_history[target]) > self.performance_window:
                    self.performance_history[target].pop(0)

        # Adapt parameters if we have enough history
        if len(self.performance_history[self.adaptation_targets[0]]) >= 10:
            self._adapt_parameters()

    def _adapt_parameters(self):
        """Adapt augmentation parameters based on performance trends."""
        # Calculate performance trends
        trends = {}
        for target in self.adaptation_targets:
            if len(self.performance_history[target]) >= 10:
                recent = self.performance_history[target][-5:]
                older = self.performance_history[target][-10:-5]

                if len(recent) > 0 and len(older) > 0:
                    recent_avg = sum(recent) / len(recent)
                    older_avg = sum(older) / len(older)
                    trends[target] = recent_avg - older_avg

        # Adjust parameters based on trends
        if "dice_score" in trends:
            dice_trend = trends["dice_score"]

            # If dice score is declining, reduce augmentation intensity
            if dice_trend < 0:
                self._reduce_augmentation_intensity()
            # If dice score is improving, can maintain or slightly increase
            elif dice_trend > 0.01:
                self._maintain_augmentation_intensity()

    def _reduce_augmentation_intensity(self):
        """Reduce augmentation intensity."""
        for category, transforms in self.base_pipeline.transform_components.items():
            for transform in transforms:
                if hasattr(transform, 'prob'):
                    transform.prob = max(0.05, transform.prob * 0.9)

                # Reduce specific parameter ranges
                if hasattr(transform, 'alpha_range'):
                    current_range = transform.alpha_range
                    new_range = (current_range[0] * 0.9, current_range[1] * 0.9)
                    transform.alpha_range = new_range

    def _maintain_augmentation_intensity(self):
        """Maintain current augmentation intensity."""
        # Could implement slight increases or maintain current levels
        pass


class CurriculumAugmentation:
    """
    Curriculum learning for data augmentation.

    Gradually increases augmentation difficulty throughout training
    to improve model robustness and convergence.
    """

    def __init__(
        self,
        curriculum_stages: List[Dict[str, Any]],
        stage_durations: List[int],
        transition_type: str = "smooth"
    ):
        """
        Initialize curriculum augmentation.

        Args:
            curriculum_stages: List of augmentation configurations for each stage
            stage_durations: Duration of each curriculum stage
            transition_type: Type of transition between stages ("hard", "smooth")
        """
        self.curriculum_stages = curriculum_stages
        self.stage_durations = stage_durations
        self.transition_type = transition_type

        # Curriculum state
        self.current_stage = 0
        self.stage_progress = 0
        self.total_stages = len(curriculum_stages)

        # Initialize with first stage
        self.current_pipeline = MedicalAugmentationPipeline(
            self.curriculum_stages[0]
        )

    def __call__(self, data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Apply curriculum augmentation."""
        # Update curriculum stage if needed
        self._update_curriculum_stage()

        # Apply current pipeline
        return self.current_pipeline(data)

    def _update_curriculum_stage(self):
        """Update curriculum stage based on progress."""
        self.stage_progress += 1

        # Check if we should advance to next stage
        if (self.stage_progress >= self.stage_durations[self.current_stage] and
            self.current_stage < self.total_stages - 1):

            if self.transition_type == "hard":
                # Hard transition to next stage
                self.current_stage += 1
                self.stage_progress = 0
                self.current_pipeline = MedicalAugmentationPipeline(
                    self.curriculum_stages[self.current_stage]
                )
            else:
                # Smooth transition
                self._smooth_stage_transition()

    def _smooth_stage_transition(self):
        """Implement smooth transition between curriculum stages."""
        # Calculate interpolation weights
        transition_window = min(50, self.stage_durations[self.current_stage] // 4)

        if self.stage_progress >= self.stage_durations[self.current_stage] - transition_window:
            # In transition period
            progress_in_transition = (
                self.stage_progress -
                (self.stage_durations[self.current_stage] - transition_window)
            ) / transition_window

            # Interpolate between current and next stage configurations
            current_config = self.curriculum_stages[self.current_stage]
            next_config = self.curriculum_stages[self.current_stage + 1]

            interpolated_config = self._interpolate_configs(
                current_config, next_config, progress_in_transition
            )

            # Update pipeline with interpolated configuration
            self.current_pipeline = MedicalAugmentationPipeline(interpolated_config)

    def _interpolate_configs(
        self,
        config1: Dict[str, Any],
        config2: Dict[str, Any],
        alpha: float
    ) -> Dict[str, Any]:
        """Interpolate between two augmentation configurations."""
        interpolated = {}

        for category in config1:
            if category in config2:
                interpolated[category] = []

                # Interpolate each transform in the category
                for i, transform1 in enumerate(config1[category]):
                    if i < len(config2[category]):
                        transform2 = config2[category][i]
                        interpolated_transform = self._interpolate_transform_config(
                            transform1, transform2, alpha
                        )
                        interpolated[category].append(interpolated_transform)

        return interpolated

    def _interpolate_transform_config(
        self,
        config1: Dict[str, Any],
        config2: Dict[str, Any],
        alpha: float
    ) -> Dict[str, Any]:
        """Interpolate between two transform configurations."""
        interpolated = config1.copy()

        # Interpolate numeric parameters
        for key in config1:
            if key in config2:
                if isinstance(config1[key], (int, float)) and isinstance(config2[key], (int, float)):
                    interpolated[key] = (1 - alpha) * config1[key] + alpha * config2[key]
                elif isinstance(config1[key], tuple) and isinstance(config2[key], tuple):
                    # Interpolate tuple ranges
                    if len(config1[key]) == 2 and len(config2[key]) == 2:
                        interpolated[key] = (
                            (1 - alpha) * config1[key][0] + alpha * config2[key][0],
                            (1 - alpha) * config1[key][1] + alpha * config2[key][1]
                        )

        return interpolated


def create_augmentation_pipeline(
    pipeline_type: str = "comprehensive",
    domain: str = "general",
    **kwargs
) -> Union[MedicalAugmentationPipeline, AdaptiveAugmentation, CurriculumAugmentation]:
    """
    Factory function to create augmentation pipelines.

    Args:
        pipeline_type: Type of pipeline ("comprehensive", "adaptive", "curriculum")
        domain: Medical domain
        **kwargs: Pipeline-specific parameters

    Returns:
        Configured augmentation pipeline
    """
    if pipeline_type == "adaptive":
        base_pipeline = MedicalAugmentationPipeline(
            kwargs.get("pipeline_config", {}),
            domain=domain
        )
        return AdaptiveAugmentation(base_pipeline, **kwargs)
    elif pipeline_type == "curriculum":
        return CurriculumAugmentation(**kwargs)
    else:  # comprehensive
        return MedicalAugmentationPipeline(
            kwargs.get("pipeline_config", {}),
            domain=domain,
            **kwargs
        )


# Example usage and testing
if __name__ == "__main__":
    print("Testing Composed Augmentation Pipelines...")

    # Create sample data
    test_data = {
        "image": torch.randn(1, 64, 64, 32),
        "seg": torch.randint(0, 4, (64, 64, 32))
    }

    print(f"Original image shape: {test_data['image'].shape}")
    print(f"Original seg shape: {test_data['seg'].shape}")

    # Test comprehensive pipeline
    print("\nTesting Comprehensive Pipeline...")

    comprehensive_config = {
        "spatial": [
            {
                "transform_type": "elastic",
                "alpha_range": (10.0, 20.0),
                "sigma_range": (3.0, 7.0),
                "prob": 0.3
            }
        ],
        "intensity": [
            {
                "transform_type": "gamma",
                "gamma_range": (0.8, 1.2),
                "prob": 0.4
            }
        ],
        "noise": [
            {
                "transform_type": "gaussian",
                "noise_variance_range": (0.0, 0.1),
                "prob": 0.2
            }
        ]
    }

    comprehensive_pipeline = MedicalAugmentationPipeline(
        comprehensive_config,
        domain="brain"
    )

    augmented_data = comprehensive_pipeline(test_data)
    print(f"Augmented image shape: {augmented_data['image'].shape}")
    print(f"Augmented seg shape: {augmented_data['seg'].shape}")

    # Test curriculum pipeline
    print("\nTesting Curriculum Pipeline...")

    curriculum_stages = [
        # Easy stage - minimal augmentation
        {
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.9, 1.1),
                    "prob": 0.2
                }
            ]
        },
        # Medium stage
        {
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (5.0, 10.0),
                    "prob": 0.2
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.8, 1.2),
                    "prob": 0.3
                }
            ]
        },
        # Hard stage - full augmentation
        {
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (10.0, 20.0),
                    "prob": 0.4
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.7, 1.3),
                    "prob": 0.5
                }
            ],
            "noise": [
                {
                    "transform_type": "gaussian",
                    "noise_variance_range": (0.0, 0.15),
                    "prob": 0.3
                }
            ]
        }
    ]

    curriculum_pipeline = CurriculumAugmentation(
        curriculum_stages,
        stage_durations=[100, 200, 300]
    )

    # Simulate curriculum progression
    for i in range(5):
        augmented_data = curriculum_pipeline(test_data)
        print(f"Curriculum step {i+1}: Current stage = {curriculum_pipeline.current_stage}")

    # Test factory function
    print("\nTesting Factory Function...")
    adaptive_pipeline = create_augmentation_pipeline(
        "adaptive",
        pipeline_config=comprehensive_config,
        domain="cardiac"
    )
    print(f"Created pipeline: {type(adaptive_pipeline).__name__}")

    print("\nAll augmentation pipeline tests completed successfully!")
    print("\nAll augmentation pipeline tests completed successfully!")
