#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Loss Configuration for Medical Image Segmentation

This module provides configuration templates and integration functions
for using advanced loss functions with the hyperparameter optimization
framework. It includes preset configurations for common medical segmentation
scenarios and utilities for seamless integration with Optuna.

Configuration Categories:
- Basic Loss Configurations
- Multi-objective Configurations
- Domain-specific Configurations (brain, cardiac, etc.)
- Curriculum Learning Configurations
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class LossConfig:
    """Configuration class for loss functions and optimization integration."""

    # Basic loss configurations
    BASIC_CONFIGS = {
        "dice_only": {
            "loss_type": "dice",
            "parameters": {},
            "weight": 1.0
        },

        "focal_basic": {
            "loss_type": "focal",
            "parameters": {
                "alpha": 0.25,
                "gamma": 2.0,
                "smooth": 1e-8
            },
            "weight": 1.0
        },

        "tversky_balanced": {
            "loss_type": "tversky",
            "parameters": {
                "alpha": 0.3,
                "beta": 0.7,
                "smooth": 1e-8
            },
            "weight": 1.0
        },

        "boundary_aware": {
            "loss_type": "boundary",
            "parameters": {
                "boundary_weight": 1.0,
                "distance_threshold": 5.0
            },
            "weight": 1.0
        }
    }

    # Combined loss configurations
    COMBINED_CONFIGS = {
        "dice_focal": {
            "components": [
                {
                    "loss_type": "dice",
                    "parameters": {},
                    "weight": 0.5
                },
                {
                    "loss_type": "focal",
                    "parameters": {
                        "alpha": 0.25,
                        "gamma": 2.0
                    },
                    "weight": 0.5
                }
            ],
            "adaptive_weighting": False
        },

        "tversky_boundary": {
            "components": [
                {
                    "loss_type": "tversky",
                    "parameters": {
                        "alpha": 0.3,
                        "beta": 0.7
                    },
                    "weight": 0.7
                },
                {
                    "loss_type": "boundary",
                    "parameters": {
                        "boundary_weight": 1.0
                    },
                    "weight": 0.3
                }
            ],
            "adaptive_weighting": True
        },

        "multi_scale": {
            "components": [
                {
                    "loss_type": "dice",
                    "parameters": {},
                    "weight": 0.4
                },
                {
                    "loss_type": "focal",
                    "parameters": {
                        "alpha": 0.25,
                        "gamma": 2.0
                    },
                    "weight": 0.3
                },
                {
                    "loss_type": "boundary",
                    "parameters": {
                        "boundary_weight": 1.0
                    },
                    "weight": 0.3
                }
            ],
            "adaptive_weighting": True,
            "schedule_type": "cosine"
        }
    }

    # Domain-specific configurations
    DOMAIN_CONFIGS = {
        "brain_tumor": {
            "description": "Optimized for brain tumor segmentation",
            "components": [
                {
                    "loss_type": "tversky",
                    "parameters": {
                        "alpha": 0.3,
                        "beta": 0.7,
                        "class_weights": [1.0, 2.0, 3.0]  # background, edema, core
                    },
                    "weight": 0.6
                },
                {
                    "loss_type": "focal",
                    "parameters": {
                        "alpha": [0.25, 0.75, 1.0],
                        "gamma": 2.0
                    },
                    "weight": 0.4
                }
            ],
            "topk_selection": {
                "enabled": True,
                "k": 0.7,
                "adaptive": True
            }
        },

        "cardiac_segmentation": {
            "description": "Optimized for cardiac structure segmentation",
            "components": [
                {
                    "loss_type": "dice",
                    "parameters": {
                        "smooth": 1e-8
                    },
                    "weight": 0.5
                },
                {
                    "loss_type": "boundary",
                    "parameters": {
                        "boundary_weight": 2.0,
                        "distance_threshold": 3.0
                    },
                    "weight": 0.5
                }
            ],
            "schedule_type": "curriculum",
            "curriculum_stages": [
                {"boundary_weight": 0.5, "duration": 50},
                {"boundary_weight": 1.0, "duration": 50},
                {"boundary_weight": 2.0, "duration": 100}
            ]
        },

        "liver_lesion": {
            "description": "Optimized for liver lesion detection",
            "components": [
                {
                    "loss_type": "focal",
                    "parameters": {
                        "alpha": 0.75,  # High weight for positive class
                        "gamma": 3.0    # Strong focus on hard examples
                    },
                    "weight": 0.7
                },
                {
                    "loss_type": "dice",
                    "parameters": {
                        "smooth": 1e-6
                    },
                    "weight": 0.3
                }
            ],
            "ohem": {
                "enabled": True,
                "keep_ratio": 0.5,
                "min_kept": 200
            }
        }
    }

    # Hyperparameter search spaces for Optuna
    OPTIMIZATION_SPACES = {
        "focal_search": {
            "alpha": {
                "type": "float",
                "low": 0.1,
                "high": 0.9,
                "step": 0.05
            },
            "gamma": {
                "type": "float",
                "low": 1.0,
                "high": 5.0,
                "step": 0.5
            }
        },

        "tversky_search": {
            "alpha": {
                "type": "float",
                "low": 0.1,
                "high": 0.9,
                "step": 0.1
            },
            "beta": {
                "type": "float",
                "low": 0.1,
                "high": 0.9,
                "step": 0.1
            }
        },

        "combined_search": {
            "dice_weight": {
                "type": "float",
                "low": 0.1,
                "high": 0.9,
                "step": 0.1
            },
            "focal_alpha": {
                "type": "float",
                "low": 0.1,
                "high": 0.9,
                "step": 0.05
            },
            "focal_gamma": {
                "type": "float",
                "low": 1.0,
                "high": 4.0,
                "step": 0.5
            },
            "boundary_weight": {
                "type": "float",
                "low": 0.1,
                "high": 2.0,
                "step": 0.1
            }
        },

        "topk_search": {
            "k_ratio": {
                "type": "float",
                "low": 0.3,
                "high": 0.9,
                "step": 0.1
            },
            "base_loss_weight": {
                "type": "float",
                "low": 0.5,
                "high": 2.0,
                "step": 0.1
            }
        }
    }

    @staticmethod
    def get_config(config_name: str) -> Dict[str, Any]:
        """
        Get a predefined configuration by name.

        Args:
            config_name: Name of the configuration

        Returns:
            Configuration dictionary
        """
        # Check basic configs
        if config_name in LossConfig.BASIC_CONFIGS:
            return LossConfig.BASIC_CONFIGS[config_name].copy()

        # Check combined configs
        if config_name in LossConfig.COMBINED_CONFIGS:
            return LossConfig.COMBINED_CONFIGS[config_name].copy()

        # Check domain configs
        if config_name in LossConfig.DOMAIN_CONFIGS:
            return LossConfig.DOMAIN_CONFIGS[config_name].copy()

        raise ValueError(f"Unknown configuration: {config_name}")

    @staticmethod
    def get_search_space(space_name: str) -> Dict[str, Any]:
        """
        Get hyperparameter search space for optimization.

        Args:
            space_name: Name of the search space

        Returns:
            Search space dictionary
        """
        if space_name not in LossConfig.OPTIMIZATION_SPACES:
            raise ValueError(f"Unknown search space: {space_name}")

        return LossConfig.OPTIMIZATION_SPACES[space_name].copy()

    @staticmethod
    def list_available_configs() -> Dict[str, List[str]]:
        """List all available configurations by category."""
        return {
            "basic": list(LossConfig.BASIC_CONFIGS.keys()),
            "combined": list(LossConfig.COMBINED_CONFIGS.keys()),
            "domain_specific": list(LossConfig.DOMAIN_CONFIGS.keys()),
            "optimization_spaces": list(LossConfig.OPTIMIZATION_SPACES.keys())
        }

    @staticmethod
    def save_config(config: Dict[str, Any], filepath: str) -> None:
        """
        Save configuration to JSON file.

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
        Load configuration from JSON file.

        Args:
            filepath: Path to config file

        Returns:
            Configuration dictionary
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    @staticmethod
    def create_optuna_objective(
        config: Dict[str, Any],
        search_space: Dict[str, Any]
    ) -> callable:
        """
        Create Optuna objective function from loss configuration.

        Args:
            config: Base loss configuration
            search_space: Parameter search space

        Returns:
            Optuna objective function
        """
        def objective(trial):
            # Sample parameters from search space
            sampled_params = {}
            for param_name, param_config in search_space.items():
                if param_config["type"] == "float":
                    sampled_params[param_name] = trial.suggest_float(
                        param_name,
                        param_config["low"],
                        param_config["high"],
                        step=param_config.get("step")
                    )
                elif param_config["type"] == "int":
                    sampled_params[param_name] = trial.suggest_int(
                        param_name,
                        param_config["low"],
                        param_config["high"],
                        step=param_config.get("step", 1)
                    )
                elif param_config["type"] == "categorical":
                    sampled_params[param_name] = trial.suggest_categorical(
                        param_name,
                        param_config["choices"]
                    )

            # Merge with base config
            trial_config = config.copy()

            # Update parameters based on sampled values
            if "components" in trial_config:
                # Multi-component loss
                for component in trial_config["components"]:
                    for param, value in sampled_params.items():
                        if param.startswith(component["loss_type"]):
                            param_key = param.replace(f"{component['loss_type']}_", "")
                            component["parameters"][param_key] = value
                        elif param.endswith("_weight") and param.startswith(component["loss_type"]):
                            component["weight"] = value
            else:
                # Single loss
                trial_config["parameters"].update(sampled_params)

            return trial_config

        return objective


def create_loss_from_config(config: Dict[str, Any]) -> callable:
    """
    Create loss function instance from configuration.

    Args:
        config: Loss configuration dictionary

    Returns:
        Configured loss function
    """
    # Import here to avoid circular imports
    from . import (create_boundary_loss, create_combined_loss,
                   create_focal_loss, create_topk_loss, create_tversky_loss)

    loss_type = config.get("loss_type", "dice")
    parameters = config.get("parameters", {})

    if loss_type == "focal":
        return create_focal_loss(**parameters)
    elif loss_type == "tversky":
        return create_tversky_loss(**parameters)
    elif loss_type == "boundary":
        return create_boundary_loss(**parameters)
    elif loss_type == "topk":
        return create_topk_loss(**parameters)
    elif loss_type in ["combined", "multi"]:
        return create_combined_loss(**parameters)
    else:
        # Default to Dice loss
        import torch.nn as nn
        return nn.CrossEntropyLoss()


def get_recommended_config(
    task_type: str,
    data_characteristics: Dict[str, Any]
) -> str:
    """
    Get recommended loss configuration based on task and data characteristics.

    Args:
        task_type: Type of segmentation task
        data_characteristics: Data characteristics (class_imbalance, boundary_complexity, etc.)

    Returns:
        Recommended configuration name
    """
    # Simple rule-based recommendations
    class_imbalance = data_characteristics.get("class_imbalance", "moderate")
    boundary_complexity = data_characteristics.get("boundary_complexity", "moderate")
    num_classes = data_characteristics.get("num_classes", 2)

    # Brain tumor segmentation
    if "brain" in task_type.lower() or "tumor" in task_type.lower():
        return "brain_tumor"

    # Cardiac segmentation
    if "cardiac" in task_type.lower() or "heart" in task_type.lower():
        return "cardiac_segmentation"

    # Liver lesion detection
    if "liver" in task_type.lower() or "lesion" in task_type.lower():
        return "liver_lesion"

    # General recommendations based on characteristics
    if class_imbalance == "severe":
        if boundary_complexity == "high":
            return "tversky_boundary"
        else:
            return "focal_basic"
    elif boundary_complexity == "high":
        return "boundary_aware"
    elif num_classes > 3:
        return "multi_scale"
    else:
        return "dice_focal"


# Example usage and testing
if __name__ == "__main__":
    print("Testing Loss Configuration System...")

    # List available configurations
    print("\nAvailable Configurations:")
    configs = LossConfig.list_available_configs()
    for category, names in configs.items():
        print(f"{category}: {names}")

    # Test getting configurations
    print("\nTesting configuration retrieval...")
    dice_focal_config = LossConfig.get_config("dice_focal")
    print(f"Dice-Focal config: {dice_focal_config}")

    brain_config = LossConfig.get_config("brain_tumor")
    print(f"Brain tumor config: {brain_config}")

    # Test search space
    print("\nTesting search space...")
    focal_space = LossConfig.get_search_space("focal_search")
    print(f"Focal search space: {focal_space}")

    # Test recommendations
    print("\nTesting recommendations...")
    recommendation = get_recommended_config(
        "brain_tumor_segmentation",
        {
            "class_imbalance": "severe",
            "boundary_complexity": "high",
            "num_classes": 3
        }
    )
    print(f"Recommended config: {recommendation}")

    # Test configuration saving/loading
    print("\nTesting save/load...")
    test_config = LossConfig.get_config("dice_focal")
    LossConfig.save_config(test_config, "/tmp/test_config.json")
    loaded_config = LossConfig.load_config("/tmp/test_config.json")
    print(f"Config saved and loaded successfully: {loaded_config == test_config}")

    print("\nAll configuration tests completed successfully!")

    print("\nAll configuration tests completed successfully!")
