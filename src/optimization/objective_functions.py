#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Objective functions for hyperparameter optimization in medical image segmentation.

This module provides objective functions that can be used with Optuna to optimize
model performance based on various metrics like Dice score, training efficiency,
and model complexity.
"""

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import optuna
import torch

from ..training.train_enhanced import train_model_with_config
from .hyperparameter_search import HyperparameterSearchSpace


class SegmentationObjective:
    """
    Objective function for medical image segmentation optimization.

    This class provides a comprehensive objective function that considers:
    - Segmentation performance (Dice score, Hausdorff distance)
    - Training efficiency (convergence speed, memory usage)
    - Model complexity (parameter count, inference time)
    """

    def __init__(
        self,
        base_config_path: Union[str, Path],
        dataset_config_path: Union[str, Path],
        data_dir: Union[str, Path],
        output_dir: Union[str, Path],
        max_epochs: int = 50,
        early_stopping_patience: int = 10,
        validation_split: float = 0.2,
        target_metrics: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None,
        pruning_enabled: bool = True,
        device: str = "auto"
    ):
        """
        Initialize the segmentation objective function.

        Args:
            base_config_path: Path to base training configuration
            dataset_config_path: Path to dataset configuration
            data_dir: Directory containing training data
            output_dir: Directory for saving optimization results
            max_epochs: Maximum training epochs per trial
            early_stopping_patience: Early stopping patience
            validation_split: Fraction of data for validation
            target_metrics: Target metric values for optimization
            weights: Weights for multi-objective optimization
            pruning_enabled: Enable Optuna pruning
            device: Device for training ('auto', 'cpu', 'cuda')
        """
        self.base_config_path = Path(base_config_path)
        self.dataset_config_path = Path(dataset_config_path)
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.max_epochs = max_epochs
        self.early_stopping_patience = early_stopping_patience
        self.validation_split = validation_split
        self.pruning_enabled = pruning_enabled

        # Set up device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Default target metrics
        self.target_metrics = target_metrics or {
            "dice_score": 0.85,
            "hausdorff_distance": 10.0,
            "training_time": 3600  # 1 hour max
        }

        # Default weights for multi-objective optimization
        self.weights = weights or {
            "performance": 0.7,  # Segmentation performance
            "efficiency": 0.2,   # Training efficiency
            "complexity": 0.1    # Model complexity
        }

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Load base configurations
        self._load_base_configs()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_base_configs(self) -> None:
        """Load base configuration files."""
        with open(self.base_config_path, 'r') as f:
            self.base_config = json.load(f)

        with open(self.dataset_config_path, 'r') as f:
            self.dataset_config = json.load(f)

    def __call__(self, trial: optuna.Trial) -> float:
        """
        Objective function for Optuna optimization.

        Args:
            trial: Optuna trial object

        Returns:
            Objective value (higher is better)
        """
        try:
            # Get suggested hyperparameters
            model_arch = trial.suggest_categorical(
                "model_arch", ["unetr", "swinunetr", "segresnet", "unet"]
            )

            # Get model-specific hyperparameters
            search_space_func = HyperparameterSearchSpace.get_search_space_for_model(model_arch)
            params = search_space_func(trial)

            # Create trial configuration
            trial_config = self._create_trial_config(params, trial.number)

            # Train model with suggested parameters
            results = self._train_trial(trial_config, trial)

            # Calculate objective value
            objective_value = self._calculate_objective(results, trial)

            # Log trial results
            self._log_trial_results(trial, params, results, objective_value)

            return objective_value

        except Exception as e:
            self.logger.error(f"Trial {trial.number} failed: {e}")
            # Return a poor score to indicate failure
            return 0.0

    def _create_trial_config(self, params: Dict[str, Any], trial_number: int) -> Dict[str, Any]:
        """
        Create a configuration for the current trial.

        Args:
            params: Suggested hyperparameters
            trial_number: Trial number

        Returns:
            Complete configuration for training
        """
        # Start with base configuration
        config = self.base_config.copy()

        # Update with suggested parameters
        for key, value in params.items():
            if key.startswith("model_"):
                param_name = key[6:]  # Remove "model_" prefix
                if "model" not in config:
                    config["model"] = {}
                config["model"][param_name] = value
            elif key.startswith("train_"):
                param_name = key[6:]  # Remove "train_" prefix
                if "training" not in config:
                    config["training"] = {}
                config["training"][param_name] = value
            elif key.startswith("data_"):
                param_name = key[5:]  # Remove "data_" prefix
                if "data" not in config:
                    config["data"] = {}
                config["data"][param_name] = value
            elif key.startswith("loss_"):
                param_name = key[5:]  # Remove "loss_" prefix
                if "loss" not in config:
                    config["loss"] = {}
                config["loss"][param_name] = value
            elif key.startswith("aug_"):
                param_name = key[4:]  # Remove "aug_" prefix
                if "augmentation" not in config:
                    config["augmentation"] = {}
                config["augmentation"][param_name] = value

        # Set trial-specific settings
        config["training"]["max_epochs"] = self.max_epochs
        config["training"]["early_stopping_patience"] = self.early_stopping_patience
        config["training"]["device"] = self.device

        # Set output directory for this trial
        trial_output_dir = self.output_dir / f"trial_{trial_number:04d}"
        config["training"]["output_dir"] = str(trial_output_dir)

        return config

    def _train_trial(self, config: Dict[str, Any], trial: optuna.Trial) -> Dict[str, Any]:
        """
        Train a model for the current trial.

        Args:
            config: Training configuration
            trial: Optuna trial object

        Returns:
            Training results dictionary
        """
        start_time = time.time()

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            temp_config_path = f.name

        try:
            # Run training
            results = train_model_with_config(
                config_path=temp_config_path,
                dataset_config_path=str(self.dataset_config_path),
                trial=trial if self.pruning_enabled else None
            )

            training_time = time.time() - start_time
            results["training_time"] = training_time

            return results

        finally:
            # Clean up temporary file
            Path(temp_config_path).unlink()

    def _calculate_objective(self, results: Dict[str, Any], trial: optuna.Trial) -> float:
        """
        Calculate the objective value from training results.

        Args:
            results: Training results
            trial: Optuna trial object

        Returns:
            Objective value (higher is better)
        """
        # Performance component (Dice score is primary metric)
        dice_score = results.get("best_dice_score", 0.0)
        performance_score = dice_score / self.target_metrics["dice_score"]

        # Efficiency component (training time and convergence)
        training_time = results.get("training_time", float('inf'))
        time_efficiency = min(1.0, self.target_metrics["training_time"] / training_time)

        # Convergence efficiency (fewer epochs to converge is better)
        best_epoch = results.get("best_epoch", self.max_epochs)
        convergence_efficiency = 1.0 - (best_epoch / self.max_epochs)

        efficiency_score = 0.7 * time_efficiency + 0.3 * convergence_efficiency

        # Complexity component (parameter count and memory usage)
        param_count = results.get("parameter_count", 1e6)
        complexity_score = min(1.0, 1e6 / param_count)  # Prefer smaller models

        # Combine components with weights
        objective_value = (
            self.weights["performance"] * performance_score +
            self.weights["efficiency"] * efficiency_score +
            self.weights["complexity"] * complexity_score
        )

        # Penalty for failed trials or very poor performance
        if dice_score < 0.3:  # Very poor segmentation
            objective_value *= 0.1

        # Store individual components for analysis
        trial.set_user_attr("dice_score", dice_score)
        trial.set_user_attr("training_time", training_time)
        trial.set_user_attr("best_epoch", best_epoch)
        trial.set_user_attr("parameter_count", param_count)
        trial.set_user_attr("performance_score", performance_score)
        trial.set_user_attr("efficiency_score", efficiency_score)
        trial.set_user_attr("complexity_score", complexity_score)

        return objective_value

    def _log_trial_results(
        self,
        trial: optuna.Trial,
        params: Dict[str, Any],
        results: Dict[str, Any],
        objective_value: float
    ) -> None:
        """Log the results of a trial."""
        self.logger.info(f"Trial {trial.number} completed:")
        self.logger.info(f"  Objective value: {objective_value:.4f}")
        self.logger.info(f"  Dice score: {results.get('best_dice_score', 0.0):.4f}")
        self.logger.info(f"  Training time: {results.get('training_time', 0.0):.1f}s")
        self.logger.info(f"  Best epoch: {results.get('best_epoch', 0)}")
        self.logger.info(f"  Model arch: {params.get('model_arch', 'unknown')}")


class MultiObjectiveSegmentationObjective(SegmentationObjective):
    """
    Multi-objective version of the segmentation objective function.

    Returns multiple objectives that can be optimized simultaneously:
    1. Dice score (maximize)
    2. Training efficiency (maximize)
    3. Model complexity (minimize)
    """

    def __call__(self, trial: optuna.Trial) -> Tuple[float, float, float]:
        """
        Multi-objective function for Optuna optimization.

        Args:
            trial: Optuna trial object

        Returns:
            Tuple of (dice_score, efficiency, -complexity)
        """
        try:
            # Get suggested hyperparameters
            model_arch = trial.suggest_categorical(
                "model_arch", ["unetr", "swinunetr", "segresnet", "unet"]
            )

            # Get model-specific hyperparameters
            search_space_func = HyperparameterSearchSpace.get_search_space_for_model(model_arch)
            params = search_space_func(trial)

            # Create trial configuration
            trial_config = self._create_trial_config(params, trial.number)

            # Train model with suggested parameters
            results = self._train_trial(trial_config, trial)

            # Calculate individual objectives
            dice_score = results.get("best_dice_score", 0.0)

            # Efficiency: combine time and convergence
            training_time = results.get("training_time", float('inf'))
            time_efficiency = min(1.0, self.target_metrics["training_time"] / training_time)
            best_epoch = results.get("best_epoch", self.max_epochs)
            convergence_efficiency = 1.0 - (best_epoch / self.max_epochs)
            efficiency = 0.7 * time_efficiency + 0.3 * convergence_efficiency

            # Complexity: parameter count (negative for minimization)
            param_count = results.get("parameter_count", 1e6)
            complexity = -param_count / 1e6  # Negative for minimization

            # Log trial results
            self._log_trial_results(trial, params, results, dice_score)

            return dice_score, efficiency, complexity

        except Exception as e:
            self.logger.error(f"Trial {trial.number} failed: {e}")
            return 0.0, 0.0, -1.0  # Poor scores for all objectives


class FastObjective(SegmentationObjective):
    """
    Fast objective function for quick hyperparameter exploration.

    Uses reduced training epochs and smaller datasets for rapid iteration.
    Useful for initial exploration before running full optimization.
    """

    def __init__(self, *args, **kwargs):
        # Override some parameters for speed
        kwargs["max_epochs"] = kwargs.get("max_epochs", 10)
        kwargs["early_stopping_patience"] = kwargs.get("early_stopping_patience", 3)
        super().__init__(*args, **kwargs)

    def _create_trial_config(self, params: Dict[str, Any], trial_number: int) -> Dict[str, Any]:
        """Create a fast trial configuration."""
        config = super()._create_trial_config(params, trial_number)

        # Reduce batch size for speed if needed
        if "training" in config and "batch_size" in config["training"]:
            config["training"]["batch_size"] = min(
                config["training"]["batch_size"], 4
            )

        # Enable AMP for speed
        if "training" not in config:
            config["training"] = {}
        config["training"]["amp"] = True

        return config


def create_objective_from_config(config_path: Union[str, Path]) -> SegmentationObjective:
    """
    Create an objective function from a configuration file.

    Args:
        config_path: Path to the objective configuration file

    Returns:
        Configured objective function
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    objective_config = config.get("objective", {})

    return SegmentationObjective(
        base_config_path=objective_config["base_config_path"],
        dataset_config_path=objective_config["dataset_config_path"],
        data_dir=objective_config["data_dir"],
        output_dir=objective_config["output_dir"],
        max_epochs=objective_config.get("max_epochs", 50),
        early_stopping_patience=objective_config.get("early_stopping_patience", 10),
        validation_split=objective_config.get("validation_split", 0.2),
        target_metrics=objective_config.get("target_metrics"),
        weights=objective_config.get("weights"),
        pruning_enabled=objective_config.get("pruning_enabled", True),
        device=objective_config.get("device", "auto")
    )
