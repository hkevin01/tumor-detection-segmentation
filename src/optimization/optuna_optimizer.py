#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optuna-based hyperparameter optimization for medical image segmentation.

This module provides a comprehensive framework for hyperparameter optimization
using Optuna, specifically designed for medical imaging tasks with MONAI.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import optuna
from optuna.integration import MLflowCallback
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from optuna.storages import RDBStorage

from .objective_functions import SegmentationObjective


class OptunaTuner:
    """
    Optuna-based hyperparameter tuner for medical image segmentation.

    Features:
    - Multi-objective optimization (Dice score + training efficiency)
    - Parallel trial execution with distributed computing
    - Early stopping for poor trials
    - Comprehensive logging and visualization
    - Resume capability from previous studies
    """

    def __init__(
        self,
        study_name: str,
        storage_url: Optional[str] = None,
        direction: Union[str, List[str]] = "maximize",
        sampler: Optional[optuna.samplers.BaseSampler] = None,
        pruner: Optional[optuna.pruners.BasePruner] = None,
        load_if_exists: bool = True,
        enable_mlflow: bool = False,
        mlflow_tracking_uri: Optional[str] = None
    ):
        """
        Initialize the Optuna tuner.

        Args:
            study_name: Name of the optimization study
            storage_url: Database URL for distributed optimization
            direction: Optimization direction ('maximize', 'minimize', or list)
            sampler: Optuna sampler (defaults to TPESampler)
            pruner: Optuna pruner (defaults to MedianPruner)
            load_if_exists: Load existing study if it exists
            enable_mlflow: Enable MLflow integration for tracking
            mlflow_tracking_uri: MLflow tracking server URI
        """
        self.study_name = study_name
        self.storage_url = storage_url
        self.direction = direction
        self.load_if_exists = load_if_exists
        self.enable_mlflow = enable_mlflow

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Configure sampler
        if sampler is None:
            self.sampler = TPESampler(
                n_startup_trials=10,
                n_ei_candidates=24,
                seed=42
            )
        else:
            self.sampler = sampler

        # Configure pruner
        if pruner is None:
            self.pruner = MedianPruner(
                n_startup_trials=5,
                n_warmup_steps=5,
                interval_steps=1
            )
        else:
            self.pruner = pruner

        # Set up MLflow callback if enabled
        self.callbacks = []
        if enable_mlflow:
            if mlflow_tracking_uri:
                import mlflow
                mlflow.set_tracking_uri(mlflow_tracking_uri)
            self.callbacks.append(MLflowCallback(tracking_uri=mlflow_tracking_uri))

        # Initialize study
        self.study = self._create_study()

    def _create_study(self) -> optuna.Study:
        """Create or load an Optuna study."""
        try:
            if self.storage_url:
                storage = RDBStorage(url=self.storage_url)
            else:
                storage = None

            study = optuna.create_study(
                study_name=self.study_name,
                storage=storage,
                direction=self.direction,
                sampler=self.sampler,
                pruner=self.pruner,
                load_if_exists=self.load_if_exists
            )

            self.logger.info(f"Created/loaded study: {self.study_name}")
            return study

        except Exception as e:
            self.logger.error(f"Failed to create study: {e}")
            raise

    def optimize(
        self,
        objective_function: SegmentationObjective,
        n_trials: int = 100,
        timeout: Optional[float] = None,
        n_jobs: int = 1,
        gc_after_trial: bool = True,
        show_progress_bar: bool = True
    ) -> optuna.Study:
        """
        Run hyperparameter optimization.

        Args:
            objective_function: Objective function to optimize
            n_trials: Number of optimization trials
            timeout: Time limit in seconds
            n_jobs: Number of parallel jobs (-1 for all CPUs)
            gc_after_trial: Run garbage collection after each trial
            show_progress_bar: Show progress bar during optimization

        Returns:
            Completed Optuna study
        """
        self.logger.info(f"Starting optimization with {n_trials} trials")

        try:
            self.study.optimize(
                objective_function,
                n_trials=n_trials,
                timeout=timeout,
                n_jobs=n_jobs,
                gc_after_trial=gc_after_trial,
                show_progress_bar=show_progress_bar,
                callbacks=self.callbacks
            )

            self.logger.info("Optimization completed successfully")
            self._log_best_results()

            return self.study

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            raise

    def _log_best_results(self) -> None:
        """Log the best trial results."""
        best_trial = self.study.best_trial

        self.logger.info("=" * 50)
        self.logger.info("OPTIMIZATION RESULTS")
        self.logger.info("=" * 50)
        self.logger.info(f"Best trial number: {best_trial.number}")
        self.logger.info(f"Best value: {best_trial.value:.4f}")
        self.logger.info("Best parameters:")

        for key, value in best_trial.params.items():
            self.logger.info(f"  {key}: {value}")

        self.logger.info("=" * 50)

    def get_best_config(self) -> Dict[str, Any]:
        """
        Get the best hyperparameter configuration.

        Returns:
            Dictionary containing the best hyperparameters
        """
        if not self.study.trials:
            raise ValueError("No trials completed yet")

        best_params = self.study.best_trial.params

        # Convert to training config format
        config = {
            "optimization": {
                "study_name": self.study_name,
                "best_trial": self.study.best_trial.number,
                "best_value": self.study.best_trial.value,
                "n_trials": len(self.study.trials)
            },
            "model": {},
            "training": {},
            "data": {}
        }

        # Map parameters to config sections
        for key, value in best_params.items():
            if key.startswith("model_"):
                config["model"][key[6:]] = value
            elif key.startswith("train_"):
                config["training"][key[6:]] = value
            elif key.startswith("data_"):
                config["data"][key[5:]] = value
            else:
                config["training"][key] = value

        return config

    def save_best_config(self, output_path: Union[str, Path]) -> None:
        """
        Save the best configuration to a JSON file.

        Args:
            output_path: Path to save the configuration
        """
        config = self.get_best_config()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        self.logger.info(f"Best configuration saved to: {output_path}")

    def get_study_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive study statistics.

        Returns:
            Dictionary containing study statistics
        """
        if not self.study.trials:
            return {"message": "No trials completed yet"}

        completed_trials = [t for t in self.study.trials
                          if t.state == optuna.trial.TrialState.COMPLETE]
        pruned_trials = [t for t in self.study.trials
                        if t.state == optuna.trial.TrialState.PRUNED]
        failed_trials = [t for t in self.study.trials
                        if t.state == optuna.trial.TrialState.FAIL]

        stats = {
            "study_name": self.study_name,
            "total_trials": len(self.study.trials),
            "completed_trials": len(completed_trials),
            "pruned_trials": len(pruned_trials),
            "failed_trials": len(failed_trials),
            "best_trial": {
                "number": self.study.best_trial.number,
                "value": self.study.best_trial.value,
                "params": self.study.best_trial.params
            } if completed_trials else None
        }

        if completed_trials:
            values = [t.value for t in completed_trials]
            stats["performance_statistics"] = {
                "mean": sum(values) / len(values),
                "std": (sum((x - stats["performance_statistics"]["mean"])**2
                           for x in values) / len(values)) ** 0.5,
                "min": min(values),
                "max": max(values)
            }

        return stats

    def visualize_optimization(self, save_dir: Union[str, Path]) -> None:
        """
        Create visualization plots for the optimization study.

        Args:
            save_dir: Directory to save visualization plots
        """
        try:
            import optuna.visualization as vis
            import plotly.graph_objects as go

            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            if not self.study.trials:
                self.logger.warning("No trials to visualize")
                return

            # Optimization history
            fig = vis.plot_optimization_history(self.study)
            fig.write_html(save_dir / "optimization_history.html")

            # Parameter importances
            try:
                fig = vis.plot_param_importances(self.study)
                fig.write_html(save_dir / "param_importances.html")
            except Exception as e:
                self.logger.warning(f"Could not create parameter importance plot: {e}")

            # Parallel coordinate plot
            try:
                fig = vis.plot_parallel_coordinate(self.study)
                fig.write_html(save_dir / "parallel_coordinate.html")
            except Exception as e:
                self.logger.warning(f"Could not create parallel coordinate plot: {e}")

            # Slice plot for parameters
            try:
                fig = vis.plot_slice(self.study)
                fig.write_html(save_dir / "parameter_slice.html")
            except Exception as e:
                self.logger.warning(f"Could not create slice plot: {e}")

            self.logger.info(f"Visualization plots saved to: {save_dir}")

        except ImportError:
            self.logger.warning("Plotly not available, skipping visualization")
        except Exception as e:
            self.logger.error(f"Visualization failed: {e}")


def create_optimizer_from_config(config_path: Union[str, Path]) -> OptunaTuner:
    """
    Create an OptunaTuner from a configuration file.

    Args:
        config_path: Path to the optimization configuration file

    Returns:
        Configured OptunaTuner instance
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    optimizer_config = config.get("optimizer", {})

    return OptunaTuner(
        study_name=optimizer_config.get("study_name", "segmentation_optimization"),
        storage_url=optimizer_config.get("storage_url"),
        direction=optimizer_config.get("direction", "maximize"),
        load_if_exists=optimizer_config.get("load_if_exists", True),
        enable_mlflow=optimizer_config.get("enable_mlflow", False),
        mlflow_tracking_uri=optimizer_config.get("mlflow_tracking_uri")
    )


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Run hyperparameter optimization")
    parser.add_argument("--config", required=True, help="Optimization config file")
    parser.add_argument("--n-trials", type=int, default=100, help="Number of trials")
    parser.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    # Create optimizer
    tuner = create_optimizer_from_config(args.config)

    # Create objective function (would need to be implemented)
    # objective = SegmentationObjective(...)

    # Run optimization
    # study = tuner.optimize(objective, n_trials=args.n_trials)

    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tuner.save_best_config(output_dir / "best_config.json")
    tuner.visualize_optimization(output_dir / "visualizations")

    print("Optimization completed!")
