#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Augmentation Configuration for Medical Image Segmentation

This module provides configuration templates and utilities for medical
image augmentation pipelines. It includes domain-specific configurations,
optimization-ready parameter spaces, and integration with hyperparameter
optimization frameworks.

Key Features:
- Domain-specific augmentation configurations
- Optimization parameter spaces for Optuna
- Progressive augmentation schedules
- Scanner-specific noise modeling
- Anatomical constraint configurations
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class AugmentationConfig:
    """Configuration manager for medical image augmentation pipelines."""

    # Domain-specific configurations
    DOMAIN_CONFIGS = {
        "brain_tumor": {
            "description": "Brain tumor segmentation augmentation",
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (5.0, 15.0),
                    "sigma_range": (3.0, 7.0),
                    "prob": 0.3,
                    "anatomical_preservation": 0.9
                },
                {
                    "transform_type": "affine",
                    "rotation_range": (-10.0, 10.0),
                    "scaling_range": (0.9, 1.1),
                    "translation_range": (-5.0, 5.0),
                    "prob": 0.4
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.8, 1.2),
                    "prob": 0.5,
                    "preserve_range": True
                },
                {
                    "transform_type": "bias_field",
                    "coefficients_range": (0.0, 0.2),
                    "order": 2,
                    "prob": 0.3
                },
                {
                    "transform_type": "contrast",
                    "contrast_range": (0.8, 1.2),
                    "brightness_range": (-0.1, 0.1),
                    "prob": 0.4
                }
            ],
            "noise": [
                {
                    "transform_type": "rician",
                    "noise_variance_range": (0.0, 0.05),
                    "prob": 0.2
                },
                {
                    "transform_type": "scanner",
                    "scanner_type": "3T_MRI",
                    "prob": 0.15
                }
            ],
            "medical": [
                {
                    "transform_type": "normalization",
                    "modality": "MRI",
                    "percentile_range": (1.0, 99.0),
                    "zero_center": True
                }
            ]
        },

        "cardiac_segmentation": {
            "description": "Cardiac structure segmentation augmentation",
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (3.0, 10.0),
                    "sigma_range": (2.0, 5.0),
                    "prob": 0.25,
                    "anatomical_preservation": 0.95  # High preservation for cardiac
                },
                {
                    "transform_type": "affine",
                    "rotation_range": (-5.0, 5.0),  # Limited rotation for cardiac
                    "scaling_range": (0.95, 1.05),
                    "prob": 0.3
                },
                {
                    "transform_type": "anisotropic",
                    "scaling_range": {
                        "x": (0.9, 1.1),
                        "y": (0.9, 1.1),
                        "z": (0.8, 1.2)  # More variation in z for cardiac
                    },
                    "prob": 0.2
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.9, 1.1),  # Conservative for cardiac
                    "prob": 0.4
                },
                {
                    "transform_type": "contrast",
                    "contrast_range": (0.9, 1.1),
                    "brightness_range": (-0.05, 0.05),
                    "prob": 0.3
                }
            ],
            "noise": [
                {
                    "transform_type": "gaussian",
                    "noise_variance_range": (0.0, 0.03),
                    "relative_noise": True,
                    "prob": 0.25
                },
                {
                    "transform_type": "motion",
                    "motion_strength_range": (0.5, 2.0),
                    "motion_direction": "z",  # Typical motion direction
                    "prob": 0.1
                }
            ]
        },

        "liver_lesion": {
            "description": "Liver lesion detection augmentation",
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (8.0, 20.0),
                    "sigma_range": (4.0, 8.0),
                    "prob": 0.4,
                    "anatomical_preservation": 0.8
                },
                {
                    "transform_type": "affine",
                    "rotation_range": (-15.0, 15.0),
                    "scaling_range": (0.85, 1.15),
                    "translation_range": (-8.0, 8.0),
                    "prob": 0.5
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.7, 1.3),
                    "prob": 0.6
                },
                {
                    "transform_type": "bias_field",
                    "coefficients_range": (0.0, 0.3),
                    "prob": 0.4
                },
                {
                    "transform_type": "contrast",
                    "contrast_range": (0.7, 1.3),
                    "brightness_range": (-0.15, 0.15),
                    "prob": 0.5
                }
            ],
            "noise": [
                {
                    "transform_type": "scanner",
                    "scanner_type": "CT",
                    "prob": 0.3
                },
                {
                    "transform_type": "gibbs",
                    "cutoff_frequency_range": (0.6, 0.8),
                    "ringing_intensity_range": (0.1, 0.2),
                    "prob": 0.1
                }
            ]
        },

        "lung_segmentation": {
            "description": "Lung structure segmentation augmentation",
            "spatial": [
                {
                    "transform_type": "elastic",
                    "alpha_range": (10.0, 25.0),
                    "sigma_range": (5.0, 10.0),
                    "prob": 0.35,
                    "anatomical_preservation": 0.75  # Allow more deformation for lungs
                },
                {
                    "transform_type": "affine",
                    "rotation_range": (-12.0, 12.0),
                    "scaling_range": (0.9, 1.1),
                    "prob": 0.4
                }
            ],
            "intensity": [
                {
                    "transform_type": "gamma",
                    "gamma_range": (0.8, 1.2),
                    "prob": 0.5
                },
                {
                    "transform_type": "intensity_shift",
                    "shift_range": (-0.1, 0.1),
                    "shift_type": "additive",
                    "prob": 0.3
                }
            ],
            "noise": [
                {
                    "transform_type": "gaussian",
                    "noise_variance_range": (0.0, 0.08),
                    "prob": 0.3
                },
                {
                    "transform_type": "scanner",
                    "scanner_type": "CT",
                    "prob": 0.25
                }
            ]
        }
    }

    # Curriculum learning configurations
    CURRICULUM_CONFIGS = {
        "progressive_3_stage": {
            "description": "3-stage progressive augmentation curriculum",
            "stages": [
                {
                    "name": "easy",
                    "duration": 200,
                    "intensity": [
                        {
                            "transform_type": "gamma",
                            "gamma_range": (0.95, 1.05),
                            "prob": 0.3
                        }
                    ]
                },
                {
                    "name": "medium",
                    "duration": 300,
                    "spatial": [
                        {
                            "transform_type": "affine",
                            "rotation_range": (-5.0, 5.0),
                            "scaling_range": (0.95, 1.05),
                            "prob": 0.3
                        }
                    ],
                    "intensity": [
                        {
                            "transform_type": "gamma",
                            "gamma_range": (0.9, 1.1),
                            "prob": 0.4
                        },
                        {
                            "transform_type": "contrast",
                            "contrast_range": (0.9, 1.1),
                            "prob": 0.3
                        }
                    ]
                },
                {
                    "name": "hard",
                    "duration": 500,
                    "spatial": [
                        {
                            "transform_type": "elastic",
                            "alpha_range": (8.0, 15.0),
                            "sigma_range": (3.0, 6.0),
                            "prob": 0.4
                        },
                        {
                            "transform_type": "affine",
                            "rotation_range": (-10.0, 10.0),
                            "scaling_range": (0.9, 1.1),
                            "prob": 0.4
                        }
                    ],
                    "intensity": [
                        {
                            "transform_type": "gamma",
                            "gamma_range": (0.8, 1.2),
                            "prob": 0.5
                        },
                        {
                            "transform_type": "bias_field",
                            "coefficients_range": (0.0, 0.2),
                            "prob": 0.3
                        }
                    ],
                    "noise": [
                        {
                            "transform_type": "gaussian",
                            "noise_variance_range": (0.0, 0.1),
                            "prob": 0.3
                        }
                    ]
                }
            ]
        }
    }

    # Optimization parameter spaces for Optuna
    OPTIMIZATION_SPACES = {
        "elastic_transform": {
            "alpha_min": {
                "type": "float",
                "low": 0.0,
                "high": 20.0,
                "step": 1.0
            },
            "alpha_max": {
                "type": "float",
                "low": 5.0,
                "high": 30.0,
                "step": 1.0
            },
            "sigma_min": {
                "type": "float",
                "low": 1.0,
                "high": 8.0,
                "step": 0.5
            },
            "sigma_max": {
                "type": "float",
                "low": 3.0,
                "high": 15.0,
                "step": 0.5
            },
            "prob": {
                "type": "float",
                "low": 0.1,
                "high": 0.8,
                "step": 0.05
            },
            "anatomical_preservation": {
                "type": "float",
                "low": 0.5,
                "high": 1.0,
                "step": 0.05
            }
        },

        "intensity_transforms": {
            "gamma_min": {
                "type": "float",
                "low": 0.5,
                "high": 0.9,
                "step": 0.05
            },
            "gamma_max": {
                "type": "float",
                "low": 1.1,
                "high": 2.0,
                "step": 0.05
            },
            "gamma_prob": {
                "type": "float",
                "low": 0.2,
                "high": 0.8,
                "step": 0.05
            },
            "contrast_range": {
                "type": "float",
                "low": 0.1,
                "high": 0.5,
                "step": 0.05
            },
            "bias_field_prob": {
                "type": "float",
                "low": 0.1,
                "high": 0.6,
                "step": 0.05
            }
        },

        "noise_transforms": {
            "gaussian_variance_max": {
                "type": "float",
                "low": 0.02,
                "high": 0.2,
                "step": 0.01
            },
            "noise_prob": {
                "type": "float",
                "low": 0.1,
                "high": 0.5,
                "step": 0.05
            },
            "motion_prob": {
                "type": "float",
                "low": 0.05,
                "high": 0.3,
                "step": 0.05
            }
        },

        "combined_pipeline": {
            "spatial_intensity": {
                "type": "float",
                "low": 0.1,
                "high": 1.0,
                "step": 0.1,
                "description": "Overall intensity scaling for spatial transforms"
            },
            "intensity_intensity": {
                "type": "float",
                "low": 0.1,
                "high": 1.0,
                "step": 0.1,
                "description": "Overall intensity scaling for intensity transforms"
            },
            "noise_intensity": {
                "type": "float",
                "low": 0.0,
                "high": 0.8,
                "step": 0.1,
                "description": "Overall intensity scaling for noise transforms"
            }
        }
    }

    @staticmethod
    def get_domain_config(domain: str) -> Dict[str, Any]:
        """
        Get domain-specific augmentation configuration.

        Args:
            domain: Medical domain name

        Returns:
            Domain configuration dictionary
        """
        if domain not in AugmentationConfig.DOMAIN_CONFIGS:
            available_domains = list(AugmentationConfig.DOMAIN_CONFIGS.keys())
            raise ValueError(f"Unknown domain: {domain}. Available: {available_domains}")

        return AugmentationConfig.DOMAIN_CONFIGS[domain].copy()

    @staticmethod
    def get_curriculum_config(curriculum_type: str) -> Dict[str, Any]:
        """
        Get curriculum learning configuration.

        Args:
            curriculum_type: Type of curriculum configuration

        Returns:
            Curriculum configuration dictionary
        """
        if curriculum_type not in AugmentationConfig.CURRICULUM_CONFIGS:
            available_curricula = list(AugmentationConfig.CURRICULUM_CONFIGS.keys())
            raise ValueError(f"Unknown curriculum: {curriculum_type}. Available: {available_curricula}")

        return AugmentationConfig.CURRICULUM_CONFIGS[curriculum_type].copy()

    @staticmethod
    def get_optimization_space(space_name: str) -> Dict[str, Any]:
        """
        Get optimization parameter space.

        Args:
            space_name: Name of parameter space

        Returns:
            Parameter space dictionary
        """
        if space_name not in AugmentationConfig.OPTIMIZATION_SPACES:
            available_spaces = list(AugmentationConfig.OPTIMIZATION_SPACES.keys())
            raise ValueError(f"Unknown space: {space_name}. Available: {available_spaces}")

        return AugmentationConfig.OPTIMIZATION_SPACES[space_name].copy()

    @staticmethod
    def list_available_configs() -> Dict[str, List[str]]:
        """List all available configurations."""
        return {
            "domains": list(AugmentationConfig.DOMAIN_CONFIGS.keys()),
            "curricula": list(AugmentationConfig.CURRICULUM_CONFIGS.keys()),
            "optimization_spaces": list(AugmentationConfig.OPTIMIZATION_SPACES.keys())
        }

    @staticmethod
    def create_custom_config(
        base_domain: str,
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create custom configuration based on domain with modifications.

        Args:
            base_domain: Base domain configuration
            modifications: Modifications to apply

        Returns:
            Custom configuration dictionary
        """
        base_config = AugmentationConfig.get_domain_config(base_domain)

        # Apply modifications
        for category, changes in modifications.items():
            if category in base_config:
                if isinstance(changes, dict):
                    # Update existing transform parameters
                    for transform_idx, transform_changes in changes.items():
                        if isinstance(transform_idx, int) and transform_idx < len(base_config[category]):
                            base_config[category][transform_idx].update(transform_changes)
                elif isinstance(changes, list):
                    # Replace entire category
                    base_config[category] = changes

        return base_config

    @staticmethod
    def save_config(config: Dict[str, Any], filepath: str) -> None:
        """
        Save augmentation configuration to file.

        Args:
            config: Configuration dictionary
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def load_config(filepath: str) -> Dict[str, Any]:
        """
        Load augmentation configuration from file.

        Args:
            filepath: Path to configuration file

        Returns:
            Configuration dictionary
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validate augmentation configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, raises exception if invalid
        """
        required_categories = ["spatial", "intensity", "noise", "medical"]

        # Check that at least one category is present
        if not any(cat in config for cat in required_categories):
            raise ValueError(f"Configuration must contain at least one of: {required_categories}")

        # Validate transform structure
        for category, transforms in config.items():
            if category in required_categories:
                if not isinstance(transforms, list):
                    raise ValueError(f"Category '{category}' must be a list of transforms")

                for i, transform in enumerate(transforms):
                    if not isinstance(transform, dict):
                        raise ValueError(f"Transform {i} in '{category}' must be a dictionary")

                    if "transform_type" not in transform:
                        raise ValueError(f"Transform {i} in '{category}' must have 'transform_type'")

        return True

    @staticmethod
    def get_recommended_config(
        task_description: str,
        data_characteristics: Dict[str, Any]
    ) -> str:
        """
        Get recommended configuration based on task and data.

        Args:
            task_description: Description of the segmentation task
            data_characteristics: Data characteristics

        Returns:
            Recommended domain configuration name
        """
        task_lower = task_description.lower()

        # Rule-based recommendations
        if "brain" in task_lower or "tumor" in task_lower:
            return "brain_tumor"
        elif "cardiac" in task_lower or "heart" in task_lower:
            return "cardiac_segmentation"
        elif "liver" in task_lower or "lesion" in task_lower:
            return "liver_lesion"
        elif "lung" in task_lower or "chest" in task_lower:
            return "lung_segmentation"
        else:
            # Default based on data characteristics
            class_imbalance = data_characteristics.get("class_imbalance", "moderate")
            anatomy_complexity = data_characteristics.get("anatomy_complexity", "moderate")

            if class_imbalance == "severe":
                return "liver_lesion"  # Has strong augmentation for imbalanced data
            elif anatomy_complexity == "high":
                return "brain_tumor"   # Has careful anatomical preservation
            else:
                return "cardiac_segmentation"  # Conservative default


def create_augmentation_from_config(config: Dict[str, Any]) -> Any:
    """
    Create augmentation pipeline from configuration.

    Args:
        config: Augmentation configuration

    Returns:
        Configured augmentation pipeline
    """
    # Validate configuration
    AugmentationConfig.validate_config(config)

    # Import here to avoid circular imports
    from .composed_augmentation import MedicalAugmentationPipeline

    # Create pipeline
    pipeline = MedicalAugmentationPipeline(config)

    return pipeline


def get_domain_config(domain: str) -> Dict[str, Any]:
    """
    Convenience function to get domain configuration.

    Args:
        domain: Domain name

    Returns:
        Domain configuration
    """
    return AugmentationConfig.get_domain_config(domain)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Augmentation Configuration System...")

    # List available configurations
    print("\nAvailable Configurations:")
    configs = AugmentationConfig.list_available_configs()
    for category, names in configs.items():
        print(f"{category}: {names}")

    # Test domain configuration
    print("\nTesting Domain Configuration...")
    brain_config = AugmentationConfig.get_domain_config("brain_tumor")
    print(f"Brain tumor config has {len(brain_config)} categories")

    cardiac_config = AugmentationConfig.get_domain_config("cardiac_segmentation")
    print(f"Cardiac config has {len(cardiac_config)} categories")

    # Test curriculum configuration
    print("\nTesting Curriculum Configuration...")
    curriculum_config = AugmentationConfig.get_curriculum_config("progressive_3_stage")
    print(f"Curriculum has {len(curriculum_config['stages'])} stages")

    # Test optimization space
    print("\nTesting Optimization Space...")
    elastic_space = AugmentationConfig.get_optimization_space("elastic_transform")
    print(f"Elastic transform space has {len(elastic_space)} parameters")

    # Test custom configuration
    print("\nTesting Custom Configuration...")
    custom_config = AugmentationConfig.create_custom_config(
        "brain_tumor",
        {
            "spatial": {
                0: {"prob": 0.5}  # Increase probability of first spatial transform
            }
        }
    )
    print("Custom config created with modifications")

    # Test configuration validation
    print("\nTesting Configuration Validation...")
    try:
        AugmentationConfig.validate_config(brain_config)
        print("Brain tumor configuration is valid")
    except Exception as e:
        print(f"Validation error: {e}")

    # Test recommendations
    print("\nTesting Recommendations...")
    recommendation = AugmentationConfig.get_recommended_config(
        "Brain tumor segmentation with T1 and FLAIR",
        {
            "class_imbalance": "severe",
            "anatomy_complexity": "high"
        }
    )
    print(f"Recommended configuration: {recommendation}")

    # Test save/load
    print("\nTesting Save/Load...")
    test_config_path = "/tmp/test_augmentation_config.json"
    AugmentationConfig.save_config(brain_config, test_config_path)
    loaded_config = AugmentationConfig.load_config(test_config_path)
    print(f"Configuration saved and loaded successfully: {loaded_config == brain_config}")

    print("\nAll augmentation configuration tests completed successfully!")
